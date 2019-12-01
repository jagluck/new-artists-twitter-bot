# import packages we need
import requests as requests
import json
from datetime import datetime, timedelta, date
from pytz import timezone
import pandas as pd
import tweepy
import os

# to run on heroku
# Consumer keys and access tokens, used for OAuth
songkick_api_key = os.environ['songkick_api_key']
tw_consumer_key = os.environ["tw_consumer_key"]
tw_consumer_secret = os.environ["tw_consumer_secret"]
tw_access_token = os.environ["tw_access_token"]
tw_access_token_secret = os.environ["tw_access_token_secret"]

# # to run locally
# keys={}
# with open(os.path.abspath("keys.json"),"r") as f:
#     keys = json.loads(f.read())
# songkick_api_key = keys['songkick_api_key']
# tw_consumer_key = keys["tw_consumer_key"]
# tw_consumer_secret = keys["tw_consumer_secret"]
# tw_access_token = keys["tw_access_token"]
# tw_access_token_secret = keys["tw_access_token_secret"]


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
        
        thisTweet = toTweet['content'][0]
        thisTime = toTweet['concertTime'][0]
        thisArtist = toTweet['artistName'][0]
        
        while (timeNow > thisTime and len(toTweet) > 0):

            toTweet = toTweet[toTweet['artistName'] != thisArtist]
            toTweet = toTweet.reset_index(drop=True)
            print("show already happened")
            print(len(toTweet['content']))
            thisTweet = toTweet['content'][0]
            thisTime = toTweet['concertTime'][0]
            thisArtist = toTweet['artistName'][0]
            
        if (len(toTweet) > 0):
            
            print(thisTweet)
    
            # only comment out for testing
            sendTweet(thisTweet)
            
            toTweet = toTweet[toTweet['artistName'] != thisArtist]
            toTweet = toTweet.reset_index(drop=True)
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
                
            artistsWhoPlayedInDC.append(artistId)  
            
    toTweetNew = pd.DataFrame(
            {
                "artistId" : artistIds,
                "artistName" : artistNames,
                "content" : contents,
                "concertTime" : concertTimes,
                "eventDate" : eventDates,
                "billingIndex" : billingIndexes
            })
    return artistsWhoPlayedInDC, toTweetNew