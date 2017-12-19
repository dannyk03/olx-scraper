# import sys

# from scrapy.utils.project import get_project_settings
# from scrapy.crawler import CrawlerProcess
from olx_scraper.spiders.olx_spider_2 import OlxSpider
# import multiprocessing as mp

# def scrape_module(queue):
#     crawler = CrawlerProcess(get_project_settings())
#     queue.put(crawler.crawl(OlxSpider))
#     # crawler.start()


# if __name__ == '__main__':
#     q = mp.Queue()
#     p = mp.Process(target=scrape_module, args=(q,))
#     p.start()
#     q.get()
#     p.join()


from scrapy import signals
from scrapy.conf import settings
from scrapy.crawler import CrawlerProcess
from scrapy.xlib.pydispatch import dispatcher
from multiprocessing.queues import Queue
import multiprocessing

class CrawlerWorker(multiprocessing.Process):

    def __init__(self, spider, result_queue):
        multiprocessing.Process.__init__(self)
        self.result_queue = result_queue

        self.crawler = CrawlerProcess(settings)

        self.items = []
        self.spider = spider
        dispatcher.connect(self._item_passed, signals.item_passed)

    def _item_passed(self, item):
        self.items.append(item)

    def run(self):
        self.crawler.crawl(self.spider)
        self.crawler.start()
        self.crawler.stop()
        self.result_queue.put(self.items)

if __name__=="__main__":
    result_queue = Queue()
    crawler = CrawlerWorker(OlxSpider, result_queue)
    crawler.start()