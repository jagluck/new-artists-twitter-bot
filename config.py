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
from apscheduler.schedulers.blocking import BlockingScheduler

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

venue_name_dict = {
    "9:30 Club" : "@930Club",
    "Songbyrd Music House" : "@SongbyrdDC",
    "Songbyrd Vinyl Lounge" : "@SongbyrdDC",
    "Songbyrd - Upstairs" : "@SongbyrdDC",
    "Atlas Brew Works" : "@AtlasBrewWorks",
    "Echostage" : "@echostage",
    "U Street Music Hall" : "@uhalldc",
    "Black Cat" : "@BlackCatDC",
    "Sixth & I" : "@SixthandI",
    "Velvet Lounge" : "@VelvetLoungeDC",
    "Flash" : "@FlashClubDC",
    "Slash Run" : "@slashrundc",
    "DC9 Nightclub" : "@dc9club",
    "The Wine Garden, City Winery DC" : "@CityWineryDC",
    "City Winery" : "@CityWineryDC",
    "Rock & Roll Hotel" : "@rocknrollhotel",
    "7DrumCity" : "@7DrumCity",
    "7 Drum City" : "@7DrumCity",
    "Union Stage" : "@unionstage",
    "Hirshhorn Museum and Sculpture Garden" : "@hirshhorn",
    "Pie Shop" : "@pieshopdc",
    "Twins Jazz" : "@twinsjazzclub",
    "The Anthem" : "@TheAnthemDC",
    "Sofar D.C." : "@sofardc",
    "Kreeger Museum of Art" : "@KreegerMuseum",
    "Dive" : "@DIVEBarDC",
    "Renaissance Downtown Hotel" : '@RenDC_Downtown',
    "The Hamilton Live" : '@thehamiltondc',
    "Comet Ping Pong" : '@cometpingpong',
    "Vinyl Lounge, Gypsy Sally's" : '@GypsySallys',
    "Gypsy Sally's" : '@GypsySallys',
    "The Miracle Theatre" : '@TheMiracleDC',
    "Dock5 @ Union Market" : '@UnionMarketDC',
    "Union Market" : '@UnionMarketDC',
    "Howard Theatre" : '@HowardTheatre'
}

from database import *
from songkick import *
from bot import *

