W# IoT-Gateway

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

Para rodar este projeto, você precisará ter o **Docker** e o **Docker Compose** instalados na sua máquina (ex: Raspberry Pi com Linux).

### 1. Clonar o Repositório

```bash
git clone [https://github.com/seu-usuario/IoT-Gateway.git](https://github.com/seu-usuario/IoT-Gateway.git)
cd IoT-Gateway
````

### 2\. Configurar e Executar com a CLI

A maneira mais fácil de configurar e rodar o gateway é usando o script da CLI. Ele fará as seguintes etapas para você:

  * Verificar se o Docker e o Docker Compose estão instalados.
  * Perguntar pelas variáveis de ambiente (usuário/senha do banco de dados, URL da API na nuvem, etc.).
  * Gerar o arquivo `.env` com suas configurações.
  * Iniciar todos os serviços (PostgreSQL, FastAPI) usando o `docker-compose`.

<!-- end list -->

```bash
# Dar permissão de execução ao script
chmod +x setup_cli.sh

# Rodar a CLI para configurar e iniciar
./setup_cli.sh
```

Siga as instruções na tela para configurar seu ambiente.

### 3\. Acessar os Serviços

Uma vez que os contêineres estiverem rodando (`docker-compose up -d`):

  * **API do Gateway**: `http://<ip>:8000`
  * **pgAdmin (Opcional)**: `http://<ip>:5050`
      * **E-mail**: `admin@gateway.com`
      * **Senha**: `admin_password`
      * Para conectar ao banco de dados, use o host `db` e a porta `5432`.

### 4\. Parar os Serviços

Para parar a infraestrutura e remover os contêineres:

```bash
docker-compose down
```

## 🛠️ Estrutura do Projeto

```
.
├── .env                  # Variáveis de ambiente
├── Dockerfile            # Configuração da imagem Docker da API
├── docker-compose.yml    # Orquestração dos serviços
├── requirements.txt      # Dependências Python
├── setup_cli.sh          # Script CLI para configuração e execução
│
└── app/
    ├── database_manager.py # Lógica de comunicação com o PostgreSQL
    ├── cloud_sender.py     # Lógica de envio e reenvio para a nuvem
    └── main.py             # A API FastAPI e a lógica principal do gateway
```

## 📜 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](https://www.google.com/search?q=LICENSE) para detalhes.
