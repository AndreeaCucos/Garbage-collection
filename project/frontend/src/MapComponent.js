import React, { Component } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import "leaflet/dist/leaflet.css";
import 'leaflet-routing-machine';
import 'leaflet-labels';
import './comp.css';
import "./MapComponent.css";
import { v4 as uuidv4 } from 'uuid';


class Map extends Component {
    constructor() {
        super();
        this.state = {
            position: [51.505, -0.09],
            zoom: 20,
            center: null,
            markers: null,
            markerPos: null,
            nodes: null,
            size: 0,
            mesage: "",
            circleM: null,
            routes: null,
            done: false,
            color: "gray",
            errorMsg: '',
            streets: []
        };
        this.routingControl = null;
        this.handleMoveMarker = this.handleMoveMarker.bind(this);
    }

    delay = ms => new Promise(
        resolve => setTimeout(resolve, ms)
    );

    async componentDidMount() {
        // Verificăm dacă token-ul utilizatorului nu a expirat.
        const resp = await fetch('/api/users',
            {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                    'Content-Type': 'application/json'
                }
            });
        if (resp.status === 401) {
            localStorage.removeItem("user");
            window.location.href = '/login';
        } else if (resp.ok) {
            const urlParams = new URLSearchParams(window.location.search);
            const type = urlParams.get('zona');
            console.log(type);
            // Realizăm cererea la Nominatim OpenStreetMap pentru a primi coodonatele centrului adresei.
            const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${type}&format=json&limit=1`);
            if (response.ok) {
                const data = await response.json();
                const lat = data[0]["lat"];
                const lon = data[0]["lon"];
                const c = [lat, lon];
                console.log(c);
                this.setState({ center: c });
                this.map = L.map('map').setView(c, 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors',
                    maxZoom: 19,
                }).addTo(this.map);
            }
        }
    }

    handleMoveMarker = async () => {
        const node_list = this.state.nodes;
        // Extragem din adresa URL denumirea orașului și a cartierului.
        const urlParams = new URLSearchParams(window.location.search);
        const zona = urlParams.get("zona");
        // Facem cerere la backend pentru a primi traseul dorit.
        const r = await fetch(`/api/garph/${encodeURIComponent(zona)}/path`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                'Content-Type': 'application/json'
            }
        });
        if (r.ok) {
            var response = await r.json();
            var path = response["path"];
            const streets = response["streets"];
            this.setState({ streets: streets });
            // Dacă răspunsul primit este None, înseamnă că nu a fost creat cu succes digraful.
            if (path === 'None') {
                this.setState({ message: "Introduceti o valoare mai mare!" });
            }
            const markers = this.state.marker;
            const iconUrl = './garbage.png';
            const iconSize = [30, 30];
            const start = parseInt(path[0]);
            const result = Object.keys(node_list).find(key => node_list[key] === parseInt(start));
            const coords = [markers[result]["lat"], markers[result]["lon"]];
            console.log(coords);
            // Adăugăm un nou marker peste nodul de start pentru a marca faptul
            // că de aici se pleacă și tot aici se ajunge.
            const circleMarker = L.circleMarker(coords, { radius: 10, fillColor: '#3388ff', fillOpacity: 0.8, color: 'red', weight: 2 });
            // Marcăm nodul de start cu roșu.
            circleMarker.bindTooltip(`S`, {
                permanent: true,
                direction: 'center',
                className: 'custom-start'
            }).openTooltip();
            // Adăugăm marker-ul hărții.
            circleMarker.addTo(this.map);
            // Buclă for în care mișcăm marker-ul cu iconița peste nodurile din trase.
            for (let i = 0; i < path.length; i++) {
                const result = Object.keys(node_list).find(key => node_list[key] === parseInt(path[i]));
                const coords = [markers[result]["lat"], markers[result]["lon"]];
                const circleMarker = L.circleMarker(coords, { radius: 7, fillColor: '#3388ff', fillOpacity: 0.8, weight: 2 });
                // Adăugăm imaginea nodului.
                circleMarker.addTo(this.map).bindPopup('<img src="' + iconUrl + '" width="' + iconSize[0] + '" height="' + iconSize[1] + '" alt="Marker Icon" />')
                    .openPopup();
                await this.delay(1000);
                circleMarker.remove();
            }
            await this.delay(100);
            circleMarker.remove();
        } else if (r.status === 401) {
            // Dacă token-ul utilizatorului a expirat, ștergem informațiile aferente lui
            // stocate în localStorage și redirecționăm către pagina de autentificare.
            localStorage.removeItem("user");
            window.location.href = '/login';
        } else if (r.status === 400)
        {
            this.setState({errorMsg: "Introduceți o rază mai mică!"});
        }
    }

    handleSubmit = async () => {
        if (this.state.size <= 0) {
            this.setState({ errorMsg: 'Valoarea nu poate fi negativă!' });
        }
        else if ((Number.isInteger(Number(this.state.size))) === false) {
            this.setState({ errorMsg: 'Valoarea trebuie să fie număr întreg!' });
        }
        else {
            // Aceste două condiții au rolul de a șterge elementele afișate pe hartă
            // pentru cazul în care utilizatorul introduce altă valoare pentru
            // rază și va fi creat un nou digraf.
            // Eliminăm nodurile de pe hartă.
            if (this.state.circleM !== null) {
                for (let i = 0; i < this.state.circleM.length; i++) {
                    this.state.circleM[i].remove(this.map);
                }
            }
            // Eliminăm și rutele existente pe hartă.
            if (this.state.routes !== null) {
                for (let i = 0; i < this.state.routes.length; i++) {
                    this.map.removeControl(this.state.routes[i]);
                }
            }
            await this.delay(100);
            const urlParams = new URLSearchParams(window.location.search);
            // Trimitem informațiile la backend pentru a crea digraful.
            const r = await fetch(`/api/graph`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location: this.state.center, size: this.state.size, denumire: urlParams.get('zona')
                })
            });
            if (r.ok) {
                this.setState({ errorMsg: '' });
                const msg = await r.json();
                var values = msg["result"];
                // Facem cerere la backend pentru a primi matricea de adiacență a digrafului
                // și dicționarul cu indecșii nodurilor.
                const resp = await fetch(`/api/graph/${encodeURIComponent(urlParams.get('zona'))}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                        'Content-Type': 'application/json'
                    }
                });

                if (resp.ok) {
                    var answer = await resp.json();
                    var matrix = answer["matrix"];
                    var nodes = answer["nodes"];
                    this.setState({ nodes: nodes });
                    var mark = {};
                    var circles = [];
                    // Adăugăm nodurile pe hartă.
                    for (let k in values) {
                        const circleMarker = L.circleMarker(values[k], {
                            radius: 7,
                            fillColor: '#3388ff',
                            fillOpacity: 0.8,
                            color: '#3388ff',
                            weight: 2,

                        });
                        // Adăugăm pentru fiecare nod numărul acestuia.(indexul)
                        circleMarker.bindTooltip(`${nodes[k]}`, {
                            permanent: true,
                            direction: 'center',
                            className: 'custom-tooltip'
                        }).openTooltip();
                        circleMarker.addTo(this.map);
                        mark[k] = { lat: values[k][0], lon: values[k][1] };
                        circles.push(circleMarker);
                    }
                    this.setState({ circleM: circles });
                    this.setState({ marker: mark });
                    const entries = Object.entries(mark);
                    // Salvăm într-un dicționar toate nodurile care sunt conectate împreună cu costul
                    // aferent arcului.
                    var connections = {};
                    for (let i = 0; i < matrix.length; i++) {
                        for (let j = 0; j < matrix.length; j++) {
                            if (!(`${i}, ${j}` in connections) && !(`${j}, ${i}` in connections)) {
                                if (matrix[i][j] !== 0) {
                                    connections[`${i}, ${j}`] = matrix[i][j];
                                }
                            }
                        }
                    }
                    // Adăugăm pe hartă rutele corespunzătoare conexiunilor determinate anterior.
                    var routes = [];
                    for (let key in connections) {
                        const parts = key.split(", ");
                        const i = parseInt(parts[0]);
                        const j = parseInt(parts[1]);
                        const point1 = L.latLng(entries[i][1]['lat'], entries[i][1]['lon']);
                        const point2 = L.latLng(entries[j][1]['lat'], entries[j][1]['lon']);
                        console.log(`${i}, ${j}`);
                        var rt = L.Routing.control({
                            waypoints: [point1, point2],
                            router: L.Routing.osrmv1({
                                serviceUrl: 'https://router.project-osrm.org/route/v1',
                                profile: 'driving',
                            }),
                            createMarker: () => null,
                            routeWhileDragging: true,
                            lineOptions: {
                                styles: [{ color: '#006699', weight: 5 }],
                            },
                            fitSelectedRoutes: false,
                            altLineOptions: {
                                styles: [{ color: '#CCCCCC', weight: 5 }],
                            },
                            addWaypoints: true,
                        });
                        rt.addTo(this.map);
                        routes.push(rt);
                        await this.delay(1000);
                    }
                    this.setState({ routes: routes });
                    this.setState({ done: true });
                    this.setState({ color: "#0f553e" });
                }
            }
            else if (r.status === 400) {
                var msg = await r.json();
                console.log(msg['error']);
                this.setState({ errorMsg: 'Introduceți o valoare mai mare !' });
            }
            else if (r.status === 401) {
                localStorage.removeItem("user");
                window.location.href = '/login';
            }
        }
    }

    handleFinish = async () => {
        // Marcăm faptul că utilizatorul a terminat de parcurs traseul.
        const r = await fetch('/api/users/neighbourhoods', {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                'Content-Type': 'application/json'
            }
        });
        if (r.ok) {
            window.location.href = '/';
        }
        else {
            console.log(r.status);
            if (r.status === 401) {
                localStorage.removeItem("user");
                window.location.href = '/login';
            }
        }

    }

    render() {
        return (
            <div
                id="app-conatiner"
                style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100vh',
                    backgroundColor: '#e0dfdf',
                    overflow: 'hidden',
                }}
            >
                <div style={{ overflow: 'hidden', height: '100%', textAlign: 'center', marginTop: '30px' }}>
                    <div id="map" style={{ height: '515px', width: '950px', margin: '0 auto' }}></div>
                </div>
                <div id='text' style={{ backgroundColor: 'black', textAlign: 'center', marginLeft: '40px', padding: '10px', height: '258px' }}>
                    <form>
                        <p style={{ color: 'white' }}>Introduceți valoarea razei</p>
                        <input style={{ width: '70px' }} value={this.state.size} onChange={(e) => this.setState({ size: e.target.value})} />
                        <br />
                        <p style={{ color: 'red', fontSize: '12px' }}>{this.state.errorMsg}</p>
                        <br />
                        <button type='button' onClick={this.handleSubmit}>Submit</button>
                    </form>
                    <br />
                    <button style={{ backgroundColor: this.state.color }} onClick={this.handleMoveMarker}  >Start</button>
                    <br />
                    <br />
                    <button style={{ backgroundColor: this.state.color }} onClick={this.handleFinish} disabled={!this.state.done}>Terminat</button>
                    <br />

                </div>
                <br />
                <div style={{ marginTop: '200px', marginLeft: '-220px', height: '200px', width: '240px', border: '1px solid black', overflowY: 'scroll', backgroundColor: '#fff', color: 'black', fontSize: '13px' }}>
                    <p style={{ textAlign: 'center' }}>Traseul este:</p>
                    {this.state.streets.map(name => (
                        <div key={uuidv4()}>&nbsp;- {name[1]}, {name[2]}</div>
                    ))}
                </div>
            </div>
        );
    }
}

export default Map;


