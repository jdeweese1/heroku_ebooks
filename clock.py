from apscheduler.schedulers.blocking import BlockingScheduler
import local_settings as settings
from ebooks import run_all

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=settings.RUN_INTERVAL)
def markov_job():
    run_all()
