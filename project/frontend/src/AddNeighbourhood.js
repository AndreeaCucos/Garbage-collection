import React from 'react';
import './style.css';

class AddNeighbourhood extends React.Component {
    constructor() {
        super();
        this.state = {
            cartier: '',
            cartiere: [],
            cities: [],
            selectedCity: '',
            selectedOption: '',
            colorOras: 'gray',
            colorcartier: 'gray',
            readCity: false,
            readCartier: false,
            oras: '',
            errorCheckOras: false,
            errorCheckCartier: false,
            distanceTop: 0,
            errorMsg: ''
        }
        this.handleCityChange = this.handleCityChange.bind(this);
        this.handleOptionChange = this.handleOptionChange.bind(this);


    }

    checkStringOras = (string) => {
        const regex = /^[a-zA-Z]+$/;
        return regex.test(string);
    };

    checkStringCartier = (string) => {
        const regex = /^[a-zA-Z\s]+$|^[a-zA-Z][a-zA-Z0-9\s]+$|^[a-zA-Z0-9][a-zA-Z\s]*$/;
        return regex.test(string);
    };

    handleOptionChange(event) {
        console.log(event.target.value);
        this.setState({ errorCheckOras: false });
        this.setState({ errorCheckCartier: false });
        this.setState({ selectedOption: event.target.value });
        if (event.target.value === 'cartier') {
            this.setState({ colorcartier: 'white' });
            this.setState({ colorOras: 'gray' });

            this.setState({ readCartier: true });
            this.setState({ readCity: false });
        }
        else if (event.target.value === 'oras') {
            this.setState({ colorcartier: 'gray' });
            this.setState({ colorOras: 'white' });
            this.setState({ readCity: true });
            this.setState({ readCartier: false });
        }
    }

    removeDiacritics(name) {
        return name.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    async handleCityChange(event) {
        this.setState({ errorCheckOras: false });
        this.setState({ errorCheckCartier: false });
        this.setState({ visible: true });
        this.setState({ color: "#0f553e" });
        this.setState({ errorMsg: '' });
        console.log(event.target.value);
        this.setState({ selectedCity: event.target.value });
        console.log("trimit " + event.target.value);
        const response = await fetch(`/api/neighbourhoods/${encodeURIComponent(event.target.value)}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                    'Content-Type': 'application/json'
                }
            });
        if (response.ok) {
            const data = await response.json();
            console.log(data);
            const names = [];
            for (var value in data['response']) {
                names.push(data['response'][value]);
            }
            this.setState({ cartiere: names });
            console.log(names);
        } else if (response.status === 401) {
            localStorage.removeItem("user");
            window.location.href = '/login'
        }

    }

    async componentDidMount() {
        const ans = await fetch('/api/cities',
            {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                    'Content-Type': 'application/json'
                }
            });
        if (ans.ok) {
            const data = await ans.json();
            console.log(data['response']);
            var cities = [];
            cities.push({
                value: '',
                label: '--Alegeți orașul--'
            });
            for (var value in data['response']) {
                cities.push({
                    value: data['response'][value],
                    label: data['response'][value]
                })
            }
            this.setState({ cities: cities });
        } else if (ans.status === 401) {
            localStorage.removeItem("user");
            window.location.href = '/login'
        }
    }

    handleAdd = async () => {
        if (this.state.selectedOption === 'cartier') {
            const cartier = this.removeDiacritics(this.state.cartier);
            if (this.state.selectedCity === '') {
                this.setState({ errorMsg: 'Trebuie să alegeți un oraș!' });
            }
            else {
                if (this.checkStringCartier(cartier) === false) {
                    this.setState({ errorMsg: 'Denumirea cartierului poate conține doar litere și cifre!' });
                }
                
                else {
                    this.setState({ errorMsg: '' });
                    const resp = await fetch('/api/neighbourhoods', {
                        method: 'POST',
                        headers: {
                            'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ zona: cartier, oras: this.removeDiacritics(this.state.selectedCity) })
                    });
                    if (resp.ok) {
                        window.location.reload();
                    } else if (resp.status === 409) {
                        this.setState({ errorMsg: "Cartierul există deja în listă!" });
                        this.setState({ errorCheckCartier: true });
                        this.setState({ distanceTop: '-50%' });
                    } else if (resp.status === 404) {
                        var msg = await resp.json();
                        this.setState({ errorMsg: msg["error"] });
                        this.setState({ errorCheckCartier: true });
                    } else if (resp.status === 401) {
                        localStorage.removeItem("user");
                        window.location.href = '/login'
                    }
                }
            }
        }
        else {
            const oras = this.removeDiacritics(this.state.oras);
            console.log(oras);
            if (this.checkStringOras(oras) === false) {
                // sirul contine cifre deci este incorect
                this.setState({ errorMsg: 'Denumirea poate conține doar litere!' });
            }
            else {
                const resp = await fetch('/api/cities', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ oras: oras })
                });
                if (resp.ok) {
                    window.location.reload();
                } else if (resp.status === 409) {
                    this.setState({ errorMsg: 'Orașul există deja în listă!' });
                    this.setState({ errorCheckOras: true });
                    this.setState({ distanceTop: '60%' });
                    console.log("incalcare unique");
                } else if (resp.status === 404) {
                    this.setState({ errorMsg: 'Orașul nu există!' });
                    this.setState({ errorCheckOras: true });
                } else if (resp.status === 401) {
                    localStorage.removeItem("user");
                    window.location.href = '/login'
                }
            }
        }
    }

    handleDelete = async () => {
        if (this.state.selectedOption === 'cartier') {
            if (this.state.selectedCity === '') {
                this.setState({ errorMsg: 'Trebuie să alegeți un oraș!' });
            }
            else {
                const cartier = this.removeDiacritics(this.state.cartier);
                if (this.checkStringCartier(cartier) === false) {
                    this.setState({ errorMsg: 'Denumirea cartierului poate conține doar litere și cifre!' });
                }
                else {
                    const city = this.removeDiacritics(this.state.selectedCity);
                    const resp = await fetch(`/api/neighbourhoods/${encodeURIComponent(city)}/${encodeURIComponent(cartier)}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                            'Content-Type': 'application/json'
                        }
                    });
                    if (resp.ok) {
                        window.location.reload();
                    } else if (resp.status === 404) {
                        const msg = await resp.json();
                        console.log(msg['error']);
                        this.setState({ errorMsg: 'Cartierul nu există în orașul selectat!' });
                    } else if (resp.status === 401) {
                        localStorage.removeItem("user");
                        window.location.href = '/login';
                    }
                }
            }

        } else if (this.state.selectedOption === 'oras') {
            const city = this.removeDiacritics(this.state.oras);

            if (this.checkStringOras(city) === false) {
                this.setState({ errorMsg: 'Denumirea poate conține doar litere!' });
            }
            else {
                const resp = await fetch(`/api/cities/${encodeURIComponent(city)}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
                        'Content-Type': 'application/json'
                    }
                });
                if (resp.ok) {
                    window.location.reload();
                } else if (resp.status === 404) {
                    this.setState({ errorMsg: 'Denumirea orașului nu există!' });
                } else if (resp.status === 401) {
                    localStorage.removeItem("user");
                    window.location.href = '/login'
                }
            }
        }

    }

    render() {
        var options = {
            ALLOWED_TAGS: [], // Lista goală de etichete HTML permise
          };

        return (
            <div style={{
                textAlign: "center", height: '90vh', width: '100vw',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
            }}>

                <div style={{
                    textAlign: 'center',
                    width: "750px",
                    height: "450px",
                    backgroundColor: "black",
                    borderRadius: "10px",
                    padding: "20px",
                    color: "white",
                }}>
                    <div style={{ display: 'flex', justifyContent: 'center', fontSize: '13px' }}>
                        <div>
                            <br />
                            <label htmlFor="second-dropdown" style={{ color: 'white' }}>Alegeți orașul:&nbsp;  </label>
                            <select id="second-dropdown" value={this.state.selectedCity} onChange={this.handleCityChange} style={{
                                padding: "3px",
                                fontSize: "13px",
                                backgroundColor: "#0f553e",
                                border: "none",
                                borderRadius: "4px",
                                boxShadow: "none",
                                outline: "none",
                                width: "120px",
                                color: 'white'
                            }}>
                                {this.state.cities.map(option => (
                                    <option key={option.value} value={option.value}>{option.label}</option>
                                ))}
                            </select>
                        </div>
                        <div style={{ marginLeft: '40px' }}>
                            <br />
                            <label htmlFor="first-dropdown">Alege:&nbsp; </label>
                            <select id="first-dropdown" value={this.state.options} onChange={this.handleOptionChange} style={{
                                padding: "3px",
                                fontSize: "13px",
                                backgroundColor: "#0f553e",
                                border: "none",
                                borderRadius: "4px",
                                boxShadow: "none",
                                outline: "none",
                                width: "120px",
                                color: 'white',

                            }}>
                                <option value={''}>--opțiune--</option>
                                <option value={'cartier'}>cartier</option>
                                <option value={'oras'}>oraș</option>
                            </select>
                        </div>
                        <br />
                        <br />
                    </div>

                    <br />
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <div style={{ marginTop: '40px' }}>
                            <div style={{ height: '200px', width: '200px', border: '1px solid black', overflowY: 'scroll', backgroundColor: '#fff', color: 'black' }}>
                                {this.state.cartiere.map(name => (
                                    <div key={name}>{name}</div>
                                ))}
                            </div>
                        </div>
                        <div style={{ marginLeft: '60px', fontSize: '14px' }}>
                            <div className='add-text' style={{ marginLeft: '30px', color: this.state.colorcartier }}>
                                
                                <div style={{ color: this.state.colorOras }}>
                                    <p>Orașe:</p>
                                    <div style={{ display: 'flex', position: 'relative' }}>
                                        <div>
                                            <label style={{ fontSize: '14px' }}>
                                                Introduceți numele orașului:&nbsp;
                                                <input
                                                    id="city"
                                                    type="text"
                                                    value={this.state.oras}
                                                    readOnly={!this.state.readCity}
                                                    onChange={(e) => this.setState({ oras: e.target.value })}
                                                />
                                            </label>
                                        </div>
                                    </div>
                                    <br />
                                </div>
                                <br />

                                <p>Cartiere:</p>
                                <div style={{ display: 'flex' }}>
                                    <div>
                                        <label style={{ fontSize: '14px' }}>
                                            Introduceți numele cartierului:&nbsp;
                                            <input
                                                id="cartier"
                                                type="text"
                                                value={this.state.cartier}
                                                readOnly={!this.state.readCartier}
                                                onChange={(e) => this.setState({ cartier: e.target.value })}
                                            />

                                        </label>
                                    </div>
                                </div>
                                <br />
                                <br />

                                <div style={{ display: 'flex' }}>
                                    <button style={{ color: 'white', fontSize: '12px' }} onClick={this.handleAdd}>Adaugă</button>
                                    <button style={{ color: 'white', marginLeft: '10px', fontSize: '12px' }} onClick={this.handleDelete}>Șterge</button>
                                </div>
                                <p style={{ color: 'red' }}>{this.state.errorMsg}</p>

                            </div>
                        </div>

                    </div>
                </div>
            </div >
        );
    }
}
export default AddNeighbourhood;