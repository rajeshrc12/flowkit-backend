from db import MongoDB
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional


class Workflow(BaseModel):
    name: str
    node: Optional[dict] = None
    edge: Optional[dict] = None
    userId: str


def serialize_doc(doc):
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    elif isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc


def get_collection():
    return MongoDB.get_collection("Workflow")


def get_credential_collection():
    return MongoDB.get_collection("Credential")


def get_all_workflow():
    return list(get_collection().find())


def get_all_credential():
    return list(get_collection().find())


def get_workflow(workflow_id: str):
    doc = get_collection().find_one({"_id": ObjectId(workflow_id)})
    return serialize_doc(doc)


def get_credential(credential_id: str):
    doc = get_credential_collection().find_one(
        {"_id": ObjectId(credential_id)})
    return serialize_doc(doc)


def create_workflow(workflow: Workflow):
    result = get_collection().insert_one(workflow.model_dump())
    return get_workflow(str(result.inserted_id))


def update_workflow(workflow_id: str, workflow: Workflow):
    get_collection().update_one({"_id": ObjectId(workflow_id)}, {
        "$set": workflow.model_dump()})
    return get_workflow(workflow_id)


def delete_workflow(workflow_id: str):
    result = get_collection().delete_one({"_id": ObjectId(workflow_id)})
    return result.deleted_count > 0
