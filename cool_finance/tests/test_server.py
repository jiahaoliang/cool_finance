import mock
from mock import Mock
from mock import patch
import unittest
try:
    from urllib.error import HTTPError
except ImportError:  # python 2
    from urllib2 import HTTPError

from cool_finance import server

sample_stock_setting = {
    "name": "QCOM",
    "targets_list": [20, 10, 30],
    "interval_s": 10
}


class TestWorker(unittest.TestCase):

    def setUp(self):
        db_client = Mock()
        datasource_mgr = Mock()
        stock_setting = sample_stock_setting
        stop_event = Mock(return_value=False)
        stop_event.wait = Mock(return_value=False)
        stop_event.is_set = Mock(return_value=False)
        self.patcher = patch("threading.Thread")
        self.worker = server.Worker(db_client, datasource_mgr,
                                    stock_setting, stop_event)

    def tearDown(self):
        self.worker = None

    def test_run_when_data_fetch_fail(self):
        failed_get_stock_data = Mock(
            side_effect=HTTPError("", 500, "msg", "hdrs", None))
        server.Worker._get_stock_data = failed_get_stock_data
        with patch("logging.Logger.warning") as mock_logging:
            mock_logging.side_effect = HTTPError("", 500, "msg", "hdrs", None)
            with self.assertRaises(HTTPError):
                self.worker.run()
        failed_get_stock_data.assert_called()

    def _set_stop_event(self):
        self.worker.stopped.is_set = Mock(return_value=True)
        return mock.DEFAULT

    def test_run_when_data_fetch_succeed(self):
        data = Mock()
        data.get_price = Mock(return_value="12345",
                              side_effect=self._set_stop_event)
        successful_get_stock_data = Mock(return_value=data)
        server.Worker._get_stock_data = successful_get_stock_data
        self.worker.run()
        successful_get_stock_data.assert_called()
