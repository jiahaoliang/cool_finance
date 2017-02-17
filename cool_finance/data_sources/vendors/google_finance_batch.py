import datetime
from threading import Lock

from googlefinance import getQuotes

from cool_finance.constants import QUERY_PRECISION_S
from cool_finance.data_sources import constants as const
from cool_finance.data_sources.vendors.google_finance import GoogleFinance
from cool_finance.log import logger

LAST_UPDATE = "last_update"
STOCKS_DATA = "stocks_data"


class GoogleFinanceBatchHandler(object):

    _symbol_key = GoogleFinance._data_json_keys[const.STOCK_SYMBOL]

    def __init__(self):
        self._stocks_list = []
        # self._stocks_data = {"last_update":datetime,
        #                       "stocks_data": {
        #                               "ABC":{...}},
        #                               "BCD":{...}} } }
        self._stocks_data = {LAST_UPDATE: None,
                             STOCKS_DATA: {}}
        self._data_access_lock = Lock()

    def add_stock(self, stock_symbol):
        # googlefinance has a bug if the getQuote() input is unicode
        # change the type to str explicitly
        self._stocks_list.append(stock_symbol)

    def fetch(self, stock_symbol):
        # Multiple works could call fetch() as well as _should_update()
        # and _fetch_batch(). Must use the _data_access_lock to guard them.
        with self._data_access_lock:
            if self._should_update():
                self._stocks_data = self._fetch_batch(self._stocks_list)
                logger.debug("Look for %s, new request sent to Google",
                             stock_symbol)
            return dict(self._stocks_data[STOCKS_DATA][stock_symbol])

    def _should_update(self):
        if self._stocks_data[LAST_UPDATE]:
            now = datetime.datetime.now()
            last_update = self._stocks_data[LAST_UPDATE]
            delta = now - last_update
            if delta.total_seconds() <= QUERY_PRECISION_S:
                return False
        return True

    def _fetch_batch(self, stocks_list):
        if not stocks_list:
            stocks_list = self._stocks_list
        quotes_list = getQuotes(stocks_list)
        now = datetime.datetime.now()
        self._stocks_data[LAST_UPDATE] = now
        self._stocks_data[STOCKS_DATA].clear()
        for item in quotes_list:
            stock_symbol = item[self._symbol_key]
            self._stocks_data[STOCKS_DATA][stock_symbol] = item
        return self._stocks_data


batch_handler = GoogleFinanceBatchHandler()


class GoogleFinanceBatch(GoogleFinance):

    vendor_name = const.GOOGLE_FINANCE_BATCH_VENDOR

    def __init__(self, stock_symbol):
        super(GoogleFinanceBatch, self).__init__(stock_symbol)
        global batch_handler
        self.batch_handler = batch_handler
        # googlefinance has a bug if the getQuote() input is unicode
        # change the type to str explicitly
        stock_symbol = stock_symbol.encode('utf-8')
        self.batch_handler.add_stock(stock_symbol)

    def _fetch(self, *args, **kwargs):
        return self.batch_handler.fetch(self.stock_symbol)
