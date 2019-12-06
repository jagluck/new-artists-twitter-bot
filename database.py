# import packages we need
import requests as requests
import json
from datetime import datetime, timedelta, date
from pytz import timezone
import pandas as pd
import tweepy
import os
import psycopg2
from psycopg2 import extras
from songkick import * 

# # to run on heroku
# from bot import *
# # Consumer keys and access tokens, used for OAuth
# songkick_api_key = os.environ['songkick_api_key']
# tw_consumer_key = os.environ["tw_consumer_key"]
# tw_consumer_secret = os.environ["tw_consumer_secret"]
# tw_access_token = os.environ["tw_access_token"]
# tw_access_token_secret = os.environ["tw_access_token_secret"]
# database_url = os.environ['HEROKU_POSTGRESQL_IVORY_URL']
# heroku_app_name =  os.environ['heroku_app_name']
# table_name =  os.environ['table_name']

# to run locally
keys={}
with open(os.path.abspath("keys.json"),"r") as f:
    keys = json.loads(f.read())
songkick_api_key = keys['songkick_api_key']
tw_consumer_key = keys["tw_consumer_key"]
tw_consumer_secret = keys["tw_consumer_secret"]
tw_access_token = keys["tw_access_token"]
tw_access_token_secret = keys["tw_access_token_secret"]
database_url = keys['HEROKU_POSTGRESQL_IVORY_URL']
heroku_app_name =  keys['heroku_app_name']
table_name =  keys['table_name']


def createTable():
    create_table = "CREATE TABLE " + table_name + " (\
    artistId int,\
    artistName varchar(255),\
    concertTime varchar(255),\
    content varchar(1000),\
    eventDate varchar(255),\
    billingIndex int,\
    tweeted int\
    );"
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute(create_table)
    conn.commit() # <--- makes sure the change is shown in the database
    conn.close()
    cursor.close()
    
def dropTable():

    create_table = "DROP TABLE " + table_name + ";"
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute(create_table)
    conn.commit() # <--- makes sure the change is shown in the database
    conn.close()
    cursor.close()
    
def clearTable():
    clear_table = "DELETE FROM " + table_name + ";"
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute(clear_table)
    conn.commit() # <--- makes sure the change is shown in the database
    conn.close()
    cursor.close()

def readTable():
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM " + table_name) # <--- makes sure the change is shown in the database
    conn.commit()
    toTweet = cursor.fetchall()
    conn.close()
    cursor.close()
    
    
    # our timezone
    eastern = timezone('US/Eastern')
    toTweet = pd.DataFrame(toTweet,columns=["artistId","artistName","concertTime","content","eventDate","billingIndex","tweeted"])
    toTweet['concertTime'] = toTweet['concertTime'].apply(lambda x: datetime.strptime(x,"%Y-%m-%d %H:%M:%S+00"))
    toTweet['concertTime'] = toTweet['concertTime'].apply(lambda x: x - timedelta(hours=(5)) + timedelta(minutes=(4)))
    toTweet['concertTime'] = toTweet['concertTime'].apply(lambda x: x.replace(tzinfo=eastern))
    toTweet = toTweet.sort_values(by=['concertTime'], ascending=True)
    return toTweet

def writeTable(toTweet):
    toTweet = toTweet.sort_values(by=['concertTime'], ascending=True)
    if len(toTweet) > 0:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        df_columns = list(toTweet)
        columns = ",".join(df_columns)
        values = "VALUES({})".format(",".join(["%s" for _ in df_columns])) 
        insert_stmt = "INSERT INTO {} ({}) {}".format(table_name,columns,values)

        cur = conn.cursor()
        psycopg2.extras.execute_batch(cur, insert_stmt, toTweet.values)
        conn.commit()
        cur.close()
        conn.close()
