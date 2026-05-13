/**
 * Carga progressiva (ramping-vus): ramp-up → platô → ramp-down.
 *
 * Execução:
 *   k6 run k6/load.js
 *   k6 run k6/load.js --summary-export=k6/results/load_summary.json
 *
 * Env:
 *   BASE_URL        — default http://localhost:8000
 *   PLATEAU_VUS     — VUs no platô (default 50); em placa fraca use 5–15
 *   LOAD_DURATION   — duração do platô (default 120s), ex.: 90s, 2m
 *   HTTP_TIMEOUT    — timeout por pedido no k6 (default 120s); o implícito era 60s
 *   PACING_MS       — pausa entre iterações em ms (default 50); placa fraca: 200–500
 *   RAMP_DURATION   — duração ramp-up e ramp-down (default 30s); fraco: 60s–2m
 *   WEAK_HARDWARE   — se 1/true, thresholds mais largos (só métricas, não evita timeout)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { buildActorDataPayload } from './lib/payloads.js';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const plateauVus = Number(__ENV.PLATEAU_VUS || '50');
const loadDuration = __ENV.LOAD_DURATION || '120s';
const httpTimeout = __ENV.HTTP_TIMEOUT || '120s';
const pacingMs = Number(__ENV.PACING_MS || '50');
const rampDuration = __ENV.RAMP_DURATION || '30s';
const weakHardware =
  __ENV.WEAK_HARDWARE === '1' ||
  __ENV.WEAK_HARDWARE === 'true' ||
  __ENV.WEAK_HARDWARE === 'yes';

const strictThresholds = {
  http_req_duration: ['p(95)<500', 'p(99)<1000'],
  http_req_failed: ['rate<0.01'],
  checks: ['rate>0.95'],
};

const relaxedThresholds = {
  http_req_duration: ['p(95)<8000', 'p(99)<20000'],
  http_req_failed: ['rate<0.05'],
  checks: ['rate>0.85'],
};

export const options = {
  stages: [
    { duration: rampDuration, target: plateauVus },
    { duration: loadDuration, target: plateauVus },
    { duration: rampDuration, target: 0 },
  ],
  thresholds: weakHardware ? relaxedThresholds : strictThresholds,
};

export default function () {
  const url = `${baseUrl}/actor-data`;
  const payload = buildActorDataPayload(__VU, __ITER);

  const res = http.post(url, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'actor-data-load' },
    timeout: httpTimeout,
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'body status success': (r) => {
      try {
        return JSON.parse(r.body).status === 'success';
      } catch {
        return false;
      }
    },
  });

  sleep(Math.max(0, pacingMs) / 1000);
}
