/**
 * Stress — aumento agressivo de VUs para observar degradação / saturação.
 * Thresholds mais permissivos que load.js (falhas esperadas sob stress extremo).
 *
 * Execução:
 *   k6 run k6/stress.js
 *   STRESS_MAX_VUS=300 k6 run k6/stress.js --summary-export=k6/results/stress_summary.json
 *
 * Env:
 *   BASE_URL        — default http://localhost:8000
 *   STRESS_MAX_VUS  — VUs máximos no platô de stress (default 200)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { buildActorDataPayload } from './lib/payloads.js';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const maxVus = Number(__ENV.STRESS_MAX_VUS || '200');

export const options = {
  stages: [
    { duration: '1m', target: maxVus },
    { duration: '2m', target: maxVus },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(99)<5000'],
    http_req_failed: ['rate<0.20'],
    checks: ['rate>0.50'],
  },
};

export default function () {
  const url = `${baseUrl}/actor-data`;
  const payload = buildActorDataPayload(__VU, __ITER);

  const res = http.post(url, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'actor-data-stress' },
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

  sleep(0.02);
}
