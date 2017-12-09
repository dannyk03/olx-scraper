import os
import re
import csv
import datetime
import mimetypes
import scrapy
import subprocess

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from .models import *