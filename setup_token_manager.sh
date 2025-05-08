#!/bin/bash
# Setup script for the token manager

set -e

echo "Setting up Fyers Token Manager"

# Create necessary directories
mkdir -p token-manager

# Copy the token manager files to the token-manager directory
cp token_manager.py token-manager/
cp login_1.py token-manager/

# Copy existing credentials if available
if [ -f "fyers_refresh_token.txt" ]; then
  cp fyers_refresh_token.txt token-manager/
  echo "Copied existing refresh token"
fi

if [ -f "fyers_access_token.txt" ]; then
  cp fyers_access_token.txt token-manager/
  echo "Copied existing access token"
fi

if [ -f ".env" ]; then
  cp .env token-manager/
  echo "Copied .env file"
else
  # Create a basic .env file
  echo "# Fyers API credentials" > token-manager/.env
  read -p "Enter your Fyers PIN: " FYERS_PIN
  echo "FYERS_PIN=$FYERS_PIN" >> token-manager/.env
  echo "Created new .env file with PIN"
fi

# Copy the Dockerfile and other files to the token-manager directory
cp token-manager/Dockerfile token-manager/
cp token-manager/requirements.txt token-manager/
cp token-manager/entrypoint.sh token-manager/

# Make entrypoint executable
chmod +x token-manager/entrypoint.sh

echo "Token Manager setup complete."
echo "You can now build and run it using Docker Compose."
