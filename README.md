# Fyers API Data Collection and Visualization System

This project automatically collects data from the Fyers API, stores it in a ClickHouse database, and visualizes it with Grafana. The system includes an automated token manager that handles both the initial login process and daily access token refreshes.

## System Components

- **Token Manager**: Handles authentication with Fyers API
  - Automatically refreshes the access token daily at 8:00 AM IST
  - Checks the refresh token validity and runs the login process every 15 days
  - Ensures access tokens are always valid for data collection

- **Data Collector**: Retrieves data from Fyers API
  - Collects holdings data every 5 minutes during market hours
  - Stores data in ClickHouse database
  - Auto-purges data older than 2 days

- **ClickHouse**: Time-series database for storing financial data
  - High-performance columnar database
  - Efficient for time-series data analysis

- **Grafana**: Dashboard for data visualization
  - Pre-configured dashboards
  - Real-time data visualization

## Installation and Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher
- Fyers Trading Account with API access

### Setup Instructions

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   The setup script will:
   - Create necessary directories
   - Set up the token manager
   - Prompt for your Fyers PIN
   - Start all services with Docker Compose

3. After setup, your services will be running:
   - Grafana is available at `http://<your-server-ip>`
   - Default credentials: `admin` / `admin`

## Token Manager

The token manager handles the Fyers API authentication process:

- **Initial Login**: Uses `login_1.py` to authenticate with Fyers and get a refresh token (valid for 15 days)
- **Daily Refresh**: Uses the refresh token to generate a new access token daily at 8:00 AM IST
- **Token Monitoring**: Checks the refresh token validity daily at 7:00 AM IST and renews it if needed

### Manual Token Operations

If you need to manually manage tokens:

1. Generate a new refresh token:
   ```bash
   docker-compose exec token-manager python token
