DB_HOST = "localhost"
DB_PORT = 27017
DB_NAME = "cool_finance_db"
PRICE_COLLECTION = "price_collection"

CONFIG_FILE = "./cool_finance.json"

LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(threadName)s - ' \
             '%(levelname)s - %(message)s'
# DEBUG_LOG_LEVEL must stricter than LOG_LEVEL
# if DEBUG_LOG_DIR is not None, DEBUG_LOG_LEVEL must be set
# if if DEBUG_LOG_DIR is None, DEBUG_LOG_LEVEL would be ignored
DEBUG_LOG_DIR = None
DEBUG_LOG_LEVEL = "DEBUG"

# set START_NOW will override the START_HOUR_MIN_SEC
# and start the server immediately
START_NOW = True
START_HOUR_MIN_SEC = (9, 30, 00)
END_HOUR_MIN_SEC = (16, 00, 00)
TIMEZONE = 'US/Eastern'
# Sat, Sun are closed market day
CLOSED_WEEKDAYS = [5, 6]
# Only one notification will be generated
# every NOTIFICATION_INTERVAL_S seconds for same stock.
NOTIFICATION_INTERVAL_S = 300
# Guarantee query result is within QUERY_PRECISION_S seconds up to date.
# A significant large number (10x, 100x) can reduce query amount to
# date source server. Tweak it if you have a daily query limit.
# Google data source doesn't seem to have a limit.
QUERY_PRECISION_S = 0.1
