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


def chat_node(message, chat_history, initial_state):
    initial_state["chat_history"] = chat_history
    initial_state["output"] = message


def agent(node, nodes, edges, initial_state):
    initial_state["tool_result"] = []
    initial_state["model_result"] = []
    nearest_node_ids = []
    tool_nodes = []
    model_nodes = []
    for edge in edges:
        if node["id"] == edge["source"]:
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
            initial_state["tool_result"].append("response from " +
                                                tool["name"]+embedding_node["name"])
        if tool["name"] == "qdrant":
            initial_state["tool_result"].append("response from " +
                                                tool["name"]+embedding_node["name"])

    for model in model_nodes:
        initial_state["model_result"].append(
            "response from " + model["name"])

    initial_state["output"] = " ".join(initial_state["model_result"])


def format_node(initial_state):
    initial_state["output"] = "***"+initial_state["output"]+"***"


def execute_workflow(execution_nodes, nodes, edges, message, chat_history):
    initial_state = {}
    for id in execution_nodes:
        node = get_node_by_id(id, nodes)

        if node["name"] == "chat_node":
            chat_node(message, chat_history, initial_state)

        if node["name"] == "agent":
            agent(node, nodes, edges, initial_state)

        if node["name"] == "format_node":
            format_node(initial_state)

    print(initial_state)


workflow_nodes = [
    {
        "id": "i1",
        "name": "chat_node",
        "is_start": True,
        "type": "root"
    },
    {
        "id": "i2",
        "name": "agent",
        "is_start": False,
        "type": "root"
    },
    {
        "id": "i3",
        "name": "pinecone",
        "is_start": False,
        "type": "tool"
    },
    {
        "id": "i4",
        "name": "gemini",
        "is_start": False,
        "type": "model"
    },
    {
        "id": "i5",
        "name": "qdrant",
        "is_start": False,
        "type": "tool"
    },
    {
        "id": "i6",
        "name": "gemini",
        "is_start": False,
        "type": "model"
    },
    {
        "id": "i7",
        "name": "gemini",
        "is_start": False,
        "type": "model"
    },
    {
        "id": "i8",
        "name": "format_node",
        "is_start": False,
        "type": "root"
    }
]

workflow_edges = [
    {
        "source": "i1",
        "target": "i2",
    },
    {
        "source": "i2",
        "target": "i3",
    },
    {
        "source": "i3",
        "target": "i4",
    },
    {
        "source": "i2",
        "target": "i5",
    },
    {
        "source": "i5",
        "target": "i6",
    },
    {
        "source": "i2",
        "target": "i7",
    },
    {
        "source": "i2",
        "target": "i8",
    },
]


message = "hi"
chat_history = []
start_node = get_start_node(workflow_nodes)
execution_nodes = get_execution_nodes(
    start_node, workflow_nodes, workflow_edges)

result = execute_workflow(execution_nodes, workflow_nodes,
                          workflow_edges, message, chat_history)
