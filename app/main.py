import os
import time
from threading import Thread, Lock
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from app.cloud_sender import CloudSender
from app.database_manager import DatabaseManager

# Configurações
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "sensor_data"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "db"), # Ajustado para o nome do serviço no Docker Compose
    "port": os.getenv("DB_PORT", "5432")
}
CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://sua-api-na-nuvem.com/api/readings")
# Intervalo do scheduler em segundos (5 minutos por padrão)
SEND_INTERVAL_SECONDS = int(os.getenv("SEND_INTERVAL_SECONDS", "300")) 

# Inicializa o FastAPI
app = FastAPI()

# Inicializa as classes de serviço
db_manager = DatabaseManager(DB_CONFIG)
db_manager.connect()
db_manager.create_table()

cloud_sender = CloudSender(CLOUD_API_URL)

# Sincronização de threads
db_lock = Lock()

# Definição dos modelos Pydantic
class SensorReading(BaseModel):
    sensor_name_or_id: str
    value: float
    unit_of_measurement: Optional[str]
    timestamp: Optional[datetime] = None

class DevicePayload(BaseModel):
    device_serial_number: str
    readings: List[SensorReading]

# Endpoint da API para receber dados dos dispositivos ESP8266/Arduino
@app.post("/readings")
async def receive_readings(payload: DevicePayload):
    """
    Recebe dados, armazena no banco local e tenta enviar imediatamente
    para a nuvem.
    """
    print(payload)
    with db_lock:
        # 1. Armazena os dados no banco de dados local imediatamente
        for reading in payload.readings:
            # Define o timestamp se não for fornecido
            if not reading.timestamp:
                reading.timestamp = datetime.now(timezone.utc)
            
            db_manager.insert_reading(
                payload.device_serial_number,
                reading.sensor_name_or_id,
                reading.value,
                reading.unit_of_measurement,
                reading.timestamp
            )
        
        # 2. Tenta enviar todos os dados não enviados, incluindo os recém-recebidos
        cloud_sender.retry_send(db_manager, payload.device_serial_number)
        
    return {"status": "success", "message": "Dados recebidos, armazenados e envio para a nuvem iniciado."}

# Lógica de envio e reenvio para a nuvem em background
def send_to_cloud_scheduler():
    """Tarefa em background para enviar dados para a nuvem periodicamente."""
    while True:
        with db_lock:
            # Tenta reenviar todos os dados pendentes de todos os dispositivos
            cloud_sender.retry_send(db_manager, None) # None para indicar todos os dispositivos
        time.sleep(SEND_INTERVAL_SECONDS)

# Inicia a thread em background
if __name__ == "__main__":
    import uvicorn
    # Inicia a thread do agendador
    sender_thread = Thread(target=send_to_cloud_scheduler, daemon=True)
    sender_thread.start()
    
    # Inicia o servidor FastAPI com uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)