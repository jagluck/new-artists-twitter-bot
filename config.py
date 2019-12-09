# import packages we need
import requests as requests
import json
from datetime import datetime, timedelta, date
from pytz import timezone
import pandas as pd
import tweepy
import os
import re
import math
import psycopg2
from psycopg2 import extras

# to run on heroku
# Consumer keys and access tokens, used for OAuth
songkick_api_key = os.environ['songkick_api_key']
tw_consumer_key = os.environ["tw_consumer_key"]
tw_consumer_secret = os.environ["tw_consumer_secret"]
tw_access_token = os.environ["tw_access_token"]
tw_access_token_secret = os.environ["tw_access_token_secret"]
database_url = os.environ['HEROKU_POSTGRESQL_IVORY_URL']
heroku_app_name =  os.environ['heroku_app_name']
table_name =  os.environ['table_name']

# # to run locally
# keys={}
# with open(os.path.abspath("keys.json"),"r") as f:
#     keys = json.loads(f.read())
# songkick_api_key = keys['songkick_api_key']
# tw_consumer_key = keys["tw_consumer_key"]
# tw_consumer_secret = keys["tw_consumer_secret"]
# tw_access_token = keys["tw_access_token"]
# tw_access_token_secret = keys["tw_access_token_secret"]
# database_url = keys['HEROKU_POSTGRESQL_IVORY_URL']
# heroku_app_name =  keys['heroku_app_name']
# table_name =  keys['table_name']

from database import *
from songkick import *
from bot import *