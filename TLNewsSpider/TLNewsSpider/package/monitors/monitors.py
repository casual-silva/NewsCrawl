# monitors.py
from spidermon import Monitor, MonitorSuite, monitors
from spidermon.contrib.monitors.mixins import StatsMonitorMixin
from .actions import SendFeiShuAction, SendFeiShuSpiderCloseAction


@monitors.name("Spider Close Stats")
class SpiderCloseStatsMonitor(Monitor):
    @monitors.name("Spider Close Data Stats")
    def test_spider_close_data_stats(self):
        pass


@monitors.name("Item Count")
class PeriodicItemCountMonitor(Monitor, StatsMonitorMixin):
    @monitors.name("The item count periodically")
    def test_count_of_items(self):
        pass


class PeriodicMonitorSuite(MonitorSuite):
    monitors_finished_actions = [SendFeiShuAction]


class SpiderCloseMonitorSuite(MonitorSuite):
    monitors_finished_actions = [SendFeiShuSpiderCloseAction]
