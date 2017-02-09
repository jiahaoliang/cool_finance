import datetime
import json
from threading import Event
from threading import Thread
import time

from pytz import timezone
import requests

from cool_finance import constants
from cool_finance import db
from cool_finance.data_sources.manager import DataSourceManager


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

    def _get_stock_data(self, stock_symbol):
        data = self.info_obj
        data.refresh()
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
        self._db_client = db.Client(constants.DB_HOST,
                                    constants.DB_PORT)
        self._datasource_mgr = DataSourceManager()
        self._worker_stopflag_list = []

    def _reload_config(self, config_file):
        with open(config_file) as stocks_config:
            stocks_json = json.load(stocks_config)
        # {"stocks": [{"name":, "less_than","greater_than", "interval_s"}]}
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

    def wait_all_workers_done(self):
        for worker, stopflag in self._worker_stopflag_list:
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
    server = Server()
    try:
        start_datetime, end_datetime, tz = get_start_and_end_datetime()
        if not constants.START_NOW:
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
