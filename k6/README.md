# Testes de carga com K6 (IoT Gateway)

Este diretório contém os cenários de carga para o endpoint **`POST /actor-data`** do gateway FastAPI. Os testes são executados **no host** (máquina onde está o K6) contra a API exposta em **`http://localhost:8000`** quando se usa o Docker Compose da raiz do repositório.

---

## Pré-requisitos

| Ferramenta | Uso |
|------------|-----|
| **Docker** e **Docker Compose** | Subir PostgreSQL, API, mock da nuvem, Prometheus, etc. |
| **K6** | Executar os scripts `.js` |

Instalação do K6: [https://k6.io/docs/getting-started/installation/](https://k6.io/docs/getting-started/installation/)

Confirme a versão (útil para reprodutibilidade em artigos ou relatórios):

```bash
k6 version
```

---

## Subir o projeto (stack local)

Na **raiz do repositório** (`iot-gateway/`):

```bash
docker compose up -d --build
```

Serviços relevantes para os testes:

| Serviço | Porta no host | Função |
|---------|----------------|--------|
| **app** (FastAPI) | **8000** | Gateway — alvo dos testes K6 (`BASE_URL`) |
| **db** (PostgreSQL) | 5432 | Persistência das leituras |
| **cloud-mock** (httpbin) | **8888** → 80 interno | Simula a API na nuvem com resposta rápida e determinística |
| **Prometheus** | 9090 | Métricas (correlação com janelas de teste) |
| **Grafana** | 3000 | Visualização (adicione o Prometheus como data source) |
| **cAdvisor** | 8080 | Métricas de containers |
| **node_exporter** | (apenas rede Docker) | Métricas do host para o Prometheus |

Documentação interativa da API: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Por que existe o `cloud-mock`

O gateway, ao receber dados em `/actor-data`, tenta sincronizar com a nuvem **no mesmo ciclo da requisição** (`retry_send`). Para testes reproduzíveis e isolados da internet, o Compose define por padrão:

```text
CLOUD_API_URL=http://cloud-mock/anything
```

O código da aplicação normaliza essa URL para um endpoint que o httpbin aceita em POST (por exemplo `.../anything/actor-data`). Assim, o tempo medido pelo K6 reflete ingestão + banco + chamada HTTP local à “nuvem”, sem dependência de rede externa.

Se precisar apontar para outra URL, use variável de ambiente ao subir o Compose ou um ficheiro `.env` na raiz do projeto (conforme [README principal](../README.md)).

---

## Executar os testes K6

Todos os comandos abaixo assumem que o diretório atual é a **raiz do repositório**, para que os imports `./lib/...` dos scripts funcionem.

### Smoke (validação rápida)

```bash
k6 run k6/smoke.js
```

Exportar resumo JSON (pasta `k6/results/` é ignorada pelo Git):

```bash
mkdir -p k6/results
k6 run k6/smoke.js --summary-export=k6/results/smoke_summary.json
```

### Carga progressiva (ramping VUs)

```bash
k6 run k6/load.js
```

### Taxa fixa de chegada (req/s)

```bash
k6 run k6/load-rps.js
```

### Stress

```bash
k6 run k6/stress.js
```

---

## Variáveis de ambiente dos scripts

Defina-as ao executar, por exemplo: `BASE_URL=http://127.0.0.1:8000 k6 run k6/load.js`.

| Variável | Scripts | Predefinição | Descrição |
|----------|---------|--------------|-----------|
| `BASE_URL` | todos | `http://localhost:8000` | URL base do gateway (sem barra final). |
| `PLATEAU_VUS` | `load.js` | `50` | Número de VUs no platô. |
| `LOAD_DURATION` | `load.js` | `120s` | Duração do platô (ex.: `90s`, `2m`). |
| `TARGET_RPS` | `load-rps.js` | `20` | Requisições por segundo desejadas. |
| `LOAD_RPS_DURATION` | `load-rps.js` | `120s` | Duração do cenário de taxa constante. |
| `PRE_ALLOCATED_VUS` | `load-rps.js` | `100` | VUs pré-alocados para absorver a taxa. |
| `STRESS_MAX_VUS` | `stress.js` | `200` | VUs máximos no platô de stress. |

---

## Bateria completa: `run-all.sh`

Executa em sequência: smoke → várias repetições de `load.js` → várias de `load-rps.js` → várias de `stress.js`, gravando um JSON de sumário por execução em `k6/results/`.

```bash
chmod +x k6/run-all.sh
./k6/run-all.sh
```

Variáveis opcionais do script:

| Variável | Predefinição | Significado |
|----------|--------------|-------------|
| `REPS_LOAD` | `5` | Repetições de `load.js` |
| `REPS_LOAD_RPS` | `5` | Repetições de `load-rps.js` |
| `REPS_STRESS` | `3` | Repetições de `stress.js` |
| `BASE_URL` | `http://localhost:8000` | Repassada aos cenários K6 |

Exemplo:

```bash
REPS_LOAD=3 TARGET_RPS=50 ./k6/run-all.sh
```

No final, o script imprime a data (UTC) e a saída de `k6 version` para rastreabilidade.

---

## Prometheus e Grafana

- **Prometheus UI**: [http://localhost:9090](http://localhost:9090)  
- Configuração de scrape: [`config/prometheus.yaml`](../config/prometheus.yaml) (node_exporter, cAdvisor, etc.).

No **Grafana** ([http://localhost:3000](http://localhost:3000)), adicione um data source **Prometheus**:

- URL **a partir do container Grafana**: `http://prometheus:9090`  
- Se aceder ao Grafana só pelo browser no host, essa URL costuma funcionar porque o Grafana e o Prometheus estão na mesma rede Docker.

Use os dashboards ou **Explore** para alinhar no tempo as métricas do host/container com as janelas em que correu o K6.

---

## Estrutura desta pasta

```text
k6/
├── README.md          # este ficheiro
├── lib/
│   └── payloads.js    # geração de JSON compatível com `ActorDataPayload`
├── smoke.js
├── load.js
├── load-rps.js
├── stress.js
├── run-all.sh
└── results/           # gerada pelos testes — ignorada pelo Git (ver .gitignore na raiz)
```

---

## Resolução de problemas

| Sintoma | O que verificar |
|---------|-----------------|
| `connection refused` em `localhost:8000` | `docker compose ps` — o serviço `app` deve estar `running`. Volte a subir: `docker compose up -d`. |
| Falhas HTTP 5xx ou timeouts sob carga | CPU/RAM do host, Postgres lento, ou thresholds do K6 demasiado apertados para o seu hardware. |
| Thresholds do K6 vermelhos em **smoke** com API parada | Esperado: o smoke falha se o gateway não estiver a ouvir na `BASE_URL`. |
| Import `./lib/payloads.js` falha | Execute `k6 run` a partir da **raiz do repo** com caminho `k6/nome.js`, não dentro de `k6/` com `k6 run smoke.js` sem ajustar caminhos. |

---

## Execução sem Docker (opcional)

Pode correr a API com Python e PostgreSQL locais conforme o [README principal](../README.md). Nesse caso, use `DB_HOST=localhost` e assegure que `CLOUD_API_URL` aponta para um endpoint que responda ao POST (por exemplo um httpbin local na porta 8888). Os comandos K6 mantêm-se os mesmos, desde que `BASE_URL` corresponda ao Uvicorn (por defeito porta **8000**).
