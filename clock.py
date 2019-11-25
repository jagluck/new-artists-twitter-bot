from apscheduler.schedulers.blocking import BlockingScheduler
from bot import *

toTweet = {}
artistsWhoPlayedInDC = []
    
sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=60)
def timed_job():
    global toTweet
    print("Start sending new tweet now")
    toTweet = sendNextTweet(toTweet)

@sched.scheduled_job('cron', hour=8)
def scheduled_job():
    print("it is 8am - start search")
    global toTweet
    global artistsWhoPlayedInDc
    cityName = "Washington, DC, US"
    cityId = "1409"
    days = 1
    artistsWhoPlayedInDC, toTweetNew = runBot(days,cityName,cityId,artistsWhoPlayedInDC)
    toTweet = Merge(toTweet, toTweetNew)
              
print("start script")
sched.start()