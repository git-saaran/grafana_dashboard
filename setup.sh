#!/bin/bash

# Create necessary directories
mkdir -p clickhouse grafana/provisioning/datasources grafana/provisioning/dashboards grafana/dashboards data-collector

# Copy files to appropriate locations
# ClickHouse config
cp clickhouse-config.xml clickhouse/config.xml
cp clickhouse-users.xml clickhouse/users.xml

# Grafana config
cp grafana-datasource-config.yaml grafana/provisioning/datasources/clickhouse.yaml
cp grafana-dashboard-config.yaml grafana/provisioning/dashboards/zerodha.yaml
cp grafana-dashboard-json.json grafana/dashboards/zerodha-holdings.json

# Data collector
cp data-collector-script.py data-collector/collect_data.py
cp data-collector-dockerfile data-collector/Dockerfile
cp data-collector-requirements.txt data-collector/requirements.txt

# Create .env file
echo "Creating .env file in data-collector directory..."
cat > data-collector/.env << EOL
API_KEY=${API_KEY:-}
API_SECRET=${API_SECRET:-}
USER_ID=${USER_ID:-}
PASSWORD=${PASSWORD:-}
TOTP=${TOTP:-}
EOL

echo "Setup complete. Make sure to fill in your API credentials in data-collector/.env"
echo "Run 'docker-compose up -d' to start the services"
