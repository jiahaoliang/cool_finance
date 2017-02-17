import datetime
import json
from threading import Event
from threading import Thread
import time

from pytz import timezone
import requests

from . import constants
from . import db
from .data_sources.manager import DataSourceManager
from .log import logger

# server will be initialized in main()
server = None




class Worker(Thread):
    def __init__(self, db_client, datasource_mgr, stock_setting, stop_event):
        super(Worker, self).__init__()
        self.stock_setting = stock_setting
        self.stock_symbol = stock_setting["name"]
        self.delay = stock_setting["interval_s"]
        self.targets_list = stock_setting.get("targets_list")
        self.db_client = db_client
        self.stopped = stop_event
        self.info_obj = datasource_mgr.get_vendor()(self.stock_symbol)
        self._last_notification_datetime = None

    def _get_stock_data(self, stock_symbol):
        data = self.info_obj
        data.fetch()
        data_set = data.get_data_json()
        self.db_client.insert_one(data_set, stock_symbol)
        return self.info_obj

    def _get_notice_msg(self, stock_setting, price):
        # msg = dict(stock_setting)
        # msg['price'] = price
        # return msg
        payload = {'value1': self.stock_symbol,
                   'value2': price,
                   'value3': "test"}
        return payload

    def _send_nofitication(self, msg):
        r = requests.post("https://maker.ifttt.com/trigger/log_update/"
                          "with/key/cJmpqL9rVFwEOAnNmRAfFn",
                          data=msg)
        logger.info("Sent notification: %s", msg)

    def run(self):
        while not (self.stopped.wait(self.delay) or self.stopped.is_set()):
            try:
                data = self._get_stock_data(self.stock_symbol)
            except Exception as err:
                logger.warning("Fetch stock info %s failed. Retry later. "
                               "Reason: %s", self.stock_symbol, err,
                               exc_info=True)
                continue
            price = data.get_price()
            logger.debug("Got %s price: $%s", self.stock_symbol, str(price))
            for target in self.targets_list:
                if abs(float(price) - target) <= 0.01:
                    notice_msg = self._get_notice_msg(
                        self.stock_setting, price)
                    now = datetime.datetime.now()
                    if (not self._last_notification_datetime or
                            (now - self._last_notification_datetime).
                            total_seconds() >=
                            constants.NOTIFICATION_INTERVAL_S):
                        self._send_nofitication(notice_msg)
                        self._last_notification_datetime = now


class Server(object):

    def __init__(self, config_file=constants.CONFIG_FILE):
        self._config_file = config_file
        self.reload_config(self._config_file)
        self._db_client = db.Client(constants.DB_HOST,
                                    constants.DB_PORT)
        self._datasource_mgr = DataSourceManager()
        self._worker_stopflag_list = []

    def reload_config(self, config_file=None):
        if not config_file:
            config_file = self._config_file
        with open(config_file) as stocks_config:
            stocks_json = json.load(stocks_config)
        # {"stocks": [{"name":"", "targets_list":[int], "interval_s": int}]}
        self.stocks_list = stocks_json['stocks']

    def start(self):
        for stock in self.stocks_list:
            stopflag = Event()
            worker = Worker(self._db_client, self._datasource_mgr,
                            stock, stopflag)
            self._worker_stopflag_list.append((worker, stopflag))

        for worker, stopflag in self._worker_stopflag_list:
            worker.start()

    def end(self):
        for worker, stopflag in self._worker_stopflag_list:
            stopflag.set()

    def restart(self):
        self.end()
        self.wait_all_workers_done()
        self.reload_config()
        self.start()

    def wait_all_workers_done(self):
        for index, (worker, stopflag) in enumerate(self._worker_stopflag_list):
            worker.join()
            self._worker_stopflag_list.pop(index)


def get_start_and_end_datetime(start_hour_min_sec=constants.START_HOUR_MIN_SEC,
                               end_hour_min_sec=constants.END_HOUR_MIN_SEC,
                               tz=timezone(constants.TIMEZONE)):
    current_datetime = datetime.datetime.now(tz)
    start_datetime = current_datetime.replace(hour=start_hour_min_sec[0],
                                              minute=start_hour_min_sec[1],
                                              second=start_hour_min_sec[2])
    if start_datetime < current_datetime:
        start_datetime += datetime.timedelta(days=1)
    weekday = start_datetime.weekday()
    if weekday in constants.CLOSED_WEEKDAYS:
        start_datetime += datetime.timedelta(days=(7 - weekday))

    end_datetime = start_datetime.replace(hour=end_hour_min_sec[0],
                                          minute=end_hour_min_sec[1],
                                          second=end_hour_min_sec[2])

    return start_datetime, end_datetime, tz


def main():
    logger.info("Welcome to Cool Finance by F.JHL.")
    global server
    server = Server()
    try:
        while True:
            server.reload_config()
            start_datetime, end_datetime, tz = get_start_and_end_datetime()
            if not constants.START_NOW:
                logger.info("The server will start at %s.", start_datetime)
                logger.info("The server will end at %s.", end_datetime)
                delta = start_datetime - datetime.datetime.now(tz)
                logger.info("The server will start %s later.", delta)
                while datetime.datetime.now(tz) < start_datetime:
                    time.sleep(1)
            logger.info("The server is going to start.")
            server.start()
            logger.info("The server is already started.")

            while datetime.datetime.now(tz) < end_datetime:
                time.sleep(1)
            logger.info("The server is going to end.")
            server.end()
            logger.info("The server is already end.")
    except (KeyboardInterrupt, Exception) as err:
        logger.info("Exception %s: The server is going to end.", err)
        server.end()
        logger.info("The server is already end.")
    finally:
        logger.info("The server is going to wait for "
                    "all pending jobs complete.")
        server.wait_all_workers_done()
        logger.info("All jobs completes. Bye.")
