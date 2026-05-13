#!/bin/bash

# --- Cores e Estilos ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Funções ---

# Executa comando como root (sudo se necessário). Usado na instalação do Docker.
run_as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

# Verifica se o daemon Docker responde (com ou sem sudo).
docker_daemon_ok() {
  if docker info &>/dev/null; then
    return 0
  fi
  if run_as_root docker info &>/dev/null; then
    return 0
  fi
  return 1
}

# docker compose v2 (plugin) ou legado docker-compose.
# Escolhe "sudo" se o utilizador não tiver acesso ao socket Docker (comum após instalação nova).
docker_compose_cmd() {
  local prefix=""
  if docker info &>/dev/null; then
    prefix=""
  elif run_as_root docker info &>/dev/null; then
    prefix="sudo "
  else
    return 1
  fi

  if [[ -z "${prefix}" ]]; then
    if docker compose version &>/dev/null; then
      echo "docker compose"
      return 0
    fi
    if command -v docker-compose &>/dev/null; then
      echo "docker-compose"
      return 0
    fi
  else
    if run_as_root docker compose version &>/dev/null; then
      echo "sudo docker compose"
      return 0
    fi
    if command -v docker-compose &>/dev/null; then
      echo "sudo docker-compose"
      return 0
    fi
  fi
  return 1
}

# Instala Docker Engine + plugin Compose (script oficial; suporta Debian/Ubuntu e ARM — Armbian).
install_docker() {
  echo -e "${YELLOW}Docker não encontrado (ou incompleto). Instalando via get.docker.com...${NC}"
  echo -e "Compatível com Linux Debian/Ubuntu e derivados (incl. Armbian em ARM)."

  if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
    echo -e "${YELLOW}Instalando curl para baixar o instalador do Docker...${NC}"
    run_as_root apt-get update -qq
    run_as_root apt-get install -y -qq curl
  fi

  if command -v curl &>/dev/null; then
    curl -fsSL https://get.docker.com | run_as_root sh
  else
    wget -qO- https://get.docker.com | run_as_root sh
  fi

  local install_status=$?
  if [[ "${install_status}" -ne 0 ]]; then
    echo -e "${RED}ERRO: Falha ao instalar o Docker (código ${install_status}).${NC}"
    echo "Consulte: https://docs.docker.com/engine/install/debian/"
    exit 1
  fi

  run_as_root systemctl enable docker 2>/dev/null || true
  run_as_root systemctl start docker 2>/dev/null || true
}

# Garante Docker CLI + daemon + Compose disponíveis.
ensure_docker() {
  echo -e "${YELLOW}--- Verificando Docker... ---${NC}"

  if ! command -v docker &>/dev/null; then
    install_docker
  fi

  if ! command -v docker &>/dev/null; then
    echo -e "${RED}ERRO: O comando docker não está disponível após a instalação.${NC}"
    exit 1
  fi

  if ! docker_daemon_ok; then
    echo -e "${YELLOW}Tentando iniciar o serviço docker...${NC}"
    run_as_root systemctl start docker 2>/dev/null || true
    sleep 2
  fi

  if ! docker_daemon_ok; then
    echo -e "${RED}ERRO: O daemon Docker não responde (docker info falhou).${NC}"
    echo "Execute: sudo systemctl status docker"
    exit 1
  fi

  if ! docker compose version &>/dev/null && ! run_as_root docker compose version &>/dev/null; then
    if command -v docker-compose &>/dev/null; then
      echo -e "${GREEN}docker-compose (legado) encontrado.${NC}"
    else
      echo -e "${YELLOW}Instalando plugin docker-compose-plugin (apt)...${NC}"
      run_as_root apt-get update -qq
      run_as_root apt-get install -y -qq docker-compose-plugin || {
        echo -e "${RED}ERRO: docker compose não está disponível. Instale o plugin Compose.${NC}"
        exit 1
      }
    fi
  fi

  local dc
  dc=$(docker_compose_cmd) || {
    echo -e "${RED}ERRO: Não foi possível determinar o comando docker compose.${NC}"
    exit 1
  }
  export SETUP_DOCKER_COMPOSE="${dc}"
  echo -e "${GREEN}Docker pronto (${dc}). Continuando...${NC}"

  if ! docker info &>/dev/null && run_as_root docker info &>/dev/null; then
    echo -e "${YELLOW}Nota: seu usuário não está no grupo 'docker'. Use sudo para compose ou execute:${NC}"
    echo "  sudo usermod -aG docker \"\$USER\" && newgrp docker"
  fi
}

# --- Validação / instalação do Docker ---
ensure_docker

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
# SETUP_DOCKER_COMPOSE definido em ensure_docker (ex.: "docker compose" ou "sudo docker compose")
${SETUP_DOCKER_COMPOSE} up -d

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Servidor iniciado com sucesso!${NC}"
  echo -e "A API está rodando na porta 8000."
  echo "Para verificar os logs, use: ${YELLOW}${SETUP_DOCKER_COMPOSE} logs -f${NC}"
  echo "Para parar os serviços, use: ${YELLOW}${SETUP_DOCKER_COMPOSE} down${NC}"
else
  echo -e "${RED}ERRO: Ocorreu um erro ao iniciar os serviços.${NC}"
  echo "Verifique as mensagens de erro acima ou execute '${SETUP_DOCKER_COMPOSE} up -d' manualmente para mais detalhes."
fi