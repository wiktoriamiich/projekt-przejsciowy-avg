import networkx as nx
import asyncio
import math
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI()
@app.get("/")
async def get_index():
    return FileResponse("visualization.html")

print ("Hello world")
G = nx.Graph()
G.add_node("StacjaA", x = 0, y = 0)
G.add_node("Skrzyżowanie", x = 10, y = 0)
G.add_node("StacjaB", x = 10, y = 10)
G.add_edge("StacjaA", "Skrzyżowanie", weight = 10)
G.add_edge("Skrzyżowanie", "StacjaB", weight = 10)

print(G.nodes(data=True))
print(G.edges(data=True))

class AGV:
    def __init__(self, agvID, currentNode, G, status="idle"):
        self.agvID = agvID
        self.currentNode = currentNode
        self.x = G.nodes[currentNode]['x']
        self.y = G.nodes[currentNode]['y']
        self.status = status
        self.path = []
    def print_info(self):
        print(f"AGV: {self.agvID} is located in node: {self.currentNode}, coordinates: ({self.x:.1f}, {self.y:.1f}). AGV status: {self.status})")
class Task:
    def __init__(self, taskID, startNode, targetNode, assignedAGV = "AUTO"):
        self.taskID = taskID
        self.startNode = startNode
        self.targetNode = targetNode
        self.assignedAGV = assignedAGV

def calculateDistance(x,y,targetX, targetY, velocity):
    dx = targetX -x 
    dy = targetY - y
    distance = math.sqrt((targetX - x)**2 + (targetY - y)**2)
    if distance <= velocity:
        return targetX, targetY
    else:
        newX = x + (dx/distance)*velocity
        newY = y + (dy/distance)*velocity
        return newX, newY
    
async def moveAGV(agv, targetNode, velocity, graph, websocket):
    path = nx.shortest_path(graph, agv.currentNode, targetNode, weight='weight')
    print(f"AGV: {agv.agvID} is moving from {agv.currentNode} to {targetNode} via path: {path}")

    for nextNode in path[1:]:
        targetX = graph.nodes[nextNode]['x']
        targetY = graph.nodes[nextNode]['y']
    
        while(agv.x, agv.y) != (targetX, targetY):
                agv.x, agv.y = calculateDistance(agv.x, agv.y, targetX, targetY, velocity)
                agv.print_info()

                await websocket.send_json({
                    "AGV": agv.agvID, 
                    "CurrentNode": agv.currentNode, 
                    "Coordinates": (agv.x, agv.y),
                    "Status": agv.status
                })
                await asyncio.sleep(0.3)

        agv.currentNode = nextNode
        print(f"AGV: {agv.agvID} has reached node: {nextNode}")


async def processTask(agv, task, graph, websocket):
    agv.status = "busy"
    print(f"Task: {task.taskID} for AGV: {agv.agvID}")
    if agv.currentNode != task.startNode:
        print(f"AGV: {agv.agvID} is moving to start task's node: {task.startNode}")
        await moveAGV(agv, task.startNode, 2, graph, websocket)

    print(f"AGV: {agv.agvID} transporitng task: {task.taskID} to target: {task.targetNode}")
    await moveAGV(agv, task.targetNode, 2, graph, websocket)
    agv.status = "idle"
    await websocket.send_json({
                        "AGV": agv.agvID, 
                        "CurrentNode": agv.currentNode, 
                        "Coordinates": (agv.x, agv.y),
                        "Status": agv.status
                    })
    print(f" Task: {task.taskID} completed by AGV: {agv.agvID}")

def getNearestIdleAGV(fleet, startNode, graph):
    idleAGVs = [agv for agv in fleet if agv.status == "idle"]
    if not idleAGVs:
        return None

    return min(
        idleAGVs,
        key = lambda agv: nx.shortest_path_length(graph, agv.currentNode, startNode, weight='weight')
    )
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"Status": "Start AGV simulation"})

    fleet = [
        AGV("AGV_1", "StacjaA", G),
        AGV("AGV_2", "StacjaB", G),
        AGV("AGV_3", "StacjaA", G)
    ]
    for agv in fleet:
        await websocket.send_json({
            "AGV": agv.agvID,
            "CurrentNode": agv.currentNode,
            "Coordinates": (agv.x, agv.y),
            "Status": agv.status
        })
    taskQueue = [
        Task("Task_1", "StacjaA", "StacjaB"),
        Task("Task_2", "StacjaB", "StacjaA")
    ]
    try:
        taskID_counter = len(taskQueue) + 1
        while True:
            for task in list(taskQueue):
                agv = None
                if task.assignedAGV == "AUTO":
                    agv = getNearestIdleAGV(fleet, task.startNode, G)
                else:
                    for a in fleet:
                        if a.agvID == task.assignedAGV and a.status == "idle":
                            agv = a
                            break
                if agv is not None:
                    taskQueue.remove(task)
                    asyncio.create_task(processTask(agv, task, G, websocket))
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.3)
                if data.get("action") == "add_task":
                    print(f"Odebrano zadanie: ",data)
                    new_task = Task(f"Task_{taskID_counter}", data["startNode"], data["targetNode"], data.get("agv", "AUTO"))
                    taskQueue.append(new_task)
                    taskID_counter += 1
                    await websocket.send_json({"Status": f"New task {new_task.taskID} added to the queue"})
            except asyncio.TimeoutError:
                pass
    except (WebSocketDisconnect, asyncio.CancelledError):
        print("WebSocket connection closed")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

 