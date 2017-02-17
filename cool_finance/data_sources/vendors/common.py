import logging

from cool_finance.data_sources import constants as const

logger = logging.getLogger(__name__)


class BaseSource(object):

    vendor_name = const.BASE_VENDOR

    # _supported_apis = []
    _support_data_json = True
    _translate_vendor_specific_key_to_common_key = True
    # _data_json_keys = {common_key:vendor_specific_key}
    _data_json_keys = {
        const.INDEX: const.INDEX,
        const.STOCK_SYMBOL: const.STOCK_SYMBOL,
        const.LAST_TRADE_PRICE: const.LAST_TRADE_PRICE,
        const.LAST_TRADE_DATETIME: const.LAST_TRADE_DATETIME,
        const.LAST_TRADE_DATE: const.LAST_TRADE_DATE,
        const.LAST_TRADE_TIME: const.LAST_TRADE_TIME,
        const.YIELD: const.YIELD,
        const.DIVIDEND: const.DIVIDEND
    }
    _data_json_related_apis = [
        "fetch_data_json",
        "refresh_data_json",
        "get_data_json",
        "get_value_from_data_json"
    ]

    def __init__(self, stock_symbol, *args, **kwargs):
        self.stock_symbol = stock_symbol
        if self._support_data_json:
            self._data_json = self.fetch_data_json(self.stock_symbol)

    def __getattr__(self, name):
        if (not self._support_data_json and
                name in self._data_json_related_apis):
            raise NotImplementedError(
                "Method %s is not implemented by data source: %s.",
                name, self.vendor_name)
        else:
            return super(BaseSource, self).__getattribute__(name)

    def _key_translate(self, data_json):
        if self._translate_vendor_specific_key_to_common_key:
            for c_key, v_key in self._data_json_keys.items():
                data_json[c_key] = data_json.pop(v_key)

        return data_json

    def _fetch(self, *args, **kwargs):
        # make your vendor specific request here...
        # return a json dict
        stock_symbol = self.stock_symbol
        data_json = {}
        for key in self._data_json_keys.keys():
            data_json[key] = "foo"
        return data_json

    def fetch_data_json(self, *args, **kwargs):
        data_json = self._fetch(args, kwargs)
        self._data_json = self._key_translate(data_json)
        return self._data_json

    def fetch(self, *args, **kwargs):
        return self.fetch_data_json(args, kwargs)

    def refresh_data_json(self, *args, **kwargs):
        return self.fetch_data_json(args, kwargs)

    def refresh(self, *args, **kwargs):
        return self.refresh_data_json(args, kwargs)

    def get_data_json(self):
        return self._data_json

    def get_value_from_data_json(self, key, is_common_key=True):
        # if is_common_key, keys must be in self._data_json_keys.keys()
        # if not is_common_key, it means vendor specific key
        if is_common_key and key not in self._data_json_keys.keys():
            raise KeyError(
                "Common key %s is not supported by data source %s.",
                key, self.vendor_name)

        return self._data_json[key]

    def get_price(self):
        return self._data_json[const.LAST_TRADE_PRICE]
