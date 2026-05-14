#!/usr/bin/env python3
"""
Simulação de métricas agregadas (smoke, carga, stress) para vários alvos
embarcados (TX9 / TX6), todos com 4 núcleos: TX9 com 2 GiB RAM; TX6 com 1,9 / 1,7 / 1,6 GiB.
Cenário **hardware muito limitado**: poucos VUs, vazões baixas e latências de
smoke/carga mais altas; no stress, RAM a 100 %, erro 98 % e 30 s (colapso sob
carga moderada já suficiente para derrubar o alvo).

Valores sintéticos, reproduzíveis (semente por dispositivo). Substitua por
traces reais (k6, Locust, JMeter) quando houver medição de laboratório.

Dependências: pip install matplotlib numpy
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib import gridspec
except ImportError as e:
    print("Instale as dependências: pip install matplotlib numpy", file=sys.stderr)
    raise e

# RAM de referência = dispositivo com mais memória (TX9); TX6 com menos RAM aumentam rpf.
REFERENCE_RAM_GIB = 2.0

# Stress em saturação de RAM (valores fixos pedidos para o artigo / figura)
STRESS_RAM_USE_PCT = 1.0  # 100 % da RAM total do dispositivo
STRESS_ERROR_PCT = 98.0
STRESS_LATENCY_MS = 30_000.0  # 30 s

# Hardware muito fraco: oferta de carga reduzida (alinhamento típico com k6 em TV box)
VU_SMOKE = 4
VU_LOAD = 20
VU_STRESS = 36
REQ_S_SMOKE_BASE = 95.0
REQ_S_LOAD_BASE = 210.0
REQ_S_STRESS_BASE = 6.5  # quase tudo falha (98 %); poucos pedidos completos


@dataclass(frozen=True)
class DeviceProfile:
    """Perfil de hardware para uma linha experimental."""

    key: str
    label: str
    cpu_cores: int
    ram_gib: float

    @property
    def ram_mib(self) -> float:
        return self.ram_gib * 1024.0


# Ordem: TX9 (2 GiB) e TX6 com 1,9 / 1,7 / 1,6 GiB.
DEVICE_PROFILES: tuple[DeviceProfile, ...] = (
    DeviceProfile("tx9", "TX9 — 4 núcleos, 2,0 GiB RAM", 4, 2.0),
    DeviceProfile("tx6_19", "TX6 — 4 núcleos, 1,9 GiB RAM", 4, 1.9),
    DeviceProfile("tx6_17", "TX6 — 4 núcleos, 1,7 GiB RAM", 4, 1.7),
    DeviceProfile("tx6_16", "TX6 — 4 núcleos, 1,6 GiB RAM", 4, 1.6),
)


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    label_pt: str
    duration_min: float
    virtual_users: int
    req_per_s: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    error_pct: float
    cpu_mean_pct: float
    ram_used_mib: float


def _rng_for_profile(profile: DeviceProfile) -> np.random.Generator:
    """Semente estável por perfil (reprodutibilidade entre execuções)."""
    seed = 42 + sum(ord(c) for c in profile.key) * 17
    return np.random.default_rng(seed)


def _jitter(rng: np.random.Generator, base: float, rel: float = 0.03) -> float:
    return float(base * (1.0 + rng.uniform(-rel, rel)))


def _ram_pressure_factor(ram_gib: float) -> float:
    """1,0 na RAM de referência; sobe levemente quando há menos RAM total."""
    return max(0.0, (REFERENCE_RAM_GIB - ram_gib) / REFERENCE_RAM_GIB)


def build_simulated_results(profile: DeviceProfile) -> list[ScenarioResult]:
    """
    Três cenários por dispositivo: smoke, carga sustentada, stress.
    Pressupõe SoC/RAM limitados: poucos VUs e vazão modesta; smoke/carga com
    latências mais altas. No stress, RAM 100 %, erro 98 % e latências 30 s.
    """
    rng = _rng_for_profile(profile)
    rpf = _ram_pressure_factor(profile.ram_gib)
    cap_mib = profile.ram_mib * 0.97

    # Ajustes coerentes com menor RAM (mesma carga ofertada, pior fila / OOM próximo).
    load_throughput_scale = 1.0 - 0.06 * rpf
    stress_throughput_scale = 1.0 - 0.1 * rpf
    latency_scale = 1.0 + 0.08 * rpf
    # Latências base maiores (CPU lenta / I/O apertado) antes do colapso de 30 s.
    smoke_lat = (1.0 + 0.35 * rpf)
    load_lat = (1.0 + 0.28 * rpf)

    smoke_ram = min(cap_mib * 0.22, _jitter(rng, profile.ram_mib * 0.20, 0.04))
    load_ram = min(cap_mib * 0.48, _jitter(rng, profile.ram_mib * 0.46, 0.03))
    stress_ram = profile.ram_mib * STRESS_RAM_USE_PCT

    return [
        ScenarioResult(
            name="smoke",
            label_pt="Smoke (sanidade)",
            duration_min=_jitter(rng, 6, 0.05),
            virtual_users=VU_SMOKE,
            req_per_s=_jitter(rng, REQ_S_SMOKE_BASE * (1.0 - 0.04 * rpf)),
            p50_ms=_jitter(rng, 85 * latency_scale * smoke_lat),
            p95_ms=_jitter(rng, 195 * latency_scale * smoke_lat),
            p99_ms=_jitter(rng, 310 * latency_scale * smoke_lat),
            error_pct=max(0.0, _jitter(rng, 0.0, 0.5)),
            cpu_mean_pct=min(92.0, _jitter(rng, 38 + 4.0 * rpf)),
            ram_used_mib=smoke_ram,
        ),
        ScenarioResult(
            name="load",
            label_pt="Carga (nominal sustentada)",
            duration_min=_jitter(rng, 32, 0.02),
            virtual_users=VU_LOAD,
            req_per_s=_jitter(rng, REQ_S_LOAD_BASE * load_throughput_scale),
            p50_ms=_jitter(rng, 165 * latency_scale * load_lat),
            p95_ms=_jitter(rng, 420 * latency_scale * load_lat),
            p99_ms=_jitter(rng, 780 * latency_scale * load_lat),
            error_pct=max(0.0, _jitter(rng, 0.04 + 0.02 * rpf, 0.35)),
            cpu_mean_pct=min(99.0, _jitter(rng, 86 + 2.5 * rpf)),
            ram_used_mib=load_ram,
        ),
        ScenarioResult(
            name="stress",
            label_pt="Stress (saturação)",
            duration_min=_jitter(rng, 18, 0.03),
            virtual_users=VU_STRESS,
            req_per_s=_jitter(rng, REQ_S_STRESS_BASE * stress_throughput_scale, 0.04),
            p50_ms=STRESS_LATENCY_MS,
            p95_ms=STRESS_LATENCY_MS,
            p99_ms=STRESS_LATENCY_MS,
            error_pct=STRESS_ERROR_PCT,
            cpu_mean_pct=min(99.5, _jitter(rng, 97)),
            ram_used_mib=stress_ram,
        ),
    ]


def results_to_table_rows(
    profile: DeviceProfile,
    rows: list[ScenarioResult],
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for r in rows:
        out.append(
            {
                "Dispositivo": profile.label,
                "Cenário": r.label_pt,
                "d (min)": round(r.duration_min, 1),
                "VUs": r.virtual_users,
                "req/s": round(r.req_per_s, 0),
                "p50 (ms)": round(r.p50_ms, 0),
                "p95 (ms)": round(r.p95_ms, 0),
                "p99 (ms)": round(r.p99_ms, 0),
                "Erro (%)": round(r.error_pct, 3),
                "CPU méd. (%)": round(r.cpu_mean_pct, 1),
                "RAM (MiB)": round(r.ram_used_mib, 0),
            }
        )
    return out


def print_markdown_table(title: str, table_rows: list[dict[str, object]]) -> None:
    if not table_rows:
        return
    keys = list(table_rows[0].keys())
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    print(f"\n{title}\n")
    print(header)
    print(sep)
    for row in table_rows:
        print("| " + " | ".join(str(row[k]) for k in keys) + " |")


def _short_device_label(p: DeviceProfile) -> str:
    prefix = "TX9" if p.key == "tx9" else "TX6"
    return f"{prefix}\n{p.ram_gib:.1f} GiB".replace(".", ",")


def plot_comparison_figure(
    by_device: dict[str, tuple[DeviceProfile, list[ScenarioResult]]],
    out_path: Path,
) -> None:
    """Uma figura: comparação entre dispositivos por tipo de cenário."""
    profiles = [by_device[k][0] for k in [d.key for d in DEVICE_PROFILES]]
    scenario_keys = ("smoke", "load", "stress")
    scenario_labels = ("Smoke", "Carga", "Stress")
    n_dev = len(profiles)
    n_sc = len(scenario_keys)
    x = np.arange(n_sc)
    width = 0.18
    offsets = np.linspace(-(n_dev - 1) / 2, (n_dev - 1) / 2, n_dev) * width * 2.2
    colors = ("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728")

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 150,
        }
    )

    fig = plt.figure(figsize=(12.0, 8.2), constrained_layout=False)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.30)

    fig.suptitle(
        "Comparação dos dispositivos (4 núcleos) — smoke, carga e stress\n"
        "TX9 (2 GiB) vs TX6 (1,9 / 1,7 / 1,6 GiB)",
        fontsize=12,
        fontweight="bold",
    )

    def scenario_row(dev_key: str, sk: str) -> ScenarioResult:
        rows = by_device[dev_key][1]
        for r in rows:
            if r.name == sk:
                return r
        raise KeyError(sk)

    # (a) Throughput
    ax1 = fig.add_subplot(gs[0, 0])
    for i, p in enumerate(profiles):
        thr = [scenario_row(p.key, sk).req_per_s for sk in scenario_keys]
        pos = x + offsets[i]
        ax1.bar(
            pos,
            thr,
            width,
            label=_short_device_label(p).replace("\n", " "),
            color=colors[i],
            edgecolor="black",
            linewidth=0.35,
        )
    ax1.set_xticks(x, scenario_labels)
    ax1.set_ylabel("Vazão (req/s)")
    ax1.set_title("(a) Vazão média por cenário")
    ax1.legend(title="Dispositivo", loc="upper right", frameon=True, ncol=1)

    # (b) p95 latency
    ax2 = fig.add_subplot(gs[0, 1])
    for i, p in enumerate(profiles):
        lat = [scenario_row(p.key, sk).p95_ms for sk in scenario_keys]
        ax2.bar(x + offsets[i], lat, width, color=colors[i], edgecolor="k", linewidth=0.35)
    ax2.set_xticks(x, scenario_labels)
    ax2.set_yscale("log")
    ax2.set_ylabel("Latência p95 (ms, log)")
    ax2.set_title("(b) Latência p95 por cenário")
    ax2.grid(True, axis="y", which="major", alpha=0.25)

    # (c) Error rate
    ax3 = fig.add_subplot(gs[1, 0])
    for i, p in enumerate(profiles):
        err = [scenario_row(p.key, sk).error_pct for sk in scenario_keys]
        ax3.bar(x + offsets[i], err, width, color=colors[i], edgecolor="k", linewidth=0.35)
    ax3.set_xticks(x, scenario_labels)
    ax3.set_ylabel("Taxa de erro (%)")
    ax3.set_title("(c) Taxa de erro por cenário")
    ymax = max(
        5.0,
        min(102.0, max(scenario_row(p.key, sk).error_pct for p in profiles for sk in scenario_keys) * 1.08),
    )
    ax3.set_ylim(0, ymax)

    # (d) RAM % of device total (stress only: clearer device spread)
    ax4 = fig.add_subplot(gs[1, 1])
    dev_x = np.arange(n_dev)
    ram_pct = []
    for p in profiles:
        r = scenario_row(p.key, "stress")
        ram_pct.append(100.0 * r.ram_used_mib / p.ram_mib)
    bars = ax4.bar(dev_x, ram_pct, color=colors, edgecolor="k", linewidth=0.4)
    ax4.set_xticks(dev_x, [_short_device_label(p) for p in profiles])
    ax4.set_ylabel("RAM usada (% da capacidade)")
    ax4.set_title("(d) Utilização de RAM no stress (saturação)")
    ax4.set_ylim(0, 105)
    for b, v in zip(bars, ram_pct):
        ax4.text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + 1.5,
            f"{v:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    foot = (
        f"VUs (utilizadores virtuais): smoke = {VU_SMOKE}; carga = {VU_LOAD}; stress = {VU_STRESS} "
        f"(iguais para TX9 e TX6).\n"
    )
    fig.text(0.5, 0.015, foot, ha="center", fontsize=10.5, style="italic", color="#555555", linespacing=1.35)

    fig.subplots_adjust(bottom=0.14, top=0.88)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    by_device: dict[str, tuple[DeviceProfile, list[ScenarioResult]]] = {}
    all_table_rows: list[dict[str, object]] = []

    for i, profile in enumerate(DEVICE_PROFILES, start=1):
        rows = build_simulated_results(profile)
        by_device[profile.key] = (profile, rows)
        part = results_to_table_rows(profile, rows)
        all_table_rows.extend(part)
        print_markdown_table(f"**Tabela {i}.** {profile.label}", part)

    print_markdown_table(
        "**Tabela consolidada.** Todos os dispositivos e cenários",
        all_table_rows,
    )

    out = Path(__file__).resolve().parent / "article_load_test_simulation.png"
    plot_comparison_figure(by_device, out)
    print(f"\nFigura comparativa salva em: {out}")
    print(
        f"\n**Rodapé (VUs).** Utilizadores virtuais por cenário (iguais em todos os dispositivos): "
        f"smoke **{VU_SMOKE}**, carga **{VU_LOAD}**, stress **{VU_STRESS}**."
    )


if __name__ == "__main__":
    main()
