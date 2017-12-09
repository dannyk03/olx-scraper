import os
import sys
import django
import subprocess

from datetime import datetime
from os import sys, path
import pdb
import schedule
import time


# load settings
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "olx_site.settings")
django.setup()


def run_scraper():
    path = 'olx_scraper/celery_crawler.py'
    subprocess.Popen(["python", path])

schedule.every().week.do(run_scraper)

def main():
    run_scraper()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()