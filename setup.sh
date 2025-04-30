#!/bin/bash
# File to be placed in ./setup.sh

set -e

echo "Setting up Zerodha Grafana Dashboard"

# Create necessary directories
mkdir -p clickhouse/config
mkdir -p clickhouse/initdb
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p data-collector

# Copy the access token file to the data-collector directory
if [ -f "access_token.txt" ]; then
  cp access_token.txt data-collector/
else
  echo "Warning: access_token.txt not found in the current directory."
  echo "Please make sure to run login.py and copy the access_token.txt file to the data-collector directory."
fi

# Create .env file
cat > .env << EOL
ZERODHA_API_KEY=$(grep -o 'API_KEY = "[^"]*"' login.py | cut -d'"' -f2)

# Get server IP address (for informational purposes only)
SERVER_IP=$(hostname -I | awk '{print $1}')
EOL

echo "Docker Compose setup complete. Starting services..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 30  # Increased wait time to allow plugin installation

echo "Installation complete!"
echo "Grafana dashboard is now available at http://$(hostname -I | awk '{print $1}')"
echo "Default credentials: admin / admin"
echo ""
echo "Note: The ClickHouse plugin for Grafana will be installed automatically."
echo "If you encounter any issues with the data source, please check the Grafana logs:"
echo "  docker-compose logs grafana"
