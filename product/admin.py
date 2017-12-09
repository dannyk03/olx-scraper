from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render
from django import forms
from django.contrib import messages

from .models import *
from .views import *

admin.site.register(Areas)
admin.site.register(Cities)
admin.site.register(ClassifiedWebsites)
admin.site.register(ClassifiedWebsitesProxies)
admin.site.register(Districts)
admin.site.register(MobileNumbers)
admin.site.register(Proxies)
admin.site.register(ScrapedLinks)
admin.site.register(ScraperMainLinks)
admin.site.register(ScrapingHistory)