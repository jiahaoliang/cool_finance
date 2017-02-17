DB_HOST = "localhost"
DB_PORT = 27017
DB_NAME = "cool_finance_db"
PRICE_COLLECTION = "price_collection"

CONFIG_FILE = "./cool_finance.json"

# set START_NOW will override the START_HOUR_MIN_SEC
# and start the server immediately
START_NOW = False
START_HOUR_MIN_SEC = (9, 30, 00)
END_HOUR_MIN_SEC = (16, 00, 00)
TIMEZONE = 'US/Eastern'
# Sat, Sun are closed market day
CLOSED_WEEKDAYS = [5, 6]
