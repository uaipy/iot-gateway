/**
 * Geração de payloads JSON compatíveis com ActorDataPayload / ActorReading (app/main.py).
 *
 * Variáveis úteis: nenhuma obrigatória aqui (vu/iter passados pelo chamador).
 */

/**
 * @param {number} vu - virtual user id (__VU)
 * @param {number} iter - iteration (__ITER)
 * @returns {string} JSON body para POST /actor-data
 */
export function buildActorDataPayload(vu, iter) {
  const serialNumber = `ESP8266-${vu}-${iter}`;
  const temperature = 20 + Math.random() * 15;
  const humidity = 40 + Math.random() * 40;
  const ts = new Date().toISOString();

  const payload = {
    serialNumber,
    readings: [
      {
        actor_name: 'temperature',
        value: Math.round(temperature * 100) / 100,
        unit_of_measurement: '°C',
        timestamp: ts,
      },
      {
        actor_name: 'humidity',
        value: Math.round(humidity * 100) / 100,
        unit_of_measurement: '%',
        timestamp: ts,
      },
    ],
  };

  return JSON.stringify(payload);
}
