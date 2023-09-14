import React from "react";
import Graph from "react-graph-vis";
import "./GraphImage.css";
import cloneDeep from 'lodash/cloneDeep';
import { useParams } from 'react-router-dom';


class GraphImage extends React.Component {
    static index = 0;


    constructor(props) {
        super(props);

        this.state = {
            response: '',
            matrix: [[]],
            path: '',
            graph: {
                nodes: [],
                edges: []
            },
            items: [],
            lista: [],
            liste: { initial: [], final: [] },
            doubled: "",
            pairsResponse: "",
            start: "",
            showHTML: [true, false, false],
            showHTML1: true,
            showHTML2: false,
            showHTML3: false,
            inputValue: "",
            medals: {
                0: {
                    "chance": 3,
                    "answer": false
                },
                1: {
                    "chance": 3,
                    "answer": false,
                },
                2: {
                    "chance": 3,
                    "answer": false,
                }
            },
            startNode: "",
            currentTime: 0
        }
        this.changeColor = this.changeColor.bind(this);
        this.intervalId = null;
    }


    handleClick = async () => {
        var cale = [];
        for (let i = 1; i < this.state.liste.final.length; i++) {
            cale.push(parseInt(this.state.liste.final[i]["text"].split(" ")[1]));
        }
        const dict = JSON.parse(localStorage.getItem('user'));
        var response = await fetch("/checkPath", {
            method: "POST",
            headers: {
                'Authorization': 'Bearer ' + dict["token"],
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: cale,
                matrix: JSON.parse(localStorage.getItem("matrix"))
            })
        });

        if (response.ok) {
            var message = await response.json();
            var result = message["result"];
            var msg = "";
            console.log(message);
            if (result === 0) {
                msg = "Calea nu este corecta!";
            } else if (result === 1) {
                msg = "Calea este corecta!";
            }
            else if (result === 2) {
                msg = "Nu toate nodurile sunt conectate intre ele !";
            }
            this.setState({ response: msg });
            if (result !== 2) {
                this.changeColor();
            }
        }
        else {
            window.location.href = '/login';
        }
    }


    randomNumberInRange(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    createGraph(matrix) {
        var l = {
            initial: [],
            final: []
        };
        console.log(matrix);
        var nodes = [];
        var edges = [];
        for (let i = 0; i < matrix.length; i++) {
            nodes.push({
                id: i, title: i.toString(), text: i.toString(), label: "Node " + i.toString(),
                shape: "image", image: "./images/pngaaa.com-11215.png"
            });
            l.initial.push(
                {
                    id: i, text: `Node ${i}`, category: "initial"
                }
            )

            for (let j = i; j < matrix.length; j++) {
                if (matrix[i][j] !== 0) {
                    edges.push(
                        { from: i, to: j, label: matrix[i][j].toString(), color: "black", dashes: [5, 10] }
                    );
                }
            }
        }
        l.final.push(
            {
                id: 0, text: `Start`, category: "final"
            }
        )


        // const styleSheet = document.styleSheets[0];
        // styleSheet.insertRule('.vis-label { color: #ff0000 !important; }', styleSheet.cssRules.length);


        this.setState({ liste: l });
        var graph = { nodes: nodes, edges: edges };
        this.setState({ graph: graph });
        var options = {
            layout: {
                randomSeed: 42,
                improvedLayout: true,
                hierarchical: false
            },
            height: "500px",
            width: "600px",
            nodes: {
                font: {
                    color: "white",
                    size: 12
                }
            },
            edges: {
                arrows: {
                    to: {
                        enabled: false
                    }
                },
                width: 2,
                smooth: {
                    type: 'curvedCW',
                    roundness: 0.2
                },
                font: {
                    size: 13,
                    color: "white", // Set the default label color here
                    background: "transparent",
                    strokeWidth: 0
                }
            },
            physics: {
                enabled: true,
                timestep: 0.3,
                repulsion: {
                    nodeDistance: 20
                },
                minVelocity: 20
            }
        };
        this.setState({ options: options });
    }

    componentWillUnmount() {
        clearInterval(this.intervalId);
        var info = JSON.parse(localStorage.getItem('user'));
        info["time"] = 0;
        localStorage.setItem('user', JSON.stringify(info));
    }

    async componentDidMount() {
        const urlParams = new URLSearchParams(window.location.search);
        const type = urlParams.get('type');
        var n = 0;
        var e = 2;
        console.log(type);
        switch (type) {
            case 'Usor': {
                const min = 3;
                const max = 6;
                n = Math.floor(Math.random() * (max - min + 1) + min);
                break;
            };
            case 'Mediu': {
                const min = 7;
                const max = 15;
                n = Math.floor(Math.random() * (max - min + 1) + min);
                break;
            };
            case 'Greu': {
                const min = 16;
                const max = 30;
                n = Math.floor(Math.random() * (max - min + 1) + min);
                break;
            }
        }
        console.log(n);
        console.log(e);

        this.intervalId = setInterval(() => {
            this.setState(prevState => ({
                currentTime: prevState.currentTime + 1000
            }));
        }, 1000);
        // folosesc text-to-speech ca sa citeasca sectiunea de teorie
        const dict = JSON.parse(localStorage.getItem('user'));
        var matrice = [];
        // console.log(JSON.parse(localStorage.getItem('matrix')));
        if (JSON.parse(localStorage.getItem('matrix')) === null) {
            const response = await fetch("/initialLoad", {
                method: "POST",
                headers: {
                    'Authorization': 'Bearer ' + dict["token"],
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    nodes: n,
                    edges: e
                })
            });

            if (response.ok) {
                var message = await response.json();
                matrice = message["result"];
                console.log(message);
                console.log(message["result"]);
                this.setState({ matrix: message["result"] });
                localStorage.setItem('matrix', JSON.stringify(message["result"]));
                this.createGraph(matrice);
            }
            else {
                console.log(message["message"]);
                window.location.href = '/login';
            }

            // }).then((response) => response.json())
            //     .then((message) => {
            //         matrice = message["result"];
            //         console.log(message);
            //         console.log(message["result"]);                                                                                     
            //         this.setState({ matrix: message["result"] });
            //         localStorage.setItem('matrix', JSON.stringify(message["result"]));
            //         this.createGraph(matrice);
            //     })
        }
        else {
            const m = JSON.parse(localStorage.getItem('matrix'));
            matrice = m;
            this.setState({ matrix: m });
        }
        this.createGraph(matrice);
    }

    async changeColor() {
        var c = [];
        for (let i = 1; i < this.state.liste.final.length; i++) {
            c[i] = this.state.liste.final[i];
        }
        var cale = [];
        for (let i = 1; i < c.length; i++) {
            cale.push(parseInt(c[i]["text"].split(" ")[1]));
        }
        const size = this.state.graph.nodes.length;
        const initial = cloneDeep(this.state.graph);
        const copy = { ...this.state.graph };

        for (let i = 0; i < cale.length - 1; i++) {

            var start = cale[i];
            var finish = cale[i + 1];

            await this.delay(1000);

            var nodes = [];

            if (start < finish) {
                nodes = [
                    ...copy.nodes.slice(0, start),
                    {
                        ...copy.nodes[start], shape: 'image',
                        image: './images/pngfind.com-bee-png-582968.png'
                    },
                    ...copy.nodes.slice(start + 1, finish),
                    { ...copy.nodes[finish] },
                    ...copy.nodes.slice(finish + 1, size),
                ]
            } else {
                nodes = [
                    ...copy.nodes.slice(0, finish),
                    {
                        ...copy.nodes[finish]
                    },
                    ...copy.nodes.slice(finish + 1, start),
                    {
                        ...copy.nodes[start], shape: 'image',
                        image: './images/pngfind.com-bee-png-582968.png'
                    },
                    ...copy.nodes.slice(start + 1, size),
                ]
            }

            var edges = { ...copy.edges };
            var index1 = 0;
            var index2 = 0;
            for (let i = 0; i < this.state.graph.edges.length; i++) {
                if ((edges[i]["from"] === start && edges[i]["to"] === finish)) {
                    index1 = i;
                }
                if (edges[i]["from"] === finish && edges[i]["to"] === start) {
                    index2 = i;
                }
            }

            var e = [];


            if (index2 === 0) {
                e = [
                    ...copy.edges.slice(0, index1),
                    { ...copy.edges[index1], color: 'yellow' },
                    ...copy.edges.slice(index1 + 1, this.state.graph.edges.length)
                ];
            }
            else if (index1 === 0) {
                e = [
                    ...copy.edges.slice(0, index2),
                    { ...copy.edges[index2], color: 'yellow' },
                    ...copy.edges.slice(index2 + 1, this.state.graph.edges.length)
                ];
            }
            else {
                e = [
                    ...copy.edges.slice(0, index1),
                    { ...copy.edges[index1], color: 'yellow' },
                    ...copy.edges.slice(index1 + 1, this.state.graph.edges.length)
                ];

            }


            const updatedGraph = {
                nodes: nodes,
                edges: e,
            };
            this.setState({ graph: updatedGraph });
            await this.delay(1000);
            const nodesWithoutImages = this.state.graph.nodes.map(node => ({ ...node }));
            this.setState({ graph: { nodes: nodesWithoutImages, edges: [] } });
            this.setState({ graph: initial });
            if (i === cale.length - 2) {
                await this.delay(1000);
                nodes = [];
                nodes = [
                    ...copy.nodes.slice(0, finish),
                    {
                        ...copy.nodes[finish], shape: 'image',
                        image: './images/pngfind.com-bee-png-582968.png'
                    },
                    ...copy.nodes.slice(finish + 1, size)
                ]

                const updated = {
                    nodes: nodes,
                    edges: [...initial.edges],
                };
                this.setState({ graph: updated });
                await this.delay(1000);
                const nodesWithoutImg = this.state.graph.nodes.map(node => ({ ...node }));
                this.setState({ graph: { nodes: nodesWithoutImg, edges: [] } });
                this.setState({ graph: initial });
            }
        }
    }

    delay = ms => new Promise(
        resolve => setTimeout(resolve, ms)
    );

    onDragStart = (event, index) => {
        event.dataTransfer.setData('index', index);
    }

    onDragOver = (event) => { event.preventDefault(); }

    onDrop = (event) => {
        const draggedIndex = event.dataTransfer.getData('index');
        var tasks = {
            initial: [],
            final: []
        }
        for (let i = 0; i < this.state.liste.initial.length; i++) {
            tasks.initial.push(this.state.liste.initial[i]);
        }

        for (let i = 0; i < this.state.liste.final.length; i++) {
            tasks.final.push(this.state.liste.final[i]);
        }


        for (let i = 0; i < this.state.liste.initial.length; i++) {
            if (this.state.liste.initial[i]["id"] === parseInt(draggedIndex)) {
                tasks.final.push(
                    {
                        id: tasks.final.length, text: `Node ${this.state.liste.initial[i]["id"]}`, category: "final"
                    }
                )

            }
        }
        this.setState({ liste: tasks });
    }

    handleSubmit = async () => {
        console.log(this.state.doubled);
        var values = this.state.doubled;
        const regex = /[\[\],]/g;
        // perechile vor fi scrise de forma [0,1]-[1,2]
        // facem post la backend pentru a verihica faptul ca exista conexiuni intre toate nodurile din caile scrise
        if (regex.test(values) === false) {
            this.setState({ pairsResponse: "Datele nu au fost introduse corect!" });
            var m = this.state.medals;
            m[GraphImage.index]["chance"] -= 1;
            this.setState({ medals: m });
        }
        else {
            const dictionary = JSON.parse(localStorage.getItem('user'));
            const response = await fetch("/checkNodesConnection", {
                method: "POST",
                headers: {
                    'Authorization': 'Bearer ' + dictionary["token"],
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    values: values,
                    matrix: JSON.parse(localStorage.getItem("matrix"))
                })
            });

            if (response.ok) {
                var message = await response.json();
                var result = message["result"];
                var pairs = message["pairs"];

                if (result === "True") {

                    const result = await fetch("/checkPairs", {
                        method: "POST",
                        headers: {
                            'Authorization': 'Bearer ' + dictionary["token"],
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            pairs: values,
                            matrix: JSON.parse(localStorage.getItem("matrix"))

                        })
                    });
                    if (result.ok) {
                        var message = await result.json();
                        var answer = message["result"];

                        if (answer == "False") {
                            this.setState({ pairsResponse: "Perechile nu sunt bune!" });
                            var m = this.state.medals;
                            m[GraphImage.index]["chance"] -= 1;
                            this.setState({ medals: m });
                        }
                        else {
                            var edges = [...this.state.graph.edges];
                            var dict = {};
                            for (let i = 0; i < pairs.length; i++) {
                                // pairs[i] = o pereche de noduri/ o lista de noduri
                                for (let j = 0; j < pairs[i].length - 1; j++) {
                                    for (let k = 1; k < pairs[i].length; k++) {
                                        for (let a = 0; a < edges.length; a++) {
                                            if (edges[a]["from"] === pairs[i][j] && edges[a]["to"] === pairs[i][k]) {

                                                dict[pairs[i][j] + ", " + pairs[i][k]] = pairs[i][k] + " to " + pairs[i][j];
                                            }
                                            else if (edges[a]["to"] === pairs[i][j] && edges[a]["from"] === pairs[i][k]) {

                                                dict[pairs[i][j] + ", " + pairs[i][k]] = pairs[i][j] + " to " + pairs[i][k];
                                            }
                                        }

                                    }
                                }

                            }
                            for (let key in dict) {
                                var info = dict[key].split(" to ");
                                var from = info[0];
                                var to = info[1];
                                edges.push({ from: parseInt(from), to: parseInt(to), label: this.state.matrix[parseInt(from)][parseInt(to)].toString(), color: "black", dashes: [5, 10] });
                            }
                            var nodes = [...this.state.graph.nodes];
                            this.setState({ graph: { nodes: nodes, edges: edges } });
                            this.setState({ pairsResponse: "Perechile sunt bune!" });
                            this.setState({ answer: true });
                            var m = this.state.medals;
                            m[GraphImage.index]["answer"] = true;
                            this.setState({ medals: m });
                        }
                    }
                    else {
                        console.log(message["message"]);
                        window.location.href = '/login';
                    }
                } else {
                    this.setState({ pairsResponse: "Perechile nu sunt bune!" });
                    var m = this.state.medals;
                    m[GraphImage.index]["chance"] -= 1;
                    this.setState({ medals: m });
                }
            }
            else {
                console.log("Eroare");
                window.location.href = '/login';
            }
        }
    }

    handleClick2 = () => {
        const initial = [...this.state.liste.initial];
        var final = [];
        final.push(
            {
                id: 0, text: `Start`, category: "final"
            }
        );
        this.setState({ liste: { initial: initial, final: final } });
    }

    handleSubmit2 = async () => {
        const dict = JSON.parse(localStorage.getItem('user'));
        const response = await fetch('/getStartingNode',
            {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + dict["token"],
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start: this.state.start,
                    matrix: JSON.parse(localStorage.getItem("matrix"))
                })
            });
        if (response.ok) {
            const data = await response.json();
            if (data["result"] === "True") {
                const copy = { ...this.state.graph };
                const size = this.state.graph.nodes.length;
                const start = parseInt(this.state.start);
                const nodes = [
                    ...copy.nodes.slice(0, start),
                    {
                        ...copy.nodes[start], shape: 'image',
                        image: './images/toppng.com-beehive-clipart-transparent-honey-bee-hive-clip-art-351x432.png'
                    },
                    ...copy.nodes.slice(start + 1, size)
                ];
                const edges = [...copy.edges];
                this.setState({ graph: { nodes: nodes, edges: edges } });
                this.setState({ startNode: "Corect!" });
                var m = this.state.medals;
                m[GraphImage.index]["answer"] = true;
                this.setState({ medals: m });
            } else {
                this.setState({ startNode: "Gresit!" });
                var m = this.state.medals;
                m[GraphImage.index]["chance"] -= 1;
                this.setState({ medals: m });
            }
        } else {
            console.log("Token expirat");
            window.location.href = '/';
        }


    }

    removeLast = () => {
        const i = [...this.state.liste.initial];
        var final = [...this.state.liste.final];
        if (final.length != 1) {
            final.pop();
            this.setState({ liste: { initial: i, final: final } });
        }
        else {
            this.setState({ liste: { initial: i, final: final } });
        }

    }

    clickNext = () => {
        console.log(`intrebare ${GraphImage.index}`);
        if (GraphImage.index <= 2) {
            if (this.state.medals[GraphImage.index]["chance"] < 0) {
                GraphImage.index += 1;
                var show = [...this.state.showHTML];
                for (let i = 0; i < show.length; i++) {
                    show[i] = false;
                }
                show[GraphImage.index] = true;
                this.setState({ showHTML: show });
            }
            else if (this.state.medals[GraphImage.index]["answer"] === true) {
                var img = "";
                if (this.state.medals[GraphImage.index]["chance"] === 3) {
                    img = "./gold-medal.png";
                }
                else if (this.state.medals[GraphImage.index]["chance"] === 2) {
                    img = "./silver-medal.png";
                }
                else {
                    img = "./badge.png";
                }
                var info = JSON.parse(localStorage.getItem('user'));
                info["score"][GraphImage.index] = img;
                localStorage.setItem('user', JSON.stringify(info));

                GraphImage.index += 1;
                var show = [...this.state.showHTML];
                for (let i = 0; i < show.length; i++) {
                    show[i] = false;
                }
                show[GraphImage.index] = true;
                this.setState({ showHTML: show });
            }
            else {
                GraphImage.index += 1;
                var show = [...this.state.showHTML];
                for (let i = 0; i < show.length; i++) {
                    show[i] = false;
                }
                show[GraphImage.index] = true;
                this.setState({ showHTML: show });
            }
        }
    }

    clickPrev = () => {
        this.setState({ start: "" });
        this.setState({ doubled: "" });

        if (GraphImage.index > 0) {
            GraphImage.index -= 1;
            var show = [...this.state.showHTML];
            for (let i = 0; i < show.length; i++) {
                show[i] = false;
            }
            show[GraphImage.index] = true;
            this.setState({ showHTML: show });
        }
    }

    // handleVoice = () => {
    //     fetch("/getText", {
    //         method: "GET"
    //     }).then((response) => response.json())
    //         .then((message) => {
    //             console.log(message["result"]);
    //         });
    // }

    handleFinish = async () => {
        // trimit la backend scorul utilizatorului
        // id-ul va fi extras din token
        var img = "";
        if (this.state.medals[GraphImage.index]["chance"] === 3) {
            img = "./gold-medal.png";
        }
        else if (this.state.medals[GraphImage.index]["chance"] === 2) {
            img = "./silver-medal.png";
        }
        else {
            img = "./badge.png";
        }
        var info = JSON.parse(localStorage.getItem('user'));
        info["score"][GraphImage.index] = img;
        info["time"] = this.state.currentTime;
        localStorage.setItem('user', JSON.stringify(info));
        const dict = JSON.parse(localStorage.getItem('user'));
        const send = await fetch('/finalScore', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + dict["token"],
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                score: dict["score"],
                time: dict["time"]
            })
        });
        if (send.ok) {
            const data = await send.json();
        }
        else {
            console.log("Token expirat");
            window.location.href = '/';
        }
        // golesc matricea si medaliile din score
        localStorage.setItem("matrix", null);
        var info = JSON.parse(localStorage.getItem("user"));
        info["score"] = { 0: "./medal.png", 1: "./medal.png", 2: "./medal.png" };
        info["time"] = 0;
        localStorage.setItem('user', JSON.stringify(info));
        clearInterval(this.intervalId);
        this.intervalId = null;
    }

    renderHTML = () => {
        var tasks = {
            initial: [],
            final: []
        };

        this.state.liste.initial.forEach((t) => {
            tasks[t.category].push(
                <div key={t.id}
                    onDragStart={(event) => this.onDragStart(event, t.id)}
                    draggable>{t.text}</div>
            )
        });

        this.state.liste.final.forEach((t) => {
            tasks[t.category].push(
                <div key={t.id}
                    onDragStart={(event) => this.onDragStart(event, t.id)}
                    draggable>{t.text}</div>
            )
        });

        switch (GraphImage.index) {
            case 1:
                return (
                    <div>
                        <p>Alege punctul de start:</p>
                        <form>
                            <input value={this.state.start}
                                onChange={(e) => this.setState({ start: e.target.value })}></input>
                            <br />
                            <br />
                            <button type='button'
                                onClick={this.handleSubmit2}>Click to submit</button>
                            <p>Result {this.state.startNode}</p>

                        </form>
                    </div>
                );
            case 0:
                return (
                    <div>
                        <p>Ce cai trebuie dublate ?</p>
                        <form>
                            <input value={this.state.doubled}
                                onChange={(e) => this.setState({ doubled: e.target.value })}></input>
                            <button type='button'
                                onClick={this.handleSubmit}>Click to submit</button>
                            <p>Result {this.state.pairsResponse}</p>

                        </form>
                    </div>
                )
            case 2:
                return (
                    <div>
                        <div>
                            <div
                                onDrop={(e) => this.onDrop(e)}>{tasks.initial}</div>
                            <br />
                            <br />
                            <div
                                onDrop={(e) => this.onDrop(e)}
                                onDragOver={(event) => this.onDragOver(event)}>
                                {tasks.final}</div>
                        </div>
                        <br />
                        <br />
                        <br />
                        <br />
                        <button type="button" style={{ padding: "6px 10px", fontSize: "15px" }}
                            onClick={this.handleClick}>Get Response</button>
                        <p>Result {this.state.response}</p>
                        {/* <button type="button" style={{ padding: "6px 10px", fontSize: "15px" }} onClick={this.handleVoice}>Speak</button> */}
                        <br />
                        <button type='button'
                            onClick={this.handleClick2}>Retry</button>
                        <br />
                        <br />
                        <button type='button'
                            onClick={this.removeLast}>Remove last item</button>
                    </div>
                );
        };
    }


    render() {
        const rootStyle = {
            backgroundImage: './4zevar190100149.jpg',
            backgroundRepeat: 'no-repeat',
            backgroundSize: 'cover',
            height: '100vh',
        };
        var info = JSON.parse(localStorage.getItem('user'));
        return (
            <div id="wrapper" style={rootStyle}>
                <div id="first" style={{ position: "relative" }}>
                    <Graph
                        graph={this.state.graph}
                        options={this.state.options}
                    />
                </div >
                <div id="second" style={{ textAlign: "right", marginTop: "0px", right: "-100px", left: "1000px" }}>
                    <p>{new Date(this.state.currentTime).toISOString().substr(11, 8)}</p>
                    <div className="medals">
                        <img src={info["score"][0]} alt="medalie" style={{ height: "40px" }}></img>
                        <img src={info["score"][1]} alt="medalie" style={{ height: "40px" }}></img>
                        <img src={info["score"][2]} alt="medalie" style={{ height: "40px" }}></img>
                    </div>

                    {this.state.showHTML[GraphImage.index] && this.renderHTML()}
                    <br />
                    <div className="button-container">
                        {/* {GraphImage.index !== 0 && <button
                            onMouseEnter={this.handleButtonHover}
                            onClick={this.clickPrev}>Previous</button>} */}

                        {GraphImage.index !== this.state.showHTML.length - 1 && < button
                            onClick={this.clickNext}>Next</button>}
                        <button type='button' onClick={this.handleFinish}>Finish</button>

                    </div>

                </div>

            </div >
        )
    }
}

export default GraphImage;

