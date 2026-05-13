/**
 * Smoke test — valida que o gateway responde em carga mínima.
 *
 * Pré-requisitos:
 *   - API em BASE_URL (default http://localhost:8000)
 *   - Gateway com CLOUD_API_URL configurada (ex.: .env na raiz do repo) se usar Docker
 *
 * Execução:
 *   k6 run k6/smoke.js
 *   k6 run k6/smoke.js --summary-export=k6/results/smoke_summary.json
 *
 * Env:
 *   BASE_URL — URL base do gateway (sem barra final)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { buildActorDataPayload } from './lib/payloads.js';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
  },
};

export default function () {
  const url = `${baseUrl.replace(/\/$/, '')}/actor-data`;
  const payload = buildActorDataPayload(__VU, __ITER);

  const res = http.post(url, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'actor-data-smoke' },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'body status success': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'success';
      } catch {
        return false;
      }
    },
  });

  sleep(0.05);
}
