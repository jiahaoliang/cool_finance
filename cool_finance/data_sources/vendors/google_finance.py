import logging

from googlefinance import getQuotes

from cool_finance.data_sources import constants as const
from cool_finance.data_sources.vendors.common import BaseSource

logger = logging.getLogger(__name__)


class GoogleFinance(BaseSource):

    vendor_name = const.GOOGLE_FINANCE_VENDOR

    _data_json_keys = {
        const.INDEX: "Index",
        const.STOCK_SYMBOL: "StockSymbol",
        const.LAST_TRADE_PRICE: "LastTradePrice",
        const.LAST_TRADE_DATETIME: "LastTradeDateTime",
        const.LAST_TRADE_TIME: "LastTradeTime"
    }

    _data_json_optional_keys = {
        const.YIELD: "Yield",
        const.DIVIDEND: "Dividend"
    }

    def _fetch(self, *args, **kwargs):
        # googlefinance has a bug if the getQuote() input is unicode
        # change the type to str explicitly
        stock_symbol = self.stock_symbol.encode('utf-8')
        return getQuotes(stock_symbol)[0]
