# IoT-Gateway

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## 📖 Visão Geral

O **IoT-Gateway** é um sistema completo e resiliente projetado para atuar como um orquestrador de dados em um ambiente de Internet das Coisas (IoT). Sua principal função é receber dados de diversos dispositivos de sensores (como ESP8266 e Arduino) por meio de uma API, armazená-los localmente em um banco de dados **PostgreSQL** e, em seguida, sincronizá-los com uma API na nuvem.

Este projeto é ideal para cenários onde a conexão com a internet pode ser instável ou intermitente, pois ele garante que nenhum dado seja perdido.

### ✨ Funcionalidades Principais

* **API de Entrada**: Uma API **FastAPI** para receber dados de múltiplos dispositivos.
* **Persistência Local**: Armazenamento seguro dos dados em um banco de dados **PostgreSQL** na própria Raspberry Pi.
* **Estratégia de Sincronização Híbrida**:
    * **Envio Imediato**: Tenta enviar os dados para a nuvem assim que são recebidos.
    * **Reenvio Agendado**: Um agendador em segundo plano verifica e reenvia periodicamente todos os dados que falharam no envio.
* **Implantação Simplificada**: Infraestrutura pronta para Docker e uma CLI (Command Line Interface) para configuração e execução.

## 🚀 Como Usar

### Pré-requisitos

#### Para Execução Local (sem Docker):
- **Python 3.10+**
- **PostgreSQL 12+** instalado e rodando
- **pip** (gerenciador de pacotes Python)

#### Para Execução com Docker:
- **Docker** e **Docker Compose** instalados

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/IoT-Gateway.git
cd iot-gateway
```

---

## 💻 Execução Local (Sem Docker)

### Passo 1: Instalar Dependências Python

```bash
# Criar um ambiente virtual (recomendado)
python3 -m venv venv

# Ativar o ambiente virtual
# No Linux/Mac:
source venv/bin/activate
# No Windows:
# venv\Scripts\activate

# Instalar as dependências
pip install -r requirements.txt
```

### Passo 2: Configurar o Banco de Dados PostgreSQL

Certifique-se de que o PostgreSQL está rodando e crie um banco de dados:

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar o banco de dados
CREATE DATABASE sensor_data;

# Criar um usuário (opcional, você pode usar o usuário padrão 'postgres')
CREATE USER seu_usuario WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE sensor_data TO seu_usuario;

# Sair do psql
\q
```

### Passo 3: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto ou exporte as variáveis de ambiente:

```bash
# Criar arquivo .env
cat > .env << EOF
DB_NAME=sensor_data
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
CLOUD_API_URL=http://sua-api-na-nuvem.com/api
SEND_INTERVAL_SECONDS=300
EOF
```

Ou exporte as variáveis diretamente no terminal:

```bash
export DB_NAME=sensor_data
export DB_USER=postgres
export DB_PASSWORD=sua_senha
export DB_HOST=localhost
export DB_PORT=5432
export CLOUD_API_URL=http://sua-api-na-nuvem.com/api
export SEND_INTERVAL_SECONDS=300
```

### Passo 4: Executar a Aplicação

```bash
# Certifique-se de estar no diretório do projeto e com o ambiente virtual ativado
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

A API estará disponível em: `http://localhost:8000`

### Passo 5: Verificar se está Funcionando

Acesse a documentação interativa da API:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🐳 Execução com Docker

### Opção 1: Usando o Script de Setup (Recomendado)

```bash
# Dar permissão de execução ao script
chmod +x setup.sh

# Executar o script de configuração
./setup.sh
```

O script irá:
- Verificar se o Docker e Docker Compose estão instalados
- Solicitar as configurações (banco de dados, URL da API na nuvem, etc.)
- Gerar o arquivo `.env` automaticamente
- Iniciar todos os serviços com Docker Compose

### Opção 2: Configuração Manual

1. **Criar arquivo `.env`**:

```bash
cat > .env << EOF
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=sensor_data
DB_HOST=db
DB_PORT=5432
CLOUD_API_URL=http://sua-api-na-nuvem.com/api
SEND_INTERVAL_SECONDS=300
EOF
```

2. **Iniciar os serviços**:

```bash
docker-compose up -d
```

3. **Verificar os logs**:

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs apenas da aplicação
docker-compose logs -f app
```

### Acessar os Serviços

Uma vez que os contêineres estiverem rodando:

- **API do Gateway**: `http://localhost:8000`
- **Documentação da API (Swagger)**: `http://localhost:8000/docs`
- **Grafana**: `http://localhost:3000`
- **Loki**: `http://localhost:3100`

### Parar os Serviços

```bash
# Parar os contêineres
docker-compose down

# Parar e remover volumes (apaga os dados do banco)
docker-compose down -v
```

---

## 📡 Enviando Dados para a API

### Formato de Requisição

A API espera receber dados no seguinte formato:

**Endpoint**: `POST http://localhost:8000/readings`

**Content-Type**: `application/json`

**Body**:
```json
{
  "device_serial_number": "ESP8266-001",
  "readings": [
    {
      "sensor_name_or_id": "temperature",
      "value": 26.5,
      "unit_of_measurement": "°C",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "sensor_name_or_id": "humidity",
      "value": 55.2,
      "unit_of_measurement": "%",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Nota**: O campo `timestamp` é opcional. Se não for fornecido, será usado o timestamp atual.

### Exemplo com cURL

```bash
curl -X POST "http://localhost:8000/readings" \
  -H "Content-Type: application/json" \
  -d '{
    "device_serial_number": "ESP8266-001",
    "readings": [
      {
        "sensor_name_or_id": "temperature",
        "value": 26.5,
        "unit_of_measurement": "°C"
      },
      {
        "sensor_name_or_id": "humidity",
        "value": 55.2,
        "unit_of_measurement": "%"
      }
    ]
  }'
```

### Exemplo com Python

```python
import requests

url = "http://localhost:8000/readings"
payload = {
    "device_serial_number": "ESP8266-001",
    "readings": [
        {
            "sensor_name_or_id": "temperature",
            "value": 26.5,
            "unit_of_measurement": "°C"
        },
        {
            "sensor_name_or_id": "humidity",
            "value": 55.2,
            "unit_of_measurement": "%"
        }
    ]
}

response = requests.post(url, json=payload)
print(response.json())
```

---

## 🔄 Formato de Dados Enviados para a Cloud

O gateway transforma os dados internos para o formato esperado pela API na nuvem:

**Endpoint**: `POST {{CLOUD_API_URL}}/actor-data`

**Content-Type**: `application/json`

**Body**:
```json
{
  "serialNumber": "ESP8266-001",
  "readings": [
    {
      "actor_name": "temperature",
      "value": 26.5,
      "unit_of_measurement": "°C",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "actor_name": "humidity",
      "value": 55.2,
      "unit_of_measurement": "%",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Nota**: O campo `timestamp` é formatado em ISO 8601 (UTC) com o sufixo 'Z'.

## 🛠️ Estrutura do Projeto

```
.
├── .env                  # Variáveis de ambiente (não versionado)
├── Dockerfile            # Configuração da imagem Docker da API
├── docker-compose.yml    # Orquestração dos serviços
├── requirements.txt      # Dependências Python
├── setup.sh              # Script CLI para configuração e execução
├── destroy.sh            # Script para parar e remover containers
├── logs.sh               # Script para visualizar logs
│
├── config/
│   ├── config.yaml       # Configuração do Loki
│   └── prometheus.yaml   # Configuração do Prometheus (opcional)
│
└── app/
    ├── __init__.py
    ├── database_manager.py # Lógica de comunicação com o PostgreSQL
    ├── cloud_sender.py     # Lógica de envio e reenvio para a nuvem
    └── main.py             # A API FastAPI e a lógica principal do gateway
```

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com o Banco de Dados

**Sintoma**: `psycopg2.OperationalError: could not connect to server`

**Soluções**:
- Verifique se o PostgreSQL está rodando:
  ```bash
  # Linux/Mac
  sudo systemctl status postgresql
  # ou
  sudo service postgresql status
  
  # Docker
  docker-compose ps db
  ```
- Verifique as credenciais no arquivo `.env`
- Para execução local, certifique-se de que `DB_HOST=localhost`
- Para Docker, certifique-se de que `DB_HOST=db`

#### 2. Erro ao Instalar Dependências

**Sintoma**: `ERROR: Could not find a version that satisfies the requirement`

**Solução**:
```bash
# Atualize o pip
pip install --upgrade pip

# Tente instalar novamente
pip install -r requirements.txt
```

#### 3. Porta 8000 já está em uso

**Sintoma**: `Address already in use`

**Soluções**:
- Pare o processo que está usando a porta:
  ```bash
  # Linux/Mac
  lsof -ti:8000 | xargs kill -9
  
  # Ou use outra porta
  uvicorn app.main:app --host 0.0.0.0 --port 8001
  ```
- Atualize a porta no `docker-compose.yml` se estiver usando Docker

#### 4. Dados não estão sendo enviados para a Cloud

**Sintomas**: Dados são salvos no banco, mas não chegam na API da nuvem

**Soluções**:
- Verifique se a `CLOUD_API_URL` está correta no `.env`
- Verifique os logs da aplicação:
  ```bash
  # Docker
  docker-compose logs -f app
  
  # Local
  # Os logs aparecerão no terminal onde você executou o uvicorn
  ```
- Teste a conectividade com a API da nuvem:
  ```bash
  curl -X GET "${CLOUD_API_URL}/health"  # Se tiver endpoint de health
  ```

#### 5. Erro de Permissão no Script setup.sh

**Sintoma**: `Permission denied`

**Solução**:
```bash
chmod +x setup.sh
./setup.sh
```

### Verificar Status dos Serviços

#### Com Docker:
```bash
# Status de todos os containers
docker-compose ps

# Logs em tempo real
docker-compose logs -f

# Logs apenas da aplicação
docker-compose logs -f app
```

#### Localmente:
```bash
# Verificar se o PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar processos Python
ps aux | grep uvicorn
```

### Limpar e Reiniciar

#### Docker:
```bash
# Parar e remover containers e volumes
docker-compose down -v

# Reconstruir as imagens
docker-compose build --no-cache

# Iniciar novamente
docker-compose up -d
```

#### Local:
```bash
# Parar a aplicação (Ctrl+C no terminal)

# Se necessário, limpar o banco de dados
sudo -u postgres psql -c "DROP DATABASE sensor_data;"
sudo -u postgres psql -c "CREATE DATABASE sensor_data;"
```

---

## 📜 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](https://www.google.com/search?q=LICENSE) para detalhes.
