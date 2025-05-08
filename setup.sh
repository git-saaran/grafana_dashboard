#!/bin/bash
# File to be placed in ./setup.sh

set -e

echo "Setting up Zerodha Grafana Dashboard with Token Manager"

# Create necessary directories
mkdir -p clickhouse/config
mkdir -p clickhouse/initdb
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p data-collector
mkdir -p token-manager

# Set up token manager files
cp token_manager.py token-manager/
cp login_1.py token-manager/
cp token-manager/Dockerfile token-manager/
cp token-manager/requirements.txt token-manager/
cp token-manager/entrypoint.sh token-manager/
chmod +x token-manager/entrypoint.sh

# Copy existing tokens if available
if [ -f "fyers_refresh_token.txt" ]; then
  cp fyers_refresh_token.txt token-manager/
  echo "Copied existing refresh token"
else
  echo "Note: No existing refresh token found. The token manager will run login.py to generate one."
fi

if [ -f "fyers_access_token.txt" ]; then
  cp fyers_access_token.txt token-manager/
  cp fyers_access_token.txt data-collector/access_token.txt
  echo "Copied existing access token"
else
  echo "Note: No existing access token found. The token manager will generate one on startup."
fi

# Create .env file for token manager
if [ -f ".env" ]; then
  cp .env token-manager/
  echo "Copied .env file to token manager"
else
  # Create a basic .env file
  echo "# Fyers API credentials" > token-manager/.env
  read -p "Enter your Fyers PIN: " FYERS_PIN
  echo "FYERS_PIN=$FYERS_PIN" >> token-manager/.env
  echo "Created new .env file with PIN"
fi

# Create .env file for main project
cat > .env << EOL
ZERODHA_API_KEY=$(grep -o 'API_KEY = "[^"]*"' login_1.py | cut -d'"' -f2 || echo "your_api_key_here")

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
echo ""
echo "Token manager logs can be viewed with:"
echo "  docker-compose logs token-manager"
