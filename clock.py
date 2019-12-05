from apscheduler.schedulers.blocking import BlockingScheduler

def timed_job():
    onceADay()

def scheduled_job():
    everyHour()


scheduler = BlockingScheduler()
scheduler.add_job(timed_job, 'cron', hour=8)
scheduler.add_job(scheduled_job, 'interval', minutes=60)
scheduler.start()
print("start script")