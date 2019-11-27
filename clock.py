from apscheduler.schedulers.blocking import BlockingScheduler
from bot import *

toTweet = {}
artistsWhoPlayedInDC = []

def timed_job():
    global toTweet
    print("Start sending new tweet now")
    toTweet = sendNextTweet(toTweet)

def scheduled_job():
    print("it is 8am - start search")
    global toTweet
    global artistsWhoPlayedInDc
    cityName = "Washington, DC, US"
    cityId = "1409"
    days = 1
    artistsWhoPlayedInDC, toTweetNew = runBot(days,cityName,cityId,artistsWhoPlayedInDC)
    toTweet = Merge(toTweet, toTweetNew)

    from apscheduler.schedulers.blocking import BlockingScheduler


scheduler = BlockingScheduler()
scheduler.add_job(scheduled_job, 'cron', hour=8)
scheduler.add_job(timed_job, 'interval', minutes=60)
scheduler.start()
print("start script")