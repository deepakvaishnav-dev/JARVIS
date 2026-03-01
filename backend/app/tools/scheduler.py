import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started successfully.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped.")

def schedule_task(job_id: str, func, trigger: CronTrigger, *args, **kwargs):
    """Add a scheduled task. E.g., trigger=CronTrigger(hour=9, minute=0)"""
    scheduler.add_job(func, trigger=trigger, id=job_id, replace_existing=True, args=args, kwargs=kwargs)
    logger.info(f"Scheduled job '{job_id}'")

# Example job
async def heartbeat_job():
    logger.info("Scheduler heartbeat: I am alive.")
