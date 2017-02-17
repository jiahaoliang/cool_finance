from cool_finance.data_sources import constants as const
from cool_finance.data_sources.vendors import (common, google_finance,
                                               google_finance_batch)


class DataSourceManager(object):

    _supported_vendors = {
        const.BASE_VENDOR: common.BaseSource,
        const.GOOGLE_FINANCE_VENDOR: google_finance.GoogleFinance,
        const.GOOGLE_FINANCE_BATCH_VENDOR:
            google_finance_batch.GoogleFinanceBatch
    }

    _support_batch_query_vendor = {
        const.GOOGLE_FINANCE_BATCH_VENDOR:
            google_finance_batch.GoogleFinanceBatch
    }

    def __init__(self, default_vendor=const.DEFAULT_DATASOURCE):
        self._default_vendor = default_vendor

    def get_vendor(self, vendor=None):
        # return the vendor class
        if not vendor:
            vendor = self._default_vendor
        return self._supported_vendors[vendor]
