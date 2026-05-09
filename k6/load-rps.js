/**
 * Taxa de chegada constante (constant-arrival-rate) — adequado para relatório acadêmico:
 * mantém RPS alvo mesmo se a latência aumentar.
 *
 * Execução:
 *   k6 run k6/load-rps.js
 *   TARGET_RPS=50 k6 run k6/load-rps.js --summary-export=k6/results/load_rps_summary.json
 *
 * Env:
 *   BASE_URL           — default http://localhost:8000
 *   TARGET_RPS         — requisições por segundo (default 20)
 *   LOAD_RPS_DURATION  — duração do cenário (default 120s)
 *   PRE_ALLOCATED_VUS  — VUs pré-alocados (default 100)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { buildActorDataPayload } from './lib/payloads.js';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const targetRps = Number(__ENV.TARGET_RPS || '20');
const duration = __ENV.LOAD_RPS_DURATION || '120s';
const preAllocatedVUs = Number(__ENV.PRE_ALLOCATED_VUS || '100');
const maxVUs = Math.max(preAllocatedVUs * 2, 500);

export const options = {
  scenarios: {
    constant_rps: {
      executor: 'constant-arrival-rate',
      rate: targetRps,
      timeUnit: '1s',
      duration,
      preAllocatedVUs,
      maxVUs,
      exec: 'default',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<800', 'p(99)<2000'],
    http_req_failed: ['rate<0.05'],
    checks: ['rate>0.90'],
  },
};

export default function () {
  const url = `${baseUrl}/actor-data`;
  const payload = buildActorDataPayload(__VU, __ITER);

  const res = http.post(url, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'actor-data-load-rps' },
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

  sleep(0.01);
}
