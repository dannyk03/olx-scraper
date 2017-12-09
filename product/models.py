from __future__ import unicode_literals

import os
import subprocess

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Areas(models.Model):
    city_id = models.IntegerField()
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'areas'
        unique_together = (('city_id', 'name'),)

class Cities(models.Model):
    country_code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cities'
        unique_together = (('country_code', 'name'),)


class ClassifiedWebsites(models.Model):
    domain = models.CharField(max_length=255)
    proxy_countries = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    max_proxies = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'classified_websites'


class ClassifiedWebsitesProxies(models.Model):
    id = models.IntegerField(primary_key=True)
    classified = models.ForeignKey(ClassifiedWebsites, models.DO_NOTHING)
    proxy = models.ForeignKey('Proxies', models.DO_NOTHING)
    suspended_level = models.IntegerField()
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'classified_websites_proxies'
        unique_together = (('classified', 'proxy'),)


class Districts(models.Model):
    area_id = models.IntegerField()
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'districts'
        unique_together = (('area_id', 'name'),)


class MobileNumbers(models.Model):
    country_code = models.CharField(max_length=2)
    city_id = models.IntegerField(blank=True, null=True)
    area_id = models.IntegerField(blank=True, null=True)
    district_id = models.IntegerField(blank=True, null=True)
    postal_code_id = models.IntegerField()
    number = models.BigIntegerField(unique=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mobile_numbers'

class Proxies(models.Model):
    country_code = models.CharField(max_length=2)
    provider = models.CharField(max_length=255)
    ip = models.CharField(max_length=45)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proxies'

class ScrapedLinks(models.Model):
    scraper = models.CharField(max_length=255)
    path = models.CharField(max_length=1000)
    hashed_path = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scraped_links'
        unique_together = (('scraper', 'hashed_path'),)


class ScraperMainLinks(models.Model):
    scraper = models.CharField(max_length=255)
    path = models.CharField(max_length=1000)
    query = models.CharField(max_length=1000, blank=True, null=True)
    hashed_url = models.CharField(unique=True, max_length=32)
    options = models.TextField(blank=True, null=True)
    last_scraped_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scraper_main_links'


class ScrapingHistory(models.Model):
    run_id = models.AutoField(primary_key=True)
    scraper = models.CharField(max_length=255)
    links_found = models.IntegerField()
    links_unique = models.IntegerField()
    numbers_found = models.IntegerField()
    numbers_unique = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    numbers_non_matched = models.IntegerField()
    active_proxies = models.TextField(blank=True, null=True)
    sleep_time = models.DecimalField(max_digits=16, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scraping_history'

class ScraypingCycleHistory(models.Model):
    scraper = models.CharField(max_length=255)
    category_index = models.IntegerField()
    cycle_index = models.IntegerField()
    first_link = models.CharField(max_length=255)
    last_link = models.CharField(max_length=255)
    current_page = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.scraper

    class Meta:
        get_latest_by = 'updated'
