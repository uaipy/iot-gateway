/**
 * Carga progressiva (ramping-vus): ramp-up → platô → ramp-down.
 *
 * Execução:
 *   k6 run k6/load.js
 *   k6 run k6/load.js --summary-export=k6/results/load_summary.json
 *
 * Env:
 *   BASE_URL       — default http://localhost:8000
 *   PLATEAU_VUS    — VUs no platô (default 50)
 *   LOAD_DURATION  — duração do platô (default 120s), ex.: 90s, 2m
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { buildActorDataPayload } from './lib/payloads.js';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const plateauVus = Number(__ENV.PLATEAU_VUS || '50');
const loadDuration = __ENV.LOAD_DURATION || '120s';

export const options = {
  stages: [
    { duration: '30s', target: plateauVus },
    { duration: loadDuration, target: plateauVus },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.95'],
  },
};

export default function () {
  const url = `${baseUrl}/actor-data`;
  const payload = buildActorDataPayload(__VU, __ITER);

  const res = http.post(url, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'actor-data-load' },
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

  sleep(0.05);
}
