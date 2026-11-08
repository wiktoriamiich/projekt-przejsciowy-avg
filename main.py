import networkx as nx
import asyncio
import math
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AGV Visualization</title>
</head>
<body>
    <h2>AGV coordinates</h2>
    <p>Click F12 and open the developer console to see the AGV positions.</p>
    <script>
        const ws = new WebSocket('ws://127.0.0.1:8000/ws');
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log("Received data:", data);
        };
    </script>
</body>
</html>
"""

@app.get("/")
async def get_index():
    return HTMLResponse(html_content)

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
    def __init__(self, agvID, currentNode, x, y):
        self.agvID = agvID
        self.currentNode = currentNode
        self.x =x
        self.y = y
    def print_status(self):
        print(f"AGV: {self.agvID} is located in node: {self.currentNode}, coordinates: ({self.x}, {self.y})")

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
                agv.print_status()

                await websocket.send_json({"AGV": agv.agvID, "CurrentNode": agv.currentNode, "Coordinates": (agv.x, agv.y)})
                await asyncio.sleep(1)

        agv.currentNode = nextNode
        print(f"AGV: {agv.agvID} has reached node: {nextNode}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"Status": "Start AGV simulation"})

    agv1 = AGV("AGV_1", "StacjaA", 0, 0)
    await moveAGV(agv1, "StacjaB", 2, G, websocket)


#asyncio.run(moveAGV(agv1, "StacjaB", 2, G))
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

