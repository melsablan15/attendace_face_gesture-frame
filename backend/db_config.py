import os
from dotenv import load_dotenv

# Load the secret variables from the .env file
load_dotenv()

DB_CONFIG = {
    'host': 'mysql-cf722f2-framessys01-cee4.c.aivencloud.com',
    'port': 21352,                              # Cloud DBs use special ports (not 3306)
    'user': 'avnadmin',
    'password': 'AVNS_s9Hfrp493AkDS7H3C1Y', 
    'database': 'defaultdb',                    # This will be 'defaultdb'
    'ssl_ca': 'ca.pem',                         # Ensure this file is in the same folder
    'ssl_disabled': False
}