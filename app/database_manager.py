import psycopg2
from psycopg2 import sql

class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None

    def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("Conectado ao banco de dados PostgreSQL.")
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            self.conn = None

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            print("Conexão com o banco de dados fechada.")

    def create_table(self):
        """Cria a tabela de leituras se ela não existir."""
        if not self.conn:
            print("Não há conexão com o banco de dados.")
            return

        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    id SERIAL PRIMARY KEY,
                    device_serial_number VARCHAR(255) NOT NULL,
                    sensor_name_or_id VARCHAR(255) NOT NULL,
                    value NUMERIC NOT NULL,
                    unit_of_measurement VARCHAR(50),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    sent_to_cloud BOOLEAN DEFAULT FALSE
                );
            """)
            self.conn.commit()
            print("Tabela 'readings' verificada/criada.")

    def insert_reading(self, device_serial, sensor_name, value, unit, timestamp):
        """Insere uma nova leitura no banco de dados."""
        if not self.conn:
            return

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO readings (device_serial_number, sensor_name_or_id, value, unit_of_measurement, timestamp)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (device_serial, sensor_name, value, unit, timestamp)
            )
            self.conn.commit()
            print(f"Leitura de {sensor_name} do dispositivo {device_serial} inserida.")

    def get_unsent_readings(self):
        """Retorna todas as leituras que ainda não foram enviadas para a nuvem."""
        if not self.conn:
            return []

        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM readings WHERE sent_to_cloud = FALSE ORDER BY timestamp ASC;")
            readings = cur.fetchall()
            return readings

    def mark_readings_as_sent(self, ids):
        """Marca as leituras com os IDs especificados como enviadas."""
        if not self.conn or not ids:
            return

        with self.conn.cursor() as cur:
            # Converte a lista de IDs para uma tupla para usar em uma cláusula IN
            id_tuple = tuple(ids)
            # A cláusula IN precisa ser construída dinamicamente para ser segura
            query = sql.SQL("UPDATE readings SET sent_to_cloud = TRUE WHERE id IN ({});").format(
                sql.SQL(',').join(sql.Placeholder() * len(id_tuple))
            )
            cur.execute(query, id_tuple)
            self.conn.commit()
            print(f"{len(ids)} leituras marcadas como enviadas.")