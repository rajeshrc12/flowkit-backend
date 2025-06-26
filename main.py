from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workflow import get_workflow
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return "Hello World"

class ChatRequest(BaseModel):
    workflow_id: str
    message: str

@app.post("/chat")
def run_chat(request: ChatRequest):
    workflow = get_workflow(request.workflow_id)

    return {"workflow": workflow, "message": request.message}

