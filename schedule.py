from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import time

scheduler = BackgroundScheduler()

# Define your periodic task
def my_periodic_task():
    print(f"Task executed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Define FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: add job and start scheduler
    scheduler.add_job(my_periodic_task, 'interval', minutes=2)
    scheduler.start()
    print("Scheduler started")

    yield  # Wait for app shutdown

    # Shutdown: gracefully stop scheduler
    scheduler.shutdown()
    print("Scheduler stopped")

# FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
