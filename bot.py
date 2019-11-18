import requests as requests
import json
from datetime import datetime, timedelta, date
import pandas as pd
import tweepy
import os
    
# keys={}
# with open("/Users/jagluck/Documents/GitHub/new-artists-twitter-bot/keys.json","r") as f:
#     keys = json.loads(f.read())

# Consumer keys and access tokens, used for OAuth
songkick_api_key = os.environ['songkick_api_key']
tw_consumer_key = os.environ["tw_consumer_key"]
tw_consumer_secret = os.environ["tw_consumer_secret"]
tw_access_token = os.environ["tw_access_token"]
tw_access_token_secret = os.environ["tw_access_token_secret"]
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

def sendTweet(content):
    api.update_status(content)
    
def getArtistHistoryPage(artistId,page):
    
    url = "https://api.songkick.com/api/3.0/artists/" + str(artistId) + "/gigography.json"
    params = {'apikey': songkick_api_key, "page" : page, "per_page" : 50}
    resp = requests.get(url, params=params) 
    return json.loads(resp.text)


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

def getUpcomingShowsPage(metroId, minDate,maxDate,page):
    
    url = "https://api.songkick.com/api/3.0/metro_areas/" + metroId + "/calendar.json"
    params = {'apikey': songkick_api_key, "min_date" : minDate, "max_date" : maxDate, "page" : page, "per_page" : 50}
    resp = requests.get(url, params=params) 
    return json.loads(resp.text)

def getUpcomingShows(daysAhead, metroId):
   
    artistIds = []
    artistNames = []
    artistUrls = []
    billings = []
    eventIds = []
    eventTypes = []
    eventUrls = []
    dates = []
    venueIds = []
    venueNames = []
    locationCities = []
    
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
                    artistIds.append(artist["id"])
                    artistNames.append(artist["displayName"])
                    artistUrls.append(artist["uri"])
                    eventIds.append(event['id']) 
                    eventTypes.append(event['type'])
                    eventUrls.append(event['uri'])
                    dates.append(event['start']['date'])
                    venueIds.append(event['venue']['id'])
                    venueNames.append(event['venue']['displayName'])
                    locationCities.append(event['location']['city']) 
 
        page = page + 1
        resp = getUpcomingShowsPage(metroId, minDate,maxDate, page)
        results = resp["resultsPage"]["results"]
    
    data = pd.DataFrame(
            {
                "artistId" : artistIds,
                "artistName" : artistNames,
                "artistUrl" : artistUrls,
                "billing" : billings,
                "eventId" : eventIds,
                "eventType" : eventTypes,
                "eventUrl" : eventUrls,
                "date" : dates,
                "venueId" : venueIds,
                "venueName" : venueNames,
                "locationCity" : locationCities
            })
    
    return data

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def runBot(days,cityName,cityId):
    
    artistsWhoPlayedInDC = []
    upcomingShows = getUpcomingShows(days,cityId)
    upcomingShows = upcomingShows[upcomingShows["locationCity"] == cityName]
    for artistId, artistName, artistUrl, venueName, eventDate, eventUrl in zip(upcomingShows["artistId"],upcomingShows["artistName"],upcomingShows["artistUrl"],upcomingShows["venueName"],upcomingShows["date"],upcomingShows["eventUrl"]):

        if artistId not in artistsWhoPlayedInDC:
            if not wasArtistInCity(cityName, artistId):
                dateString = datetime.strptime(eventDate, "%Y-%m-%d").strftime("%B") + " " + ordinal(datetime.strptime(eventDate, "%Y-%m-%d").day)
                content = (str(artistName) + " is playing their first concert in DC at " + venueName + " on " + dateString + " " + eventUrl)
                sendTweet(content)
            artistsWhoPlayedInDC.append(artistId)      