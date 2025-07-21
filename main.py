from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workflow import get_workflow, get_credential
from pydantic import BaseModel
from dotenv import load_dotenv
from google_config import get_worksheet_data
import json
import requests
from deepdiff import DeepDiff
import re

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def replace_keys_in_json(match, replacements):
    json_str = match.group(0)
    obj = json.loads(json_str)
    for k, v in replacements.items():
        if k in obj:
            obj[k] = v
    return json.dumps(obj)


def google_sheets(node, response):
    credential = get_credential(node["data"]["account"])

    data = get_worksheet_data(node, credential)

    diff = DeepDiff(node["data"]["response"], data, ignore_order=True)

    # If no diff at all, return False
    if not diff:
        return False

    # Extract only newly added items (e.g., new rows)
    added_items = diff.get('iterable_item_added', {})
    new_objects = list(added_items.values())

    return new_objects


def extract_value(match):
    obj = json.loads(match.group(0))
    # Return the only value in the JSON object
    return next(iter(obj.values()))


def slack(node, response):
    credential = get_credential(node["data"]["account"])
    print(credential)
    message_strings = []
    message_template = node["data"]["messageText"]

    for row in response:
        new_msg = re.sub(
            r'\{[^{}]+\}', lambda m: replace_keys_in_json(m, row), message_template)

        result = re.sub(r'\{[^{}]+\}', extract_value, new_msg)

        message_strings.append(result)

    print("message_strings", message_strings)
    # setup
    # replace with the user id
    user_id = credential['data']['authed_user']["id"]
    access_token = credential['data']['access_token']
    message = "\n".join(message_strings)

    # Step 1: Open a DM channel with the user
    open_dm_url = "https://slack.com/api/conversations.open"
    open_dm_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    open_dm_payload = {
        "users": user_id
    }
    open_dm_response = requests.post(
        open_dm_url, headers=open_dm_headers, json=open_dm_payload)

    channel_id = open_dm_response.json()['channel']['id']

    # Step 2: Send a message to that channel
    send_msg_url = "https://slack.com/api/chat.postMessage"
    send_msg_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    send_msg_payload = {
        "channel": channel_id,
        "text": message
    }
    send_msg_response = requests.post(
        send_msg_url, headers=send_msg_headers, json=send_msg_payload)


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
    response = []
    # print(json.dumps(workflow, indent=4))
    for node in workflow["node"]:
        if (node["type"] == "google_sheets"):
            result = google_sheets(node, response)
            if not result:
                break
            response += result

        if (node["type"] == "slack"):
            slack(node, response)

    return workflow
