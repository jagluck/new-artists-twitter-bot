from apscheduler.schedulers.blocking import BlockingScheduler
from bot import *

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=5)
def timed_job():
    print("start search")
    cityName = "Washington, DC, US"
    cityId = "1409"
    days = 1
    runBot(days,cityName,cityId)

# @sched.scheduled_job('cron', hour=8)
# def scheduled_job():
#     print("it is 8am - start search")
#     cityName = "Washington, DC, US"
#     cityId = "1409"
#     days = 1
#     runBot(days,cityName,cityId)
              
print("start script")
sched.start()