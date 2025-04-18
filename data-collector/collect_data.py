# data-collector/collect_data.py
import os
import time
import datetime
import logging
import schedule
import clickhouse_driver
from kiteconnect import KiteConnect
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize ClickHouse client
client = clickhouse_driver.Client(
    host='clickhouse',
    port=9000,
    database='default',
    user='default',
    password='default'
)

# Create tables if they don't exist
def setup_database():
    logger.info("Setting up database...")
    
    # Create database if not exists
    client.execute('''
    CREATE DATABASE IF NOT EXISTS zerodha
    ''')
    
    # Create holdings table with TTL
    client.execute('''
    CREATE TABLE IF NOT EXISTS zerodha.holdings (
        timestamp DateTime,
        trading_symbol String,
        exchange String,
        instrument_token UInt64,
        isin String,
        product String,
        quantity Int32,
        average_price Float64,
        last_price Float64,
        close_price Float64,
        pnl Float64,
        day_change Float64,
        day_change_percentage Float64
    ) ENGINE = MergeTree()
    PARTITION BY toYYYYMMDD(timestamp)
    ORDER BY (timestamp, trading_symbol)
    TTL timestamp + INTERVAL 2 DAY TO DELETE
    ''')

# Initialize Kite Connect
def initialize_kite():
    try:
        # Load access token from file
        with open("access_token.txt", "r") as file:
            access_token = file.read().strip()
        
        # Initialize KiteConnect with API key and access token
        kite = KiteConnect(api_key=os.getenv("API_KEY"))
        kite.set_access_token(access_token)
        
        return kite
    except Exception as e:
        logger.error(f"Error initializing Kite Connect: {e}")
        return None

# Get holdings data and store in ClickHouse
def collect_holdings_data():
    try:
        now = datetime.datetime.now()
        
        # Check if it's within market hours (9:15 AM to 3:30 PM) and a weekday (1-5)
        if (now.hour < 9 or (now.hour == 9 and now.minute < 15) or 
            now.hour > 15 or (now.hour == 15 and now.minute > 30) or 
            now.weekday() > 4):
            logger.info("Outside market hours, skipping data collection")
            return
        
        kite = initialize_kite()
        if not kite:
            return
        
        # Get holdings data
        holdings = kite.holdings()
        
        if not holdings:
            logger.info("No holdings data available")
            return
        
        # Prepare data for insertion
        current_time = datetime.datetime.now()
        rows = []
        
        for holding in holdings:
            rows.append((
                current_time,
                holding['tradingsymbol'],
                holding['exchange'],
                holding['instrument_token'],
                holding['isin'],
                holding['product'],
                holding['quantity'],
                holding['average_price'],
                holding['last_price'],
                holding['close_price'],
                holding['pnl'],
                holding['day_change'],
                holding['day_change_percentage']
            ))
        
        # Insert data into ClickHouse
        client.execute(
            '''
            INSERT INTO zerodha.holdings (
                timestamp, trading_symbol, exchange, instrument_token, isin, product,
                quantity, average_price, last_price, close_price, pnl, day_change, day_change_percentage
            ) VALUES
            ''',
            rows
        )
        
        logger.info(f"Inserted {len(rows)} holdings records")
    
    except Exception as e:
        logger.error(f"Error collecting holdings data: {e}")

# Function to purge old data at 9 AM
def purge_old_data():
    try:
        logger.info("Running scheduled data purge...")
        # The TTL will handle most of the deletion, but we can force it here
        client.execute('''
        OPTIMIZE TABLE zerodha.holdings FINAL
        ''')
        logger.info("Data purge completed")
    except Exception as e:
        logger.error(f"Error during data purge: {e}")

# Main function
def main():
    # Setup database on startup
    setup_database()
    
    # Schedule data collection every 5 minutes during market hours
    schedule.every(5).minutes.do(collect_holdings_data)
    
    # Schedule data purge at 9 AM every day
    schedule.every().day.at("09:00").do(purge_old_data)
    
    # Run once at startup
    collect_holdings_data()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
