from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=3)
def timed_job():
    print('This job is run every three minutes.')
    
# @sched.scheduled_job('cron', day_of_week='mon-sun', hour=9)
# def scheduled_job():
#     print('This job is run every weekday at 9am.')

sched.start()