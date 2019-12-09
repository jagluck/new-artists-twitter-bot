from config import *

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
    
def formatName(name):
    name = name.lower()
    name = name.replace(" ", "")
    name = name.replace("_", "")
    name = name.replace("'", "")
    name = name.replace("\"", "")
    name = name.replace("(US)", "")
    name = name.replace(",", "")
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = re.sub('\W', '', name)
    return name

def findHandle(artistName):

    searchAccounts = api.search_users(artistName,20,1)

    artistName = formatName(artistName)
#     print(artistName)
#     print("#####")

    maxScore = 0
    maxHandle = "None"

    for acj in searchAccounts:
        thisScore = 0
        account = acj._json
#         print(account.keys())
        thisScreenName = formatName(account['screen_name'])
        thisName = formatName(account['name'])

#         print("screen name: " + thisScreenName)
#         print("name: " + thisName)

        # check name
        if (artistName == thisName):
#             print("name perfect match +50")
            thisScore = thisScore + 50
        elif (artistName in thisName):
#             print("name sub match +25")
            thisScore = thisScore + 25

        if ("band" in thisName):
#             print("name band match +30")
            thisScore = thisScore + 30

        if ("music" in thisName):
#             print("name music match +30")
            thisScore = thisScore + 30

        # check screen name
        if (artistName == thisScreenName):
#             print("screen name perfect match +25")
            thisScore = thisScore + 25
        elif (artistName in thisScreenName):
#             print("screen name sub match +13")
            thisScore = thisScore + 13

        if ("band" in thisScreenName):
#             print("screen name band match +15")
            thisScore = thisScore + 15

        if ("music" in thisScreenName):
#             print("screen name music match +15")
            thisScore = thisScore + 15

        # check verified
        if (account['verified'] == True):
#             print("verified +20")
            thisScore = thisScore + 20

        # check followers
        followersPoints = math.ceil(account['followers_count']/100)
        if (followersPoints > 20):
            followersPoints = 20
        thisScore = thisScore + followersPoints
#         print("followers: +" + str(followersPoints))

        # if they have an image
        if (account['default_profile_image']):
#             print("no background image: -50")
            thisScore = thisScore - 50
            
        # see if they have a url
        if (account['url'] != None):
            r = requests.head(account['url'], allow_redirects=True)
            accountLink = r.url.lower()
            musicSites = ['soundcloud''bandcamp','spotify','itunes']
            for musicSite in musicSites:
                if musicSite in accountLink:
#                     print("music site link " + musicSite + ": +50")
                    thisScore = thisScore + 50
                    
            if (artistName in accountLink):
#                 print("site link " + artistName + ": +30")
                thisScore = thisScore + 30
#             print(r.url)

        # private/public
        if (account['protected']):
#             print("protected: -50")
            thisScore = thisScore - 50

        # check description

        description = account['description'].lower()
        descriptionWordList = ['mgmt', 'managment','band','inquiries','music','tour','album','stream','song','single']
        for word in descriptionWordList:
            if word in description:
#                 print("description match " + word + ": +20")
                thisScore = thisScore + 20

        # look for fan accounts
        if ("fan account" in description):
#             print("fan account: -100")
            thisScore = thisScore - 100

#         print("total score: " + str(thisScore))
#         print("----")

        if (thisScore > maxScore):
            maxScore = thisScore
            maxHandle = account['screen_name']
    
    if (maxScore > 99):
        return maxHandle
    else:
        return "None"                        
    
# this runs every hour, it sends the first tweet that is qualified if there is one
def sendNextTweet(toTweet):
    print(len(toTweet))
    if (len(toTweet) != 0):
        
        now = datetime.now()
        if (now.hour < 21):

            # maybe add a check now or somekind of resorting logic to make sure show has not already happened

            timeNow = datetime.now(eastern)

            didWeTweet = False

            for index,row in toTweet.iterrows():
                # did we not already tweet something this hour and did it not already happen and did we not already tweet it?
                if ((didWeTweet == False) and (row['concertTime'] > timeNow) and (row['tweeted'] == 0)):
                    didWeTweet = True
                    thisTweet = row['content']
                    handleResponse = findHandle(row['artistName'])
                    if (handleResponse == "None"):
                        thisTweet = row['artistName'] + thisTweet
                    else:
                        thisTweet = row['artistName'] + " @" + handleResponse + thisTweet
  
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
                content = " is playing their first show in DC!"
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
    days = 3
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
    