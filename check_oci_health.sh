cat > run_health_check.sh << 'EOF'
#!/bin/bash

# Configuration
PROJECT_NAME="scratch" # Adjust if your podman-compose project name is different
MYSQL_CONTAINER="${PROJECT_NAME}_mysql_1"
TEMPORAL_CONTAINER="${PROJECT_NAME}_temporal_1"
WORKER_CONTAINER="${PROJECT_NAME}_worker_1"
FRONTEND_CONTAINER="${PROJECT_NAME}_frontend_1"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================"
echo "P&A SYSTEM HEALTH CHECK (OCI)"
echo "Date: $(date)"
echo "============================================"

check_container() {
    local name=$1
    # Try to find container by partial name if exact name fails
    local cid=$(podman ps -q --filter "name=$name")
    
    if [ -n "$cid" ]; then
        local state=$(podman inspect -f '{{.State.Status}}' $cid)
        if [ "$state" == "running" ]; then
            echo -e "[${GREEN}OK${NC}] Container '$name' is RUNNING"
            return 0
        else
            echo -e "[${RED}FAIL${NC}] Container '$name' is in state: $state"
            return 1
        fi
    else
        echo -e "[${RED}FAIL${NC}] Container matching '$name' NOT FOUND"
        return 1
    fi
}

check_http() {
    local url=$1
    local name=$2
    local code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$code" == "200" ] || [ "$code" == "302" ]; then
        echo -e "[${GREEN}OK${NC}] $name is responding (HTTP $code)"
    else
        echo -e "[${RED}FAIL${NC}] $name check failed at $url (HTTP $code)"
        echo "    >>> Last logs for $name:"
        podman logs --tail 10 $(podman ps -q --filter "name=$name" | head -n 1) 2>/dev/null
    fi
}

echo ""
echo ">>> 1. Checking Container Status"
check_container "mysql"
check_container "temporal"
check_container "worker"
check_container "frontend"
check_container "temporal-ui"

echo ""
echo ">>> 2. Checking Service Endpoints"
# Frontend (Streamlit)
check_http "http://localhost:8501/_stcore/health" "Frontend Health"

# Temporal UI
check_http "http://localhost:8080" "Temporal UI"

echo ""
echo ">>> 3. Checking Database Connection (from Worker)"
# Execute a simple python script inside worker to test DB connectivity
WORKER_ID=$(podman ps -q --filter "name=worker" | head -n 1)
if [ -n "$WORKER_ID" ]; then
    echo "Running connectivity test inside worker container..."
    podman exec $WORKER_ID python -c "
import os, MySQLdb, sys
try:
    db = MySQLdb.connect(
        host=os.environ.get('MYSQL_HOST'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER'),
        passwd=os.environ.get('MYSQL_PASSWORD'),
        db=os.environ.get('MYSQL_DATABASE')
    )
    print('   [OK] Successfully connected to MySQL')
    db.close()
except Exception as e:
    print(f'   [FAIL] Database connection error: {e}')
    sys.exit(1)
"
    if [ $? -eq 0 ]; then
        echo -e "[${GREEN}OK${NC}] Database connectivity verified"
    else
        echo -e "[${RED}FAIL${NC}] Database connectivity failed"
    fi
else
    echo -e "[${RED}SKIP${NC}] Cannot test DB: Worker container not found"
fi

echo ""
echo ">>> 4. Checking Temporal Service"
# Check if Temporal is ready
TEMPORAL_ID=$(podman ps -q --filter "name=temporal" | head -n 1)
if [ -n "$TEMPORAL_ID" ]; then
    if curl -s http://localhost:7233 > /dev/null; then 
         echo "Checking Temporal logs for startup confirmation..."
         if podman logs $TEMPORAL_ID 2>&1 | grep -q "service started"; then
             echo -e "[${GREEN}OK${NC}] Temporal service appears to be started"
         else
             echo -e "[${RED}WARN${NC}] Could not confirm Temporal startup in logs"
         fi
    else
         echo -e "[${RED}WARN${NC}] Temporal port 7233 not reachable via curl (expected for gRPC)"
    fi
fi

echo ""
echo "============================================"
echo "End of Health Check"
EOF

chmod +x run_health_check.sh
./run_health_check.sh
