import logging
import re
import os
import django
import scrapy
import requests
import json
import datetime
from os import sys, path
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from lxml import etree
from scrapy.utils.log import configure_logging  
import pdb
import time
import ast
import base64
import httplib
import schedule
import threading
from .my_thread import MyThread
import signal
import hashlib
import multiprocessing

logging.basicConfig ( 
   filename = 'testlog' + datetime.datetime.today().strftime('%Y-%m-%d') + '.log', 
   format = '%(levelname)s: %(message)s'
)

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "olx_site.settings")
django.setup()

from product.models import *
from product.views import *

main_urls = [
    'https://www.olx.ua/detskiy-mir/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/nedvizhimost/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/transport/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/zhivotnye/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/dom-i-sad/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/elektronika/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/uslugi/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/moda-i-stil/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/hobbi-otdyh-i-sport/?search%5Bprivate_business%5D=private',
    'https://www.olx.ua/otdam-darom/?search%5Bfilter_float_price%3Afrom%5D=free&search%5Bprivate_business%5D=private',
    'https://www.olx.ua/obmen-barter/?search%5Bfilter_float_price%3Afrom%5D=exchange&search%5Bprivate_business%5D=private'
]

domain = "olx.ua"

country_code = 'UA'

check_mobile_prefix = ['39', '38','44', '45', '32', '48' ,'50', '63', '66', '67', '68','73', '91', '92', '93', '94', '95', '96', '97', '98', '99']

international_code = '380'

iterator_in_one_cycle = -1

category_index = 0

gear = [0, 1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 100000, 1000000]

total_count = 0

multi_threads = []

multi_instances = []

max_delay_limit = 10

self_scrapy_history = None
self_proxies = None
self_website = None
update_proxy_thread = None
self_iterator_in_one_cycle = 0

def init():
    current_page = 1

def parse_spider():
    global self_website
    global self_proxies
    global self_scrapy_history
    global multi_threads
    global multi_instances
    global update_proxy_thread

    self_website = ClassifiedWebsites.objects.filter(domain=domain).first()        
    self_proxies = get_or_create_proxies_for_website(self_website)        
    
    sleep_time = 7.5
    self_scrapy_history = ScrapingHistory.objects.create(scraper=domain, links_found=0, links_unique=0, numbers_found=0, numbers_unique=0, numbers_non_matched=0, active_proxies=[], sleep_time=sleep_time)
    for i in range(0, 24):
        self_scrapy_history.active_proxies.append(len(self_proxies))

    self_scrapy_history.save()

    update_proxy_thread = MyThread(name='child procs', target=update_active_proxies)
    update_proxy_thread.start()
    create_instances()

    task = []

    for key, url in enumerate(main_urls):
        task.append((url, key, ))

    # pdb.set_trace()
    pool = multiprocessing.Pool(len(main_urls))
    async_results = [pool.apply_async(each_category_scrape, t) for t in task]
    pool.close()
    map(multiprocessing.pool.ApplyResult.wait, async_results)

    # pool.map(each_category_scrape, task)

    # for t in task:
    #     self.multi_threads.append(pool.apply_async(self.each_category_scrape, t))
    
    # for key, url in enumerate(main_urls):
    #     _thread = MyThread(name='category '+str(key+1), target=each_category_scrape, args=[url,key,])
    #     _thread.start()
    #     multi_threads.append(_thread)

    signal.signal(signal.SIGINT, kill_threads)
    signal.pause()


"""
    spider for each category and for the purpose multi-threading.
    @param:
        category_url: category url to be scraped
        category_index: index of category
    @return:
        Null
"""
def each_category_scrape(category_url, category_index):
    global self_website
    global self_proxies
    global self_scrapy_history
    global multi_threads
    global multi_instances

    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    scrapy_cycle_history = None
    try:
        scrapy_cycle_history = ScraypingCycleHistory.objects.filter(category_index=category_index).latest()
        if get_difference_days(scrapy_cycle_history.updated) > 5:
            scrapy_cycle_history = ScraypingCycleHistory.objects.create(scraper=domain, category_index=category_index, current_page=1, first_link='', last_link='', cycle_index=0)
    except:
        scrapy_cycle_history = ScraypingCycleHistory.objects.create(scraper=domain, category_index=category_index, current_page=1, first_link='', last_link='', cycle_index=0)

    current_page = scrapy_cycle_history.current_page

    range_first_value = 1
    gear_index = 1
    total_cycle_array = []
    self_scrapy_history.numbers_non_matched = 0

    try:
        while (range_first_value + gear[gear_index]) < 99000000:
            total_count = 0
            count_proxy_per_cycle = len(self_proxies)
            it_cycle = 0
            content = setup_proxy_check_xpath(category_url, '//*[@id="body-container"]/div[3]/div/div[4]/span[15]//span/text()', category_index)
            max_page_number = int(content[0].xpath('//*[@id="body-container"]/div[3]/div/div[4]/span[15]//span/text()')[0])

            # count the url
            current_url_num = 0 
            
            # count the available mobile number
            current_mobile_num = 0

            # cycle number
            cycle_num = 0


            while current_page <= max_page_number:
                content = setup_proxy_check_xpath(category_url+'&page='+str(current_page), '//table//tr[@class="wrap"]//a[contains(@class, "thumb")]/@href', category_index)
                url_list = content[0].xpath('//table//tr[@class="wrap"]//a[contains(@class, "thumb")]/@href')

                for url in url_list:
                    start = time.clock()
                    if domain not in url:
                        logging.debug("$$$$$$$$$$$$$$$$$ url is not valid $#$$$$$$$$$$$$$$$$$$$$$")
                        continue                

                    self_scrapy_history.links_found += 1
                    if check_url_twice(url):
                        logging.debug("$$$$$$$$$$$$$$ url is twice repeated $$$$$$$$$$$$$$$$$")
                        continue                

                    address = ""
                    phone = ""
                    
                    while address == "":
                        content = setup_proxy_check_xpath(url, '//*[@id="offerdescription"]/div[2]/div[1]/a/strong/text()', category_index, True)
                        try:
                            address = content[0].xpath('//*[@id="offerdescription"]/div[2]/div[1]/a/strong/text()')[0]
                        except:
                            logging.debug("########## address is not available ##########")
                            continue

                        try:
                            phone = content[0].xpath('//*[@id="contact_methods"]/li[2]/div/strong//text()')[0]
                        except:
                            pass

                    

                    if phone is not '':
                        phone = filter_mobile(phone)

                        if not check_phone_number(phone):
                            self_scrapy_history.numbers_non_matched += 1
                            logging.debug("############# Non matched ###############" + str(phone))
                            continue

                        self_scrapy_history.numbers_found += 1
                        current_mobile_num += 1                            
                    else:
                        logging.debug("$$$$$$$$$$$ phone number is not available $$$$$$$$$$$$$$$$$$$$")
                        continue

                    
                    if address is not '':
                        current_url_num += 1
                        scrapy_cycle_history.cycle_index = cycle_num

                        try:
                            total_cycle_array[cycle_num][1] = datetime.datetime.today().strftime('%Y-%m-%d') + '&' + url
                            scrapy_cycle_history.last_link = total_cycle_array[cycle_num][1]
                        except IndexError:
                            total_cycle_array.append(['', ''])
                            total_cycle_array[cycle_num][0] = datetime.datetime.today().strftime('%Y-%m-%d') + '&' + url
                            scrapy_cycle_history.first_link = total_cycle_array[cycle_num][0]

                        scrapy_cycle_history.save()
                        
                        it_cycle += 1

                        if it_cycle == count_proxy_per_cycle - 1:
                            cycle_num += 1
                            it_cycle = 0
                            time.sleep(sleep_time)
                            sleep_time += 1

                        
                        self_scrapy_history.links_unique += 1
                        self_scrapy_history.save()
                        save_data(address, phone)
                        print("######################### time line per url ######################")
                        print time.clock() - start
                        logging.debug("######################### time line per url ######################")
                        logging.debug(str(time.clock() - start))

                        total_count += 1

                current_page += 1
                scrapy_cycle_history.current_page = current_page
                scrapy_cycle_history.save()

            if total_count >= 20000:
                gear_index -= 1
                if gear[gear_index] == 0:
                    logging.debug("$$$$$$$$$$$$$$$$ gear index is finisihed ##$$$$$$$$")
                    break

            if total_count  <= 2000:
                gear_index += 1

            range_first_value = range_first_value + gear[gear_index] + 1

    except Exception as err:
        print(err)
        logging.debug(err)
        time.sleep(60)
        each_category_scrape(category_url, category_index)
        return

    try:
        multi_threads[category_index].stop()
        multi_threads[category_index].join()
    except:
        pass

"""
    Create the headless browser with given proxy list
"""
def create_instances():
    global self_website
    global self_proxies
    global self_scrapy_history
    global multi_instances

    del multi_instances[:]
    for _proxy in self_proxies:
        proxy = _proxy.proxy
        service_args=[]
        service_args.append('--proxy={}:{}'.format(proxy.ip, proxy.port))

        if proxy.username and proxy.password:
            service_args.append('--proxy-auth={}:{}'.format(proxy.username, proxy.password))

        capabilities = DesiredCapabilities.PHANTOMJS
        capabilities['phantomjs.page.settings.resourceTimeout'] = max_delay_limit * 1000

        driver = webdriver.PhantomJS(service_args=service_args,
                                desired_capabilities=capabilities,
                                service_log_path='/tmp/ghostdriver.log')

        driver.set_window_size(1120, 1080)
        driver.set_page_load_timeout(max_delay_limit)

        multi_instances.append(driver)

"""
    - Request with @url on webdriver using phantomJS for headless browser
        
    - confirm with @xpath_string if webpage is full-downloaded

        Loop and request until webpage is full
"""
def setup_proxy_check_xpath(url, xpath_string, category_index, isPhone=False):
    global self_website
    global self_proxies
    global self_scrapy_history
    global multi_threads
    global multi_instances
    global self_iterator_in_one_cycle

    content = None
    while True:
        iterator_in_one_cycle = (self_iterator_in_one_cycle + 1) % len(multi_instances)
        self_iterator_in_one_cycle = iterator_in_one_cycle
        try:
            multi_instances[iterator_in_one_cycle].get(url)
        except httplib.BadStatusLine as bsl:
            print(bsl)
            logging.debug(bsl)
            update_or_remove_proxy(self_proxies[iterator_in_one_cycle])
            continue
        except TimeoutException as e:
            print(e)
            logging.debug(e)
            update_or_remove_proxy(self_proxies[iterator_in_one_cycle])
            continue
        except WebDriverException as e:
            update_or_remove_proxy(self_proxies[iterator_in_one_cycle])
            print(e)
            logging.debug(e)
            continue
        except KeyboardInterrupt as e:
            print(e)
            logging.debug(e)
            update_or_remove_proxy(self_proxies[iterator_in_one_cycle])
            continue            
        except Exception as e:
            update_or_remove_proxy(self_proxies[iterator_in_one_cycle])
            print(str(e))
            logging.debug(e)
            continue   


        content = etree.HTML(multi_instances[iterator_in_one_cycle].page_source.encode('utf8'))
        element = content.xpath(xpath_string)

        if len(element) == 0:
            continue
        
        if isPhone == True:
            try:
                phone_elem = multi_instances[iterator_in_one_cycle].find_element_by_xpath('//*[@id="contact_methods"]/li[2]/div')
                phone_elem.click()
                time.sleep(3)
                content = etree.HTML(multi_instances[iterator_in_one_cycle].page_source.encode('utf8'))
            except:
                pass
            
        break

    return content, iterator_in_one_cycle

"""
    Kill main process and all thread when Control+C or project will be finished
"""
def kill_threads(signal, frame):
    global update_proxy_thread

    os._exit(1)
    # for _thread in self.multi_threads:
    #     _thread.stop()
    #     _thread.join()

    update_proxy_thread.stop()
    update_proxy_thread.join()


"""
    get different days with old date from today
    @param:
        old_date: old date
    @return:
        different days
"""
def get_difference_days(old_date):
    d1 = datetime.datetime.utcfromtimestamp(old_date.created_utc)
    result = datetime.datetime.utcnow() - d1
    return result.days


"""
    validating and fixing phone number
    @param: 
        num: phone number
    @return: validated number
"""
def filter_mobile(num):
    if num == '':
        return 0

    num = num.strip().replace(" ", "")
    num = str(int(filter(str.isdigit, num)))

    if len(num) < 11:
        num = international_code + str(num)

    if num.startswith(international_code) and len(num) == 13:
        num = num.replace('3800', '380')

    return int(num)

"""
    check if given phone number has regular prefix
    @param: 
        phone: phone number
    @return: True or False
"""
def check_phone_number(phone):
    # check if international code 
    if str(phone).startswith(international_code):
        prefix = str(phone)[3:5]
        if prefix in check_mobile_prefix:
            return True

    return False

"""
    Check if url was already scraped
    @param: 
        url: ad full link
    @return:
        True or False
"""
def check_url_twice(url):
    path = url.replace('https://www.olx.ua', '').split('#')
    hashed_path = hashlib.sha256(path).hexdigest()
    count = ScrapedLinks.objects.filter(path__iexact=path).count()

    if count > 0:
        return True

    ScrapedLinks.objects.create(scraper=domain, path=path, hashed_path=str(time.time()))
    return False


"""
    Get valid proxies from Proxies table which are not status "suspended"

    @param: 
        website: scraped domain
    @return:
        valid proxy list
"""
def get_proxies(website):
    country_codes = website.proxy_countries
    country_codes = ast.literal_eval(country_codes)

    alt_proxies = Proxies.objects.filter(country_code__in=country_codes).all()
    
    proxies = []

    for proxy in alt_proxies:
        try:
            if proxy.classifiedwebsitesproxies_set.first().status == 'suspended':
                continue
        except:
            pass

        proxies.append(proxy)

    if len(proxies) == 0:
        print("proxies are unavailable!")
        kill_threads(None, None)

    if len(proxies) > website.max_proxies:
        proxies = proxies[:website.max_proxies]

    return proxies


"""
    Increase suspended_level once proxy is suspended
    Update status, 'suspended' when level is more than 50 ( times )
    At that time, refresh proxy list from table

    @param:
        classified_proxy: proxy which is suspended once.
    @return:
        Null
"""
def update_or_remove_proxy(classified_proxy):
    global self_website
    global self_proxies

    classified_proxy.suspended_level += 1
    classified_proxy.save()
    if classified_proxy.suspended_level >= 50:
        classified_proxy.status = 'suspended'
        classified_proxy.save()
        self_proxies = get_or_create_proxies_for_website(self_website)
        create_instances()

"""
    Insert proxy to classified_website_proxies table

    return proxy list for scraped domain

    @param: 
        website: scrap domain
    @return:
        valid proxy list
"""
def get_or_create_proxies_for_website(website):
    proxies = get_proxies(website)
    for proxy in proxies:
        try:
            if ClassifiedWebsitesProxies.objects.filter(classified=website, proxy=proxy, status='online').count() > 0:
                continue
            
            ClassifiedWebsitesProxies.objects.create(classified=website, proxy=proxy, suspended_level=0, status='online')
        except Exception as ex:
            print(ex)
            logging.debug(ex)

    return ClassifiedWebsitesProxies.objects.filter(classified=website, status='online').all()

"""
    Update active proxies with new proxies or original proxy per hour
"""
def _update_active_proxies():
    global self_website
    global self_scrapy_history

    proxies = get_or_create_proxies_for_website(self_website)
    del self_scrapy_history.active_proxies[0]
    self_scrapy_history.active_proxies.append(len(proxies))
    self_scrapy_history.save()

"""
    update active proxies per hour after checking online proxies from table.
"""
def update_active_proxies():
    schedule.every().hour.do(_update_active_proxies)
    while True:
        schedule.run_pending()
        time.sleep(1)        

"""
    Save address and phone and check result OUTPUT
    @param:
        address: scraped address
    @return:
        Null
"""
def save_data(address, phone):
    city_name = ''
    area_name = ''
    district_name = ''

    if len(address.split(',')) > 0:
        area_name = address.split(',')[0].strip()
    if len(address.split(',')) > 1:
        city_name = address.split(',')[1].strip()
    if len(address.split(',')) > 2:
        district_name = address.split(',')[2].strip()


    city = Cities.objects.filter(display_name__iexact=city_name).first()
    area = Areas.objects.filter(display_name__iexact=area_name).first()
    district = Districts.objects.filter(display_name__iexact=district_name).first()

    if not area:
        number_save_and_log(phone, None, None, None, city_name, area_name, district_name, '111')
    elif not city:
        number_save_and_log(phone, city.id, None, None, city_name, area_name, district_name, '011')
    elif not district:
        number_save_and_log(phone, city.id, area.id, None, city_name, area_name, district_name, '001')
    else:
        number_save_and_log(phone, city.id, area.id, district.id, city_name, area_name, district_name, '000')

    if not city and area and district:
        logging.debug('############  country, city, area, district LOG ####################')
        logging.debug('country:'+str(country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + ' 100') 

    if city and not area and district:
        logging.debug('############  country, city, area, district LOG ####################')
        logging.debug('country:'+str(country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + ' 010')

    if city and area and not district:
        logging.debug('############  country, city, area, district LOG ####################')
        logging.debug('country:'+str(country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + ' 110')


"""
    Save valid row to mobbile_numbers database and Log
    @param:
        city_id: id of cities table for current address
        area_id: id of areas table for current address
        district_id: id of districts table for current address
        city_name: city name of current address
        area_name: area name of current address
        district_name: district name of current address
        result: OUTPUT

    @return:
        Null
"""
def number_save_and_log(phone, city_id, area_id, district_id, city_name, area_name, district_name, result):
    global self_scrapy_history

    try:
        MobileNumbers.objects.create(country_code=country_code, city_id=city_id, area_id=area_id, district_id=district_id, number=int(phone), postal_code_id=0)
        self_scrapy_history.numbers_unique += 1
    except Exception as e:
        # self_scrapy_history.numbers_non_matched += 1
        print(e)
        logging.debug(e)

    self_scrapy_history.save()
    logging.debug('############  country, city, area, district LOG ####################')
    logging.debug('country:'+str(country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + result)


class OlxSpider(scrapy.Spider):
    name = "olx-2"

    def start_requests(self):
        yield scrapy.Request('https://google.com',callback=self.parse)

    def parse(self, reseponse):
        parse_spider()