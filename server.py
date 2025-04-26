import asyncio
import os
import uuid
from fastapi import FastAPI,status,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add podcast request model
class PodcastRequest(BaseModel):
    url: str

# Process the long tasks
async def process_task(task_id: str):
    # Simulate a long task
    await asyncio.sleep(20)
    # Update the task status to "completed" on the database
    collection.update_one(
        {"task_id": task_id},
        {"$set": {"status": "completed"}}
    )

# Initialize mongo client
client = MongoClient(os.getenv("MONGO_CLIENT_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
collection = db[os.getenv("MONGO_COLLECTION_NAME")]

@app.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_podcast(request: PodcastRequest, background_tasks:BackgroundTasks ):
    # Accept url from user and create a task
    task_id = str(uuid.uuid4())
    # Get the url from the user or use a default url
    url = request.url or "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # Create a task in the database
    collection.insert_one(
        {
            "task_id": task_id,
            "resource_url": url,
            "status": "pending"
        }
    )
    background_tasks.add_task(process_task, task_id)
    return {"task_id": task_id}

# Track the status of the task
@app.get("/status/{task_id}")
async def get_task_status(task_id:str):
    # Use task id to get process status
    task = collection.find_one({"task_id": task_id})
    if task and task['status'] == "completed":
        return {
            "status": task['status'],
            "resource_url": task['resource_url']
        }
    return {"status": "Not-found"}
@app.get("/")
async def health_check():
    return {"status": "ok"}