cat > run_collect_config.sh << 'EOF'
#!/bin/bash

# Output file
OUTPUT_FILE="oci_config_dump.txt"

echo "============================================" > "$OUTPUT_FILE"
echo "OCI CONFIGURATION DUMP" >> "$OUTPUT_FILE"
echo "Generated on: $(date)" >> "$OUTPUT_FILE"
echo "============================================" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo ">>> HOST INFO" >> "$OUTPUT_FILE"
uname -a >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo ">>> PODMAN VERSION" >> "$OUTPUT_FILE"
podman version >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo ">>> RUNNING CONTAINERS (podman ps)" >> "$OUTPUT_FILE"
podman ps -a >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo ">>> NETWORK CONFIG (podman network inspect pna-network)" >> "$OUTPUT_FILE"
podman network inspect pna-network >> "$OUTPUT_FILE" 2>&1

# Function to dump file content safely
dump_file() {
    local filepath="$1"
    echo "" >> "$OUTPUT_FILE"
    echo ">>> FILE: $filepath" >> "$OUTPUT_FILE"
    if [ -f "$filepath" ]; then
        echo "--------------------------------------------" >> "$OUTPUT_FILE"
        cat "$filepath" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "--------------------------------------------" >> "$OUTPUT_FILE"
    else
        echo "[FILE NOT FOUND]" >> "$OUTPUT_FILE"
    fi
}

echo "Collecting configuration files..."

# Dump critical config files
dump_file "podman-compose.yml"
dump_file ".env"
dump_file "config/dynamicconfig/development-sql.yaml"

# Check for potential override files
dump_file "podman-compose.override.yml"
dump_file "docker-compose.yml"

# Check for custom scripts
dump_file "start.sh"
dump_file "deploy.sh"

echo ""
echo "Done! The configuration has been saved to: $OUTPUT_FILE"
echo "Please copy the content of '$OUTPUT_FILE' and share it with the assistant."
echo ""
echo "You can view it with: cat $OUTPUT_FILE"
EOF

chmod +x run_collect_config.sh
./run_collect_config.sh
