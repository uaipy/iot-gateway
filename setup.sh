#!/bin/bash

# --- Cores e Estilos ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Funções de Validação ---

check_dependency() {
  if ! command -v "$1" &> /dev/null
  then
    echo -e "${RED}ERRO: $1 não foi encontrado.${NC}"
    echo -e "Por favor, instale o $1 e tente novamente."
    echo -e "Exemplo: sudo apt-get install $1"
    exit 1
  fi
}

# --- Validação das Ferramentas ---
echo -e "${YELLOW}--- Verificando dependências... ---${NC}"
check_dependency "docker"
echo -e "${GREEN}Docker e Docker Compose encontrados. Continuando...${NC}"

# --- Coleta de Dados do Usuário ---
echo -e "${YELLOW}--- Configuração do Servidor Gateway ---${NC}"
echo "Insira as informações. Pressione ENTER para usar o valor padrão."

# Função para obter entrada do usuário com valor padrão
get_input() {
    local prompt="$1"
    local default_value="$2"
    local input_value
    
    # Mostra o valor atual ou padrão
    read -p "$prompt (Padrão: $default_value): " input_value
    
    # Retorna o valor de entrada ou o padrão
    if [[ -z "$input_value" ]]; then
        echo "$default_value"
    else
        echo "$input_value"
    fi
}

# Carrega valores existentes do .env se o arquivo existir
if [ -f .env ]; then
  echo -e "${YELLOW}Arquivo .env existente detectado. Usando os valores como padrão.${NC}"
  # Source para carregar as variáveis no ambiente do script
  set -a; source .env; set +a
fi

# Pede as configurações do banco de dados
DB_USER=$(get_input "Usuário do PostgreSQL" "${DB_USER:-postgres}")
DB_PASSWORD=$(get_input "Senha do PostgreSQL" "${DB_PASSWORD:-postgres}")
DB_NAME=$(get_input "Nome do banco de dados" "${DB_NAME:-sensor_data}")

# Pede a URL da API da nuvem
CLOUD_API_URL=$(get_input "URL da API na nuvem" "${CLOUD_API_URL:-http://sua-api-na-nuvem.com/api/readings}")

# Pede o intervalo do agendador
SEND_INTERVAL_SECONDS=$(get_input "Intervalo de reenvio (em segundos)" "${SEND_INTERVAL_SECONDS:-300}")

# --- Geração do Arquivo .env ---
echo -e "${YELLOW}--- Gerando arquivo .env... ---${NC}"
cat > .env << EOF
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
DB_HOST=db
DB_PORT=5432
CLOUD_API_URL=${CLOUD_API_URL}
SEND_INTERVAL_SECONDS=${SEND_INTERVAL_SECONDS}
EOF

echo -e "${GREEN}Arquivo .env gerado com sucesso!${NC}"
echo ""

# --- Execução do Docker Compose ---
echo -e "${YELLOW}--- Iniciando a infraestrutura com Docker Compose... ---${NC}"
docker compose up -d

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Servidor iniciado com sucesso!${NC}"
  echo -e "A API está rodando na porta 8000."
  echo "Para verificar os logs, use: ${YELLOW}docker compose logs -f${NC}"
  echo "Para parar os serviços, use: ${YELLOW}docker compose down${NC}"
else
  echo -e "${RED}ERRO: Ocorreu um erro ao iniciar os serviços.${NC}"
  echo "Verifique as mensagens de erro acima ou execute 'docker compose up' manualmente para mais detalhes."
fi