from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.utils.tasks import update_statistics, check_media_files_expiration


def start_scheduler() -> AsyncIOScheduler:
    """
    Start the scheduler for periodic tasks.

    :return: The scheduler.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_executor(AsyncIOExecutor())

    scheduler.add_job(update_statistics, IntervalTrigger(minutes=30))
    scheduler.add_job(check_media_files_expiration, IntervalTrigger(days=1))
    scheduler.start()
    return scheduler