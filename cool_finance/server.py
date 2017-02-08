import datetime
import json
import signal
import sys
from threading import Event
from threading import Thread
import time

from pytz import timezone
from yahoo_finance import Share

from cool_finance import constants
from cool_finance import db
from ulits.forked_pdb import ForkedPdb


class Worker(Thread):
    def __init__(self, db_client, stock_setting, stop_event):
        super(Worker, self).__init__()
        self.stock_setting = stock_setting
        self.stock_symbol = stock_setting["name"]
        self.delay = stock_setting["interval_s"]
        self.targets_list = stock_setting.get("targets_list")
        self.db_client = db_client
        self.stopped = stop_event

    def _get_stock_data(self, stock_symbol):
        data = Share(stock_symbol)
        self.db_client.insert_one(data.data_set, stock_symbol)
        return data

    def _get_notice_msg(self, stock_setting, price):
        msg = dict(stock_setting)
        msg['price'] = price
        return msg

    def _send_nofitication(self, msg):
        print msg

    def run(self):
        while not (self.stopped.wait(self.delay) or self.stopped.is_set()):
            data = self._get_stock_data(self.stock_symbol)
            price = data.get_price()
            for target in self.targets_list:
                if abs(float(price) - target) <= 0.01:
                    notice_msg = self._get_notice_msg(
                        self.stock_setting, price)
                    self._send_nofitication(notice_msg)


class Server(object):

    def __init__(self, config_file=constants.CONFIG_FILE):
        self._reload_config(config_file)
        self.db_client = db.Client(constants.DB_HOST,
                                   constants.DB_PORT)
        self.worker_stopflag_list = []

    def _reload_config(self, config_file):
        with open(config_file) as stocks_config:
            stocks_json = json.load(stocks_config)
        # {"stocks": [{"name":, "less_than","greater_than", "interval_s"}]}
        self.stocks_list = stocks_json['stocks']

    def start(self):
        for stock in self.stocks_list:
            stopflag = Event()
            worker = Worker(self.db_client, stock, stopflag)
            self.worker_stopflag_list.append((worker, stopflag))

        for worker, stopflag in self.worker_stopflag_list:
            worker.start()

    def end(self):
        for worker, stopflag in self.worker_stopflag_list:
            stopflag.set()

    def wait_all_workers_done(self):
        for worker, stopflag in self.worker_stopflag_list:
            worker.join()


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

    delta = start_datetime - current_datetime
    print delta

    return start_datetime, end_datetime, tz


def main():
    try:
        server = Server()

        start_datetime, end_datetime, tz = get_start_and_end_datetime()
        while datetime.datetime.now(tz) < start_datetime:
            time.sleep(1)
        print "start"
        server.start()

        while datetime.datetime.now(tz) < end_datetime:
            time.sleep(1)
        print "end"
        server.end()
    except KeyboardInterrupt:
        print "KeyboardInterrupt"
        server.end()
    finally:
        server.wait_all_workers_done()