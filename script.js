
console.log("AGV Symulator został uruchomiony!");
console.log("Mapa fabryki jest gotowa do dalszej rozbudowy.");


const route = [
    { id: "S1", x: 11, y: 55 },
    { id: "B",  x: 25, y: 55 },
    { id: "C",  x: 75, y: 55 },
    { id: "S2", x: 89, y: 55 }
];

console.log("AGV Symulator uruchomiony!");
console.log("Punkty trasy:");

route.forEach(function(point) {
    console.log(point.id, "x:", point.x, "y:", point.y);
});