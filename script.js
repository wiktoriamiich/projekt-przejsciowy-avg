function sendTask(){
    //pobranie wybranych wartosci z obu list <select> po ich ID
    const start = document.getElementById("startNode").value;
    const target = document.getElementById("targetNode").value;
    const selectedAGV = document.getElementById("agvSelect").value

    //zabezpieczenie przed wyslaniem zadania z tego samego punktu start i target
    if(start === target){
        alert("Wybierz różne stacje startową i doelową");
        return
    }
    //wyslanie pakietu JSON przez otwarte polaczenie WebSocket 
    ws.send(JSON.stringify({
    action: "add_task",
    agv: selectedAGV,
    startNode: start,
    targetNode: target
    }));
}


