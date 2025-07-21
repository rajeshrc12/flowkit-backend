from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workflow import get_workflow
from pydantic import BaseModel
from google_config import genai
from dotenv import load_dotenv
from gemini import retrieve_from_pinecone
import json
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


def get_ordered_nodes(nodes, edges, start_node):
    # Build adjacency list
    graph = {node: [] for node in nodes}
    for edge in edges:
        graph[edge["source"]].append(edge["target"])

    visited = set()
    ordered_nodes = []

    def dfs(node):
        if node not in visited:
            visited.add(node)
            ordered_nodes.append(node)
            for neighbor in graph.get(node, []):
                dfs(neighbor)

    dfs(start_node)
    return ordered_nodes


def get_node_by_id(id, nodes):
    return next((node for node in nodes if node["id"] == id), None)


def get_edge_by_source_id(id, edges):
    return next((edge for edge in edges if edge["source"] == id), None)


def get_edge_by_target_id(id, edges):
    return next((edge for edge in edges if edge["target"] == id), None)


def get_start_node(nodes):
    return next((node for node in nodes if node["is_start"] == True), None)


def get_execution_nodes(start_node, nodes, edges):
    root_node_ids = []
    for node in nodes:
        if node["type"] == "root":
            root_node_ids.append(node["id"])

    root_node_edges = []
    for edge in edges:
        if edge["source"] in root_node_ids and edge["target"] in root_node_ids:
            root_node_edges.append(edge)

    execution_nodes = get_ordered_nodes(
        root_node_ids, root_node_edges, start_node["id"])
    return execution_nodes


def chat_node(message, chat_message, initial_state):
    initial_state["chat_message"] = chat_message
    initial_state["output"] = message


def agent(agent_node, nodes, edges, initial_state):
    tool_result = []
    model_result = []
    nearest_node_ids = []
    tool_nodes = []
    model_nodes = []

    for edge in edges:
        if agent_node["id"] == edge["source"]:
            nearest_node_ids.append(edge["target"])

    for id in nearest_node_ids:
        node = get_node_by_id(id, nodes)
        if node["type"] == "tool":
            tool_nodes.append(node)
        if node["type"] == "model":
            model_nodes.append(node)

    for tool in tool_nodes:
        embedding_node_id = get_edge_by_source_id(
            tool["id"], edges)["target"]
        embedding_node = get_node_by_id(embedding_node_id, nodes)
        if tool["name"] == "pinecone":
            results = retrieve_from_pinecone(initial_state["output"])
            for i, doc in enumerate(results, 1):
                tool_result.append(doc.page_content)

    model_node = model_nodes[0]

    if model_node["name"] == "gemini":
        chat = client.chats.create(
            model="gemini-2.5-flash",
            history=[
                genai.types.Content(
                    role=item["role"],
                    parts=[genai.types.Part(text=part)
                           for part in item["parts"]]
                )
                for item in initial_state["chat_message"]
            ]
        )
        prompt = initial_state["output"]
        if tool_result:
            prompt = f"""
            You need to answer user query based on give data, just return answer no headline or title.
            User query : 
            {initial_state["output"]}
            Data:
            {" ".join(tool_result)}

            """
        initial_state["chat_message"].append(
            {"role": "user", "parts": [initial_state["output"]]})
        response = chat.send_message(prompt)
        initial_state["chat_message"].append(
            {"role": "model", "parts": [response.text]})
        initial_state["output"] = response.text


def format_node(initial_state):
    initial_state["output"] = "***"+initial_state["output"]+"***"


def execute_workflow(execution_nodes, nodes, edges, message, chat_message):
    initial_state = {}
    for id in execution_nodes:
        node = get_node_by_id(id, nodes)

        if node["name"] == "chat_node":
            chat_node(message, chat_message, initial_state)

        if node["name"] == "agent":
            agent(node, nodes, edges, initial_state)

        if node["name"] == "format_node":
            format_node(initial_state)
    return initial_state


@app.get("/")
def health_check():
    return "Hello World"


class ChatRequest(BaseModel):
    workflow_id: str
    message: str
    chat_message: list


@app.post("/chat")
def run_chat(request: ChatRequest):
    workflow = get_workflow(request.workflow_id)
    # print(json.dumps(workflow, indent=4))
    workflow_nodes = []
    workflow_edges = []
    for node in workflow["node"]:
        if "credentialId" in node["data"]:
            print(node["data"]["name"], node["data"]["credentialId"])
        workflow_nodes.append({
            "id": node["id"],
            "name": node["data"]["name"],
            "is_start": node["data"]["isStart"],
            "type": node["data"]["type"]
        })
    for edge in workflow["edge"]:
        workflow_edges.append({
            "source": edge["source"],
            "target": edge["target"],
        })
    start_node = get_start_node(workflow_nodes)
    execution_nodes = get_execution_nodes(
        start_node, workflow_nodes, workflow_edges)
    print(execution_nodes)
    result = execute_workflow(execution_nodes, workflow_nodes,
                              workflow_edges, request.message, request.chat_message)

    # print(result)
    return {"chat_message": result["chat_message"]}
