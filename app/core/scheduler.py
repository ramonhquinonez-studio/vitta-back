from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler: AsyncIOScheduler | None = None

def init_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

def get_scheduler() -> AsyncIOScheduler:
    if not scheduler:
        raise RuntimeError("Scheduler not initialized")
    return scheduler
