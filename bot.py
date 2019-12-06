# import packages we need
import requests as requests
import json
from datetime import datetime, timedelta, date
from pytz import timezone
import pandas as pd
import tweepy
import os
from database import *
from songkick import *

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


# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(tw_consumer_key, tw_consumer_secret)
auth.set_access_token(tw_access_token, tw_access_token_secret)
 
# Creation of the actual interface, using authentication
api = tweepy.API(auth)

# our timezone
eastern = timezone('US/Eastern')

# this sends a tweet :)
def sendTweet(content):
    api.update_status(content)
    
# this runs every hour, it sends the first tweet that is qualified if there is one
def sendNextTweet(toTweet):
    if (len(toTweet) != 0):
        # maybe add a check now or somekind of resorting logic to make sure show has not already happened
        
        timeNow = datetime.now(eastern)
        
        didWeTweet = False
        
        for index,row in toTweet.iterrows():
            # did we not already tweet something this hour and did it not already happen and did we not already tweet it?
            if ((didWeTweet == False) and (row['concertTime'] > timeNow) and (row['tweeted'] == 0)):
                didWeTweet = True
                thisTweet = row['content']
                print(thisTweet)
                sendTweet(thisTweet)
                toTweet.loc[index,'tweeted'] = 1
    else:
        print("nothing to send")
        
    return toTweet


    


# this runs once a day, it finds new artists in the area
def runBot(days, cityName, cityId, artistsWhoPlayedInDC):
        
    upcomingShows = getUpcomingShows(days,cityId)
    upcomingShows = upcomingShows[upcomingShows["locationCity"] == cityName]
    upcomingShows.drop_duplicates(subset ="artistId", inplace = True) 
    
    contents = []
    artistIds = []
    artistNames = []
    artistNames = []
    concertTimes = []
    eventDates = []
    artistUrls = []
    billingIndexes = []
    tweetedes = []
                    
    for index, row in upcomingShows.iterrows():
        artistId = row['artistId']
        eventDate = row['eventDate']
        concertTime = row['concertTime']
        venueName = row['venueName']
        eventUrl = row['eventUrl']
        artistName = row['artistName']
        billingIndex = row['billingIndex']
        if artistId not in artistsWhoPlayedInDC:
            if not wasArtistInCity(cityName, artistId):
                
                # make the tweet string
                dateString = datetime.strptime(eventDate, "%Y-%m-%d").strftime("%B") + " " + ordinal(datetime.strptime(eventDate, "%Y-%m-%d").day)
                content = (str(artistName) + " is playing their first show in DC!")
                if (billingIndex == 1):
                    content = content + " They are headlining at " + venueName + " on " + dateString + " " + eventUrl
                else:
                    content = content + " They are opening at " + venueName + " on " + dateString + " " + eventUrl   
                    
                # fix times that are null with noon of the day of cencert so it goes first
                if (concertTime == None):
                    concertTime = datetime.strptime(eventDate,"%Y-%m-%d")
                    concertTime = concertTime.replace(tzinfo=eastern)
                    concertTime = concertTime + timedelta(hours=(12))
                else:
                    concertTime = datetime.strptime(concertTime,"%Y-%m-%dT%H:%M:%S%z")
                    concertTime = concertTime.replace(tzinfo=eastern)
                
                # add one second per billing index
                concertTime = concertTime - timedelta(seconds=(billingIndex - 1))
                
                # add values to lists to make dataframe later
                artistIds.append(artistId)
                artistNames.append(artistName)
                contents.append(content)
                concertTimes.append(concertTime)
                eventDates.append(eventDate)
                billingIndexes.append(billingIndex)
                tweetedes.append(0)
            
    toTweetNew = pd.DataFrame(
            {
                "artistId" : artistIds,
                "artistName" : artistNames,
                "concertTime" : concertTimes,
                "content" : contents,
                "eventDate" : eventDates,
                "billingIndex" : billingIndexes,
                "tweeted" : tweetedes
            })
    return toTweetNew

def onceADay():
    toTweet = readTable()
    artistsWhoPlayedInDC = toTweet['artistId']
    cityName = "Washington, DC, US"
    cityId = "1409"
    days = 1
    toTweetNew  = runBot(days,cityName,cityId,artistsWhoPlayedInDC)

    # make sure we don't already have a artist
    toTweetNew = toTweetNew[~toTweetNew['artistId'].isin(artistsWhoPlayedInDC)]
    # combine results
    toTweet = pd.concat([toTweet, toTweetNew], ignore_index=True)
    # remove shows that are very old
    twoWeeksAgo = datetime.now(eastern) - timedelta(weeks=(2))
    toTweet = toTweetNew[toTweetNew['concertTime'] > twoWeeksAgo]

    # sort by time
    toTweet = toTweet.sort_values(by=['concertTime'], ascending=True)

    # clear
    clearTable()
    
    # upload
    writeTable(toTweet)
    print("got artists")
    
def everyHour():
    toTweet = readTable()
    print("Start sending new tweet now")
    toTweet = sendNextTweet(toTweet)
    clearTable()
    writeTable(toTweet)
    