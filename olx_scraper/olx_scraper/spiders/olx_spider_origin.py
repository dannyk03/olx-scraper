# -*- coding: utf-8 -*-
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
import logging
import ast
import base64
import httplib
import schedule
import threading
from .my_thread import MyThread
import signal

sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "olx_site.settings")
django.setup()

from product.models import *
from product.views import *

class OlxSpider(scrapy.Spider):
    name = "olx-origin"

    url = [
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

    total_cycle_array = []
    
    country_code = 'UA'

    check_mobile_prefix = ['39', '38', '50', '63', '66', '67', '68', '91', '92', '93', '94', '95', '96', '97', '98', '99']

    international_code = '380'

    iterator_in_one_cycle = -1

    category_index = 0

    gear = [0, 1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 100000, 1000000]

    total_count = 0

    def __init__(self):

        logfile = open('testlog' + datetime.datetime.today().strftime('%Y-%m-%d') + '.log' , 'w')        
        configure_logging(install_root_handler = False) 
        logging.basicConfig ( 
           filename = logfile, 
           format = '%(levelname)s: %(your_message)s', 
           level = logging.INFO 
        )
        self.current_page = 1

    def start_requests(self):
        yield scrapy.Request('https://google.com',callback=self.parse)

    def parse(self, response):
        """
            Main scraping module
        """
        self.website = ClassifiedWebsites.objects.filter(domain=self.domain).first()        
        self.proxies = self.get_or_create_proxies_for_website(self.website)        
        self.sleep_time = 7.5;
        self.scrapy_history = ScrapingHistory.objects.create(scraper=self.domain, links_found=0, links_unique=0, numbers_found=0, numbers_unique=0, numbers_non_matched=0, active_proxies=[], sleep_time=self.sleep_time)
        for i in range(0, len(self.proxies)):
            self.scrapy_history.active_proxies.append(len(self.proxies))
        self.scrapy_history.save()
        
        update_proxy_thread = MyThread(name='child procs', target=self.update_active_proxies)
        update_proxy_thread.start()

        self.scrapy_cycle_history = None
        try:
            self.scrapy_cycle_history = ScraypingCycleHistory.objects.latest()
            if self.get_difference_days(self.scrapy_cycle_history.updated) > 5:
                self.scrapy_cycle_history = ScraypingCycleHistory.objects.create(scraper=self.domain, category_index=0, current_page=1, first_link='', last_link='', cycle_index=0)
        except:
            self.scrapy_cycle_history = ScraypingCycleHistory.objects.create(scraper=self.domain, category_index=0, current_page=1, first_link='', last_link='', cycle_index=0)

        self.category_index = self.scrapy_cycle_history.category_index
        self.current_page = self.scrapy_cycle_history.current_page

        while self.category_index < len(self.url):
            self.range_first_value = 1
            gear_index = 1

            while (self.range_first_value + self.gear[gear_index]) < 99000000:
                self.total_count = 0
                try:                    
                    count_proxy_per_cycle = len(self.proxies)

                    self.setup_proxy_check_xpath(self.url[self.category_index], '//*[@id="body-container"]/div[3]/div/div[4]/span[15]//span/text()')
                    content = etree.HTML(self.driver.page_source.encode('utf8'))
                    max_page_number = int(content.xpath('//*[@id="body-container"]/div[3]/div/div[4]/span[15]//span/text()')[0])

                    # count the url
                    current_url_num = 0 
                    
                    # count the available mobile number
                    current_mobile_num = 0

                    # cycle number
                    cycle_num = 0


                    while self.current_page <= max_page_number:
                        print(self.url[1]+'&page='+str(self.current_page))

                        self.setup_proxy_check_xpath(self.url[1]+'&page='+str(self.current_page), '//table//tr[@class="wrap"]//a[contains(@class, "thumb")]/@href')
                        content = etree.HTML(self.driver.page_source.encode('utf8'))
                        url_list = content.xpath('//table//tr[@class="wrap"]//a[contains(@class, "thumb")]/@href')

                        for url in url_list:
                            if self.domain not in url:
                                continue                
                            if self.check_url_twice(url):
                                continue                

                            address = ""
                            phone = ""
                            
                            while address == "":
                                self.setup_proxy_check_xpath(url, '//*[@id="offerdescription"]/div[2]/div[1]/a/strong/text()')

                                try:
                                    phone_elem = self.driver.find_element_by_xpath('//*[@id="contact_methods"]/li[2]/div')
                                    phone_elem.click()
                                except:
                                    break

                                time.sleep(3)
                                main_cont = etree.HTML(self.driver.page_source.encode('utf8'))
                                try:
                                    address = main_cont.xpath('//*[@id="offerdescription"]/div[2]/div[1]/a/strong/text()')[0]
                                except:
                                    print("+++++++++++++++++ address empty +++++++++++++++")
                                    continue

                                try:
                                    phone = main_cont.xpath('//*[@id="contact_methods"]/li[2]/div/strong//text()')[0]
                                except:
                                    print("++++++++++++++++++ phone empty ++++++++++++++")

                            ########## end while
                            self.scrapy_history.links_found += 1

                            if phone is not '':
                                phone = self.filter_mobile(phone)
                                self.scrapy_history.numbers_found += 1

                                if not self.check_phone_number(phone):
                                    self.scrapy_history.numbers_non_matched += 1
                                    continue

                                current_mobile_num += 1
                                
                                ##? self.scrapy_history.numbers_unique
                            else:
                                continue

                            if address is not '':
                                current_url_num += 1
                                self.scrapy_cycle_history.cycle_index = cycle_num

                                try:
                                    self.total_cycle_array[cycle_num][1] = datetime.datetime.today().strftime('%Y-%m-%d') + '&' + url
                                    self.scrapy_cycle_history.last_link = self.total_cycle_array[cycle_num][1]
                                except IndexError:
                                    self.total_cycle_array.append(['', ''])
                                    self.total_cycle_array[cycle_num][0] = datetime.datetime.today().strftime('%Y-%m-%d') + '&' + url
                                    self.scrapy_cycle_history.first_link = self.total_cycle_array[cycle_num][0]

                                self.scrapy_cycle_history.save()
                                    
                                it_cycle = self.iterator_in_one_cycle % count_proxy_per_cycle

                                if it_cycle == count_proxy_per_cycle - 1:
                                    """
                                        Optimize the sleep time
                                    """
                                    cycle_num += 1
                                    time.sleep(self.sleep_time)

                                
                                self.scrapy_history.links_unique += 1
                                ##? self.scrapy_history.links_unique                    

                                self.scrapy_history.save()
                                self.save_data(address, phone)

                                self.total_count += 1

                                # print('======================================')
                                # print(address)
                                # print(phone)
                                # print(url)
                                # print(current_url_num)
                                # print('=========================================')

                        self.current_page += 1
                        self.scrapy_cycle_history.current_page = self.current_page
                        self.scrapy_cycle_history.save()

                    self.driver.quit()

                    if self.total_count >= 20000:
                        gear_index -= 1
                        if self.gear[gear_index] == 0:
                            print('{} category has max count {}'.format(self.category_index, self.total_count))
                            break


                    if self.total_count  <= 2000:
                        gear_index += 1

                    self.range_first_value = self.range_first_value + self.gear[gear_index] + 1

                except Exception as err:
                    print(err)
                    time.sleep(60)
                    yield scrapy.Request('https://google.com',callback=self.parse, errback=self.parse, dont_filter=True)

            self.category_index += 1
            self.scrapy_cycle_history.category_index = self.category_index
            self.scrapy_cycle_history.save()

        update_proxy_thread.stop()
        update_proxy_thread.join()

        signal.signal(signal.SIGINT, self.kill_threads)
        signal.pause()

    def setup_proxy_check_xpath(self, url, xpath_string):
        """
            - Request with @url on webdriver using phantomJS for headless browser
                
            - confirm with @xpath_string if webpage is full-downloaded

                Loop and request until webpage is full
        """
        while True:
            self.iterator_in_one_cycle = (self.iterator_in_one_cycle + 1) % len(self.proxies)
            proxy = self.proxies[self.iterator_in_one_cycle].proxy
            service_args=[]
            # service_args=['--ignore-ssl-errors=true',
            #                '--ssl-protocol=any',
            #                '--load-images=false']

            # service_args.append('--proxy={}:{}'.format(proxy['ip'], proxy['port']))
            service_args.append('--proxy={}:{}'.format(proxy.ip, proxy.port))
            # service_args.append('--web-security=no')
            # service_args.append('--proxy-type=http')

            if proxy.username and proxy.password:
                service_args.append('--proxy-auth={}:{}'.format(proxy.username, proxy.password))

            print("################ proxy #########################")
            print('Proxy {}:{}'.format(proxy.ip, proxy.port))
            # print('Proxy {}:{}'.format(proxy['ip'], proxy['port']))
            print("################ proxy #########################")

            capabilities = DesiredCapabilities.PHANTOMJS
            # capabilities["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36")
            capabilities['phantomjs.page.settings.resourceTimeout'] = 50000

            # self.driver = webdriver.PhantomJS(service_args=service_args)
            self.driver = webdriver.PhantomJS(service_args=service_args,
                                    desired_capabilities=capabilities,
                                    service_log_path='/tmp/ghostdriver.log')

            self.driver.set_window_size(1120, 1080)
            # self.driver.implicitly_wait(2)
            self.driver.set_page_load_timeout(50)

            try:
                self.driver.get(url)
            except httplib.BadStatusLine as bsl:
                print(bsl)
                self.update_or_remove_proxy(self.proxies[self.iterator_in_one_cycle])
                continue
            except TimeoutException as e:
                print(e)
                self.update_or_remove_proxy(self.proxies[self.iterator_in_one_cycle])
                continue
            except Exception as e:
                print(str(e))
                continue   
            except WebDriverException as e:
                print(e)
                continue
            except KeyboardInterrupt as e:
                print(e)
                self.update_or_remove_proxy(self.proxies[self.iterator_in_one_cycle])
                continue
            except Exception as e:
                print(e)
                continue


            content = etree.HTML(self.driver.page_source.encode('utf8'))
            element = content.xpath(xpath_string)

            if len(element) == 0:
                continue

            break

    def kill_threads(self, signal, frame):
        os._exit(1)

    def get_difference_days(self, old_date):
        """
            get different days with old date from today
            @param:
                old_date: old date
            @return:
                different days
        """
        d1 = datetime.datetime.utcfromtimestamp(old_date.created_utc)
        result = datetime.datetime.utcnow() - d1
        return result.days

    def filter_mobile(self, num):
        """
            validating and fixing phone number
            @param: 
                num: phone number
            @return: validated number
        """
        if num == '':
            return 0

        num = num.strip().replace(" ", "")
        num = str(int(filter(str.isdigit, num)))

        if len(num) < 11:
            num = self.international_code + str(num)

        if num.startswith(self.international_code) and len(num) == 13:
            num = num.replace('3800', '380')

        return int(num)

    def check_phone_number(self, phone):
        """
            check if given phone number has regular prefix
            @param: 
                phone: phone number
            @return: True or False
        """
        # check if international code 
        if str(phone).startswith(self.international_code):
            prefix = str(phone)[3:5]
            if prefix in self.check_mobile_prefix:
                return True

        return False

    def check_url_twice(self, url):
        """
            Check if url was already scraped
            @param: 
                url: ad full link
            @return:
                True or False
        """
        path = url.replace('https://www.olx.ua', '').split('#')[0]
        hashed_path = path
        count = ScrapedLinks.objects.filter(hashed_path__iexact=hashed_path).count()

        if count > 0:
            return True

        ScrapedLinks.objects.create(scraper=self.domain, path=path, hashed_path=hashed_path)
        return False

    def get_proxies(self, website):
        """
            Get valid proxies from Proxies table which are not status "suspended"

            @param: 
                website: scraped domain
            @return:
                valid proxy list
        """
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

        if len(proxies) > website.max_proxies:
            proxies = proxies[:website.max_proxies]

        return proxies

    def update_or_remove_proxy(self, classified_proxy):
        """
            Increase suspended_level once proxy is suspended
            Update status, 'suspended' when level is more than 50 ( times )
            At that time, refresh proxy list from table

            @param:
                classified_proxy: proxy which is suspended once.
            @return:
                Null
        """
        classified_proxy.suspended_level += 1
        classified_proxy.save()
        if classified_proxy.suspended_level >= 50:
            classified_proxy.status = 'suspended'
            classified_proxy.save()

            self.proxies = self.get_or_create_proxies_for_website(self.website)

    def get_or_create_proxies_for_website(self, website):
        """
            Insert proxy to classified_website_proxies table

            return proxy list for scraped domain

            @param: 
                website: scrap domain
            @return:
                valid proxy list
        """
        proxies = self.get_proxies(website)
        for proxy in proxies:
            try:
                if ClassifiedWebsitesProxies.objects.filter(classified=website, proxy=proxy, status='online').count() > 0:
                    continue
                
                ClassifiedWebsitesProxies.objects.create(classified=website, proxy=proxy, suspended_level=0, status='online')
            except Exception as ex:
                print(ex);

        return ClassifiedWebsitesProxies.objects.filter(classified=website, status='online').all()

    def _update_active_proxies(self):
        proxies = self.get_or_create_proxies_for_website(self.website)
        del self.scrapy_history.active_proxies[0]
        self.scrapy_history.active_proxies.append(len(proxies))

    def update_active_proxies(self):
        """
            update active proxies per hour after checking online proxies from table.
        """
        schedule.every().hour.do(self._update_active_proxies)
        while True:
            schedule.run_pending()
            time.sleep(1)        

    def save_data(self, address, phone):
        """
            Save address and phone and check result OUTPUT
            @param:
                address: scraped address
            @return:
                Null
        """
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

        print("city=====================================================")
        print(city)
        print("area=====================================================")
        print(area)
        print("district=====================================================")
        print(district)

        if not area:
            self.number_save_and_log(phone, None, None, None, city_name, area_name, district_name, '111')
        elif not city:
            self.number_save_and_log(phone, city.id, None, None, city_name, area_name, district_name, '011')
        elif not district:
            self.number_save_and_log(phone, city.id, area.id, None, city_name, area_name, district_name, '001')
        else:
            self.number_save_and_log(phone, city.id, area.id, district.id, city_name, area_name, district_name, '000')

        if not city and area and district:
            logging.debug('############  country, city, area, district LOG ####################')
            logging.debug('country:'+str(self.country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + ' 100') 

        if city and not area and district:
            logging.debug('############  country, city, area, district LOG ####################')
            logging.debug('country:'+str(self.country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + ' 010')

        if city and area and not district:
            logging.debug('############  country, city, area, district LOG ####################')
            logging.debug('country:'+str(self.country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + ' 110')

    def number_save_and_log(self, phone, city_id, area_id, district_id, city_name, area_name, district_name, result):
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
        try:
            MobileNumbers.objects.create(country_code=self.country_code, city_id=city_id, area_id=area_id, district_id=district_id, number=int(phone), postal_code_id=0)
            self.scrapy_history.numbers_unique += 1
            self.scrapy_history.save()

        except Exception as e:
            print(e)

        logging.info('country:'+str(self.country_code) + ' city:' + str(city_name.encode('utf8')) + ' area:' + str(area_name.encode('utf8')) + ' district:' + str(district_name.encode('utf8')) + ' number:' + str(phone) + ' result' + result)        
