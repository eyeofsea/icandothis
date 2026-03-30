#!/usr/bin/env bash
#
# setup.sh - Bootstrap the SCM Risk Intelligence Platform
#
# Checks prerequisites, starts Docker services, waits for readiness,
# seeds the Neo4j database, and prints access URLs.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Colours (degrade gracefully when piped)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    GREEN='' YELLOW='' RED='' CYAN='' NC=''
fi

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ---------------------------------------------------------------------------
# 1. Check prerequisites
# ---------------------------------------------------------------------------
info "Checking prerequisites..."

if ! command -v docker &>/dev/null; then
    fail "Docker is not installed. Please install Docker: https://docs.docker.com/get-docker/"
fi
ok "Docker found: $(docker --version)"

if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    fail "Docker Compose is not available. Install docker-compose or a Docker version with the compose plugin."
fi
ok "Docker Compose found: $($COMPOSE_CMD version --short 2>/dev/null || $COMPOSE_CMD version)"

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    fail "Python 3 is not installed. Please install Python 3.10+."
fi
PYTHON=$(command -v python3 || command -v python)
ok "Python found: $($PYTHON --version)"

# ---------------------------------------------------------------------------
# 2. Start Docker Compose services
# ---------------------------------------------------------------------------
info "Starting Docker Compose services..."
$COMPOSE_CMD up -d

# ---------------------------------------------------------------------------
# 3. Wait for Neo4j to become ready
# ---------------------------------------------------------------------------
info "Waiting for Neo4j to become ready..."

NEO4J_MAX_RETRIES=30
NEO4J_RETRY_INTERVAL=5
NEO4J_READY=false

for i in $(seq 1 $NEO4J_MAX_RETRIES); do
    if docker compose exec -T neo4j cypher-shell -u neo4j -p scmrisk2024 "RETURN 1" &>/dev/null; then
        NEO4J_READY=true
        break
    fi
    echo -n "."
    sleep $NEO4J_RETRY_INTERVAL
done
echo ""

if [ "$NEO4J_READY" = false ]; then
    fail "Neo4j did not become ready within $((NEO4J_MAX_RETRIES * NEO4J_RETRY_INTERVAL))s. Check logs: $COMPOSE_CMD logs neo4j"
fi
ok "Neo4j is ready."

# ---------------------------------------------------------------------------
# 4. Wait for PostgreSQL to become ready
# ---------------------------------------------------------------------------
info "Waiting for PostgreSQL to become ready..."

PG_MAX_RETRIES=20
PG_READY=false

for i in $(seq 1 $PG_MAX_RETRIES); do
    if docker compose exec -T postgres pg_isready -U scmrisk -d scm_risk_db &>/dev/null; then
        PG_READY=true
        break
    fi
    echo -n "."
    sleep 3
done
echo ""

if [ "$PG_READY" = false ]; then
    warn "PostgreSQL did not become ready in time. Continuing anyway..."
else
    ok "PostgreSQL is ready."
fi

# ---------------------------------------------------------------------------
# 5. Wait for Redis to become ready
# ---------------------------------------------------------------------------
info "Waiting for Redis to become ready..."

REDIS_MAX_RETRIES=10
REDIS_READY=false

for i in $(seq 1 $REDIS_MAX_RETRIES); do
    if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
        REDIS_READY=true
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

if [ "$REDIS_READY" = false ]; then
    warn "Redis did not become ready in time. Continuing anyway..."
else
    ok "Redis is ready."
fi

# ---------------------------------------------------------------------------
# 6. Install Python dependencies (if needed)
# ---------------------------------------------------------------------------
info "Checking Python dependencies..."

if ! $PYTHON -c "import neo4j" &>/dev/null; then
    info "Installing Python dependencies from backend/requirements.txt..."
    $PYTHON -m pip install -r backend/requirements.txt --quiet
    ok "Python dependencies installed."
else
    ok "Python dependencies already available."
fi

# ---------------------------------------------------------------------------
# 7. Run the Neo4j seed script
# ---------------------------------------------------------------------------
info "Seeding Neo4j database..."
$PYTHON backend/app/database/seed.py

if [ $? -eq 0 ]; then
    ok "Database seeded successfully."
else
    fail "Database seeding failed. Check output above for details."
fi

# ---------------------------------------------------------------------------
# 8. Print summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  SCM Risk Intelligence Platform - Setup Complete${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  ${CYAN}Neo4j Browser:${NC}    http://localhost:7474"
echo -e "                    User: neo4j / Password: scmrisk2024"
echo ""
echo -e "  ${CYAN}Neo4j Bolt:${NC}       bolt://localhost:7687"
echo ""
echo -e "  ${CYAN}PostgreSQL:${NC}       postgresql://scmrisk:scmrisk2024@localhost:5432/scm_risk_db"
echo ""
echo -e "  ${CYAN}Redis:${NC}            redis://localhost:6379"
echo ""
echo -e "  ${CYAN}Backend API:${NC}      http://localhost:8000  (start with: uvicorn backend.app.main:app --reload)"
echo -e "  ${CYAN}Frontend:${NC}         http://localhost:3000  (start with: cd frontend && npm run dev)"
echo ""
echo -e "${GREEN}============================================================${NC}"
