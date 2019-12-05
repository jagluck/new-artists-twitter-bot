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
    
# this gets one page of an artists history, up to 50 shows
def getArtistHistoryPage(artistId,page):
    
    url = "https://api.songkick.com/api/3.0/artists/" + str(artistId) + "/gigography.json"
    params = {'apikey': songkick_api_key, "page" : page, "per_page" : 50}
    resp = requests.get(url, params=params) 
    return json.loads(resp.text)

# this searches an artists full history and returns 
# true or false if they have ever played a show in dc
def wasArtistInCity(city, artistId):
    
    page = 1
    resp = getArtistHistoryPage(artistId, page)
    results = resp["resultsPage"]["results"]
    while (results != {}):
        events = results["event"]
        for event in events:
            if (city == event['location']['city']):
                return True

        page = page + 1
        resp = getArtistHistoryPage(artistId, page)
        results = resp["resultsPage"]["results"]
    
    return False

# this gets one page of the upcoming shows in DC, up to 50 shows
def getUpcomingShowsPage(metroId, minDate, maxDate, page):
    
    url = "https://api.songkick.com/api/3.0/metro_areas/" + metroId + "/calendar.json"
    params = {'apikey': songkick_api_key, "min_date" : minDate, "max_date" : maxDate, "page" : page, "per_page" : 50}
    resp = requests.get(url, params=params) 
    return json.loads(resp.text)

# this gets all of the upcoming shows in DC
def getUpcomingShows(daysAhead, metroId):
   
    artistIds = []
    artistNames = []
    artistUrls = []
    billings = []
    billingIndexes = []
    eventIds = []
    eventTypes = []
    eventUrls = []
    eventDates = []
    venueIds = []
    venueNames = []
    locationCities = []
    concertTimes = []
    
    page = 1
    minDate = str(date.today())
    maxDate = str(date.today() + timedelta(daysAhead))
    resp = getUpcomingShowsPage(metroId, minDate,maxDate, page)
    results = resp["resultsPage"]["results"]
    
    while (results != {}):
        events = results["event"]
    
        for event in events:
            for performance in event["performance"]:
                artist = performance["artist"]
                if ("PRIVATE EVENT" not in artist["displayName"]):
                    billings.append(performance["billing"])
                    billingIndexes.append(performance["billingIndex"])
                    artistIds.append(artist["id"])
                    artistNames.append(artist["displayName"])
                    artistUrls.append(artist["uri"])
                    eventIds.append(event['id']) 
                    eventTypes.append(event['type'])
                    eventUrls.append(event['uri'])
                    eventDates.append(event['start']['date'])
                    venueIds.append(event['venue']['id'])
                    venueNames.append(event['venue']['displayName'])
                    locationCities.append(event['location']['city']) 
                    concertTimes.append(event["start"]["datetime"])
 
        page = page + 1
        resp = getUpcomingShowsPage(metroId, minDate,maxDate, page)
        results = resp["resultsPage"]["results"]
    
    data = pd.DataFrame(
            {
                "artistId" : artistIds,
                "artistName" : artistNames,
                "artistUrl" : artistUrls,
                "billing" : billings,
                "billingIndex" : billingIndexes,
                "eventId" : eventIds,
                "eventType" : eventTypes,
                "eventUrl" : eventUrls,
                "eventDate" : eventDates,
                "venueId" : venueIds,
                "venueName" : venueNames,
                "locationCity" : locationCities,
                "concertTime" : concertTimes
            })
    
    return data

# this adds the correct ordinal to the date
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

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
                sendTweet(thisTweet)
                toTweet.loc[index,'tweeted'] = 1
    else:
        print("nothing to send")
        
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
    
    toTweet = pd.DataFrame(toTweet,columns=["artistId","artistName","concertTime","content","eventDate","billingIndex","tweeted"])
    toTweet['concertTime'] = toTweet['concertTime'].apply(lambda x: datetime.strptime(x,"%Y-%m-%d %H:%M:%S+00"))
    toTweet['concertTime'] = toTweet['concertTime'].apply(lambda x: x - timedelta(hours=(5)) + timedelta(minutes=(4)))
    toTweet['concertTime'] = toTweet['concertTime'].apply(lambda x: x.replace(tzinfo=eastern))
    toTweet = toTweet.sort_values(by=['concertTime'], ascending=True)
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