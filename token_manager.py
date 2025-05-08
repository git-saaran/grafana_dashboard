#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import subprocess
import schedule
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("token_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TokenManager')

class TokenManager:
    """Class to manage Fyers API tokens - handles login and token refresh"""
    
    def __init__(self, env_file='.env'):
        """Initialize with environment variables."""
        self.env_file = env_file
        self.refresh_token_file = "fyers_refresh_token.txt"
        self.access_token_file = "fyers_access_token.txt"
        self.app_id_hash = "220cdc5d2345d2e767f9537377c19c0ace440f2071dbdc13738ae68ca6d98d4e"
        
        # Load environment variables
        self._load_env(env_file)
        
    def _load_env(self, env_file):
        """Load configuration from environment variables or .env file."""
        # Try to load from .env file if it exists
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_file}")
        
        # Get PIN from environment variable or set a default
        self.pin = os.getenv('FYERS_PIN', '1978')  # Default PIN from your access_token.py
        
    def check_refresh_token_validity(self):
        """Check if the refresh token exists and is valid."""
        # Check if file exists
        if not Path(self.refresh_token_file).exists():
            logger.info("Refresh token file not found, need to perform initial login")
            return False
        
        # Check token age (valid for 15 days)
        token_file_stat = Path(self.refresh_token_file).stat()
        token_age_days = (datetime.datetime.now().timestamp() - token_file_stat.st_mtime) / (60*60*24)
        
        if token_age_days >= 14:  # Check a day early to be safe
            logger.info(f"Refresh token is {token_age_days:.1f} days old, needs renewal (valid for 15 days)")
            return False
            
        logger.info(f"Refresh token is {token_age_days:.1f} days old, still valid")
        return True
    
    def perform_initial_login(self):
        """Run the login_1.py script to get a fresh refresh token."""
        logger.info("Performing initial login to get new refresh token")
        try:
            result = subprocess.run(
                [sys.executable, "login_1.py"], 
                capture_output=True, 
                text=True
            )
            
            logger.info(f"Login script output: {result.stdout}")
            
            if "Authentication completed successfully" in result.stdout:
                logger.info("Initial login successful, refresh token generated")
                return True
            else:
                logger.error(f"Login script failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running login script: {str(e)}")
            return False
    
    def generate_access_token(self):
        """Generate an access token using the refresh token."""
        logger.info("Generating access token from refresh token")
        
        try:
            # Check if refresh token exists
            if not Path(self.refresh_token_file).exists():
                logger.error("Refresh token file not found")
                return False
                
            # Read the refresh token
            with open(self.refresh_token_file, "r") as file:
                refresh_token = file.read().strip()
                
            # Define the required data for the POST request
            data = {
                "grant_type": "refresh_token",
                "appIdHash": self.app_id_hash,
                "refresh_token": refresh_token,
                "pin": self.pin
            }
            
            # Convert the data dictionary to a JSON string
            data_json = json.dumps(data)
            
            # Construct the curl command
            curl_command = [
                "curl",
                "--location",
                "--request",
                "POST",
                "https://api-t1.fyers.in/api/v3/validate-refresh-token",
                "--header",
                "Content-Type: application/json",
                "--data-raw",
                data_json
            ]
            
            # Execute the curl command
            result = subprocess.run(curl_command, capture_output=True, text=True)
            logger.info(f"Curl response: {result.stdout}")
            
            # Parse the response as JSON
            response_json = json.loads(result.stdout)
            if response_json.get("s") == "ok" and "access_token" in response_json:
                access_token = response_json["access_token"]
                # Save the access token to a file
                with open(self.access_token_file, "w") as file:
                    file.write(access_token)
                logger.info(f"Access token successfully generated and saved to {self.access_token_file}")
                
                # Also copy the access token to the data-collector directory
                data_collector_token_file = Path("data-collector") / self.access_token_file
                if Path("data-collector").exists():
                    with open(data_collector_token_file, "w") as file:
                        file.write(access_token)
                    logger.info(f"Access token also copied to {data_collector_token_file}")
                
                return True
            else:
                logger.error(f"Failed to retrieve access token. Response: {response_json}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating access token: {str(e)}")
            return False
    
    def check_and_update_tokens(self):
        """Main function to check and update tokens as needed."""
        logger.info("Checking token status...")
        
        # Check if we need a new refresh token
        if not self.check_refresh_token_validity():
            logger.info("Need to generate new refresh token")
            if self.perform_initial_login():
                logger.info("Successfully generated new refresh token")
            else:
                logger.error("Failed to generate new refresh token")
                return False
        
        # Generate new access token
        if self.generate_access_token():
            logger.info("Successfully updated access token")
            return True
        else:
            logger.error("Failed to update access token")
            return False


def main():
    """Main function to run the token manager."""
    token_manager = TokenManager()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if "--generate-access-token" in sys.argv:
            # Just generate access token and exit
            logger.info("Running in access token generation mode")
            token_manager.generate_access_token()
            return
        elif "--check-tokens" in sys.argv:
            # Check and update tokens if needed, then exit
            logger.info("Running in token check mode")
            token_manager.check_and_update_tokens()
            return
    
    # If no args, run in normal mode with scheduler
    
    # Run initially on startup
    token_manager.check_and_update_tokens()
    
    # Schedule the token refresh daily at 8:00 AM IST
    schedule.every().day.at("08:00").do(token_manager.generate_access_token)
    
    # Schedule refresh token check every day at 7:00 AM IST
    schedule.every().day.at("07:00").do(token_manager.check_and_update_tokens)
    
    logger.info("Token manager started. Running scheduled tasks...")
    logger.info("Next token refresh will happen at 08:00 AM IST")
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()
