import sys

from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from olx_scraper.spiders.olx_spider import OlxSpider

def scrape_module():
    crawler = CrawlerProcess(get_project_settings())
    crawler.crawl(OlxSpider)
    crawler.start()

if __name__ == '__main__':
    scrape_module()