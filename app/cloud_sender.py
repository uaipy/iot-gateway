import requests
import json
import time

class CloudSender:
    def __init__(self, api_url):
        self.api_url = api_url

    def send_data(self, payload):
        """Tenta enviar os dados para a API da nuvem."""
        try:
            print(f"Tentando enviar {len(payload['readings'])} leituras para a nuvem...")
            headers = {"Content-Type": "application/json"}
            print(f"Payload: {json.dumps(payload, indent=2)}")
            response = requests.post(self.api_url, data=json.dumps(payload), headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()  # Lança um erro se o status não for 2xx
            print("Dados enviados com sucesso para a nuvem!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar dados para a nuvem: {e}")
            return False

    def retry_send(self, db_manager, device_serial):
        """
        Pega todos os dados não enviados do banco e tenta enviá-los.
        
        Args:
            db_manager (DatabaseManager): A instância do gerenciador de banco de dados.
            device_serial (str): O número de série do dispositivo a ser enviado.
        """
        unsent_readings = db_manager.get_unsent_readings()

        if not unsent_readings:
            print("Nenhum dado pendente para enviar.")
            return

        readings_by_device = {}
        for row in unsent_readings:
            reading_id, device_serial, sensor_name, value, unit, timestamp, _ = row
            if device_serial not in readings_by_device:
                readings_by_device[device_serial] = {
                    "device_serial_number": device_serial,
                    "readings": [],
                    "ids": []  # Apenas para controle interno
                }

            formatted_timestamp = timestamp.isoformat().replace('+00:00', 'Z')

            readings_by_device[device_serial]["readings"].append({
                "sensor_name_or_id": sensor_name,
                "value": float(value),
                "unit_of_measurement": unit,
                "timestamp": formatted_timestamp
            })

            readings_by_device[device_serial]["ids"].append(reading_id)

        for payload in readings_by_device.values():
            ids_to_mark = payload.pop("ids")  # Remove antes de enviar
            success = self.send_data(payload)
            if success:
                db_manager.mark_readings_as_sent(ids_to_mark)
