from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workflow import get_workflow
from pydantic import BaseModel
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from google import genai
import json
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()
chat = client.chats.create(model="gemini-2.5-flash")

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


class ChatState(TypedDict):
    message: str
    chat_message: list


def agent(state: ChatState):
    pass


def chat_node(state: ChatState):
    pass


def gemini(state: ChatState):
    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            history=[
                genai.types.Content(
                    role=item["role"],
                    parts=[genai.types.Part(text=part)
                           for part in item["parts"]]
                )
                for item in state["chat_message"]
            ]
        )
        # Send current message
        state["chat_message"].append(
            {"role": "user", "parts": [state["message"]]})
        response = chat.send_message(state["message"])
        state["chat_message"].append(
            {"role": "model", "parts": [response.text]})
        return state

    except Exception as e:
        print("Error:", str(e))
        return state


graph_builder = StateGraph(ChatState)

graph_builder.add_node("chat_node", chat_node)
graph_builder.add_node("agent", agent)
graph_builder.add_node("gemini", gemini)

g = 0


@app.get("/")
def hello():
    return "Hello World"


class ChatRequest(BaseModel):
    workflow_id: str
    message: str
    chat_message: list


@app.post("/chat")
def run_chat(request: ChatRequest):
    global g
    workflow = get_workflow(request.workflow_id)
    _state: ChatState = {
        "chat_message": request.chat_message,
        "message": request.message,
    }

    edges = workflow["edge"]

    if (len(edges) < 3 and g == 0):
        g = 1
        graph_builder.add_edge(START, edges[0]["source"])
        graph_builder.add_edge(edges[0]["source"], edges[1]["target"])
        graph_builder.add_edge(edges[1]["target"], END)

    graph = graph_builder.compile()
    graph_result = graph.invoke(_state)
    print(graph_result)
    return {"chat_message": graph_result.get("chat_message")}
    return {}
