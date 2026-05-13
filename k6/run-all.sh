#!/usr/bin/env bash
# Executa a bateria de testes K6 com exportação versionada para k6/results/.
#
# Pré-requisitos:
#   - k6 instalado (https://k6.io/)
#   - Stack Docker: docker compose up -d (defina CLOUD_API_URL no .env ou no ambiente)
#
# Variáveis opcionais:
#   REPS_LOAD=5       — repetições de load.js
#   REPS_LOAD_RPS=5   — repetições de load-rps.js
#   REPS_STRESS=3     — repetições de stress.js
#   BASE_URL          — repassada aos scripts k6 (default http://localhost:8000)
#
# Uso:
#   chmod +x k6/run-all.sh && ./k6/run-all.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="${ROOT}/results"
mkdir -p "${RESULTS}"

TS="$(date -u +"%Y-%m-%dT%H-%M-%SZ")"
REPS_LOAD="${REPS_LOAD:-5}"
REPS_LOAD_RPS="${REPS_LOAD_RPS:-5}"
REPS_STRESS="${REPS_STRESS:-3}"

export BASE_URL="${BASE_URL:-http://localhost:8000}"

run_k6() {
  local label="$1"
  local script="$2"
  local out="${RESULTS}/${label}_${TS}.json"
  echo ""
  echo "=== ${label} -> ${out} ==="
  k6 run "${script}" --summary-export="${out}"
}

echo "BASE_URL=${BASE_URL}"
echo "Timestamp batch (UTC): ${TS}"

run_k6 "smoke" "${ROOT}/smoke.js"

i=1
while [[ "${i}" -le "${REPS_LOAD}" ]]; do
  run_k6 "load_${i}" "${ROOT}/load.js"
  i=$((i + 1))
done

i=1
while [[ "${i}" -le "${REPS_LOAD_RPS}" ]]; do
  run_k6 "load_rps_${i}" "${ROOT}/load-rps.js"
  i=$((i + 1))
done

i=1
while [[ "${i}" -le "${REPS_STRESS}" ]]; do
  run_k6 "stress_${i}" "${ROOT}/stress.js"
  i=$((i + 1))
done

echo ""
echo "=== Ambiente (para rastreabilidade em artigo) ==="
echo "date -u: $(date -u)"
(k6 version) || true
