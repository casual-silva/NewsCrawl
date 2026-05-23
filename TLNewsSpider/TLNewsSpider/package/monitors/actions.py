import json
import requests
from spidermon.core.actions import Action


class CloseSpiderAction(Action):
    def run_action(self):
        spider = self.data["spider"]
        spider.logger.info("Closing spider")
        spider.crawler.engine.close_spider(spider, "closed_by_spidermon")


class SendFeiShuAction(Action):
    webHookURL = 'https://open.feishu.cn/open-apis/bot/hook/b5b9c7dd-2504-4a64-a43a-141fc0e4e2e5'

    def run_action(self):
        item_extracted = getattr(self.data.stats, "item_scraped_count", 0)
        msg = f"item scraped count: >{item_extracted}< for >{self.data.spider.name}<"

        sendData = {
            'title': f"Spidermon Item Count for {self.data.spider.name}",
            'text': msg,
        }

        response = requests.post(url=self.webHookURL, json=sendData)
        return response


class SendFeiShuSpiderCloseAction(Action):
    webHookURL = 'https://open.feishu.cn/open-apis/bot/hook/b5b9c7dd-2504-4a64-a43a-141fc0e4e2e5'

    def run_action(self):
        sendData = {
            'title': f"Spidermon Spider Close Stats for {self.data.spider.name}",
            'text': str(self.data.stats),
        }

        response = requests.post(url=self.webHookURL, json=sendData)
        return response
