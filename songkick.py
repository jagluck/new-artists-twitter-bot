from config import *

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
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

