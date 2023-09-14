import React from 'react';
import "./style.css";


class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isLogged: false,
      popupOpen: false,
      nodes: "",
      edges: 2,
      selectedOption: '',
      selectedCity: '',
      options: [],
      cities: [],
      errorText: '',
      showPopup: false,
      done: true,
      color: "#0f553e",
      visible: false
    };

    this.openModal = this.openModal.bind(this);
    this.closeModal = this.closeModal.bind(this);
    this.handleOptionChange = this.handleOptionChange.bind(this);
    this.handleCityChange = this.handleCityChange.bind(this);

  }

  handleOptionChange(event) {
    this.setState({errorText: ''});
    this.setState({ selectedOption: event.target.value });
  }

  async handleCityChange(event) {
    this.setState({errorText: ''});
    this.setState({ visible: true });
    this.setState({ color: "#0f553e" });

    console.log(event.target.value);
    this.setState({ selectedCity: event.target.value });
    console.log("trimit " + event.target.value);
    const response = await fetch(`/api/neighbourhoods?city=${encodeURIComponent(event.target.value)}`,
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
      var options = [];
      options.push({
        value: '',
        label: '--Alegeți zona--'
      })

      const response2 = await fetch('/api/users/neighbourhoods', {
        method: 'GET',
        headers: {
          'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
          'Content-Type': 'application/json'
        }
      });
      if (response2.ok) {
        var msg = await response2.json();
        var check = msg['response'];
        console.log(check);
        if (check === 0) {
          this.setState({ showPopup: true });
          this.setState({ done: false });
          this.setState({ color: "gray" })
          this.setState({ visible: false });
        }
        else {
          this.setState({ done: true });
        }
      } else if (response.status === 401) {
        localStorage.removeItem("user");
        window.location.href = '/login'
      }
      for (var value in data['response']) {
        options.push({
          value: data['response'][value],
          label: data['response'][value]
        })
      }
      this.setState({ options: options });
    } else if (response.status === 401) {
      localStorage.removeItem("user");
      window.location.href = '/login'
    }

  }

  openModal() {
    this.setState({ popupOpen: true });
  }

  closeModal() {
    this.setState({ popupOpen: false });
  }

  closePopup() {
    this.setState({ showPopup: false });
  }


  async componentDidMount() {
    if (localStorage.getItem('user') === null) {
      this.setState({ isLogged: false });
    } else {
      this.setState({ isLogged: true });
      this.setState({ color: 'gray' });
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

  }

  handleFinish = async () => {
    const response = await fetch('/api/users/neighbourhoods', {
      method: 'PUT',
      headers: {
        'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
        'Content-Type': 'application/json'
      }
    });
    if (response.ok) {
      var message = await response.json();
      console.log(message['response']);
      this.setState({ done: true });
      this.closePopup();
      window.location.reload();
    }
    else if (response.status === 401) {
      localStorage.removeItem("user");
      window.location.href = '/login'
    }
  }

  handleClick = (event) => {
    event.preventDefault();
    console.log(event.target.textContent);
    const url = `/game?type=${encodeURIComponent(event.target.textContent)}`;
    window.location.href = url;
  };

  checkAvailable = async () => {
    if (this.state.selectedOption === '') {
      this.setState({ errorText: 'Alegeți un cartier !' });
    }
    else {
      const response2 = await fetch('/api/users/neighbourhoods',
        {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ zona: this.state.selectedOption, oras: this.state.selectedCity })
        }
      );
      if (response2.ok) {
        const msg2 = await response2.json();
        console.log(msg2["response"]);
        const search = `${this.state.selectedCity}, ${this.state.selectedOption}`
        const url = `/map?zona=${encodeURIComponent(search)}`;
        window.location.href = url;
      } else if (response2.status === 401) {
        localStorage.removeItem("user");
        window.location.href = '/login'
      }
    }
  }


  render() {
    return (
      <div className='homeContainer' style={{ textAlign: "center", height: '90vh', width: '100vw' }} >
        <div className="popup">
          {this.state.showPopup ? (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              <div className="popup_inner" style={{
                marginTop: '10px',
                textAlign: 'center',
                width: "320px",
                height: "100px",
                backgroundColor: "black",
                borderRadius: "10px",
                padding: "10px",
                color: "white",
                fontSize: '7px',

              }}>
                <h1>Nu ați marcat terminarea zonei anterioare</h1>
                <button onClick={this.handleFinish} style={{ color: 'white' }}>Încheiat</button>
              </div>
            </div>
          ) : null}
        </div>
        <br />
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}>
          {this.state.isLogged &&
            <div
              style={{
                marginTop: '90px',
                textAlign: 'center',
                width: "300px",
                height: "290px",
                backgroundColor: "black",
                borderRadius: "10px",
                padding: "20px",
                color: "white"
              }}
            >

              <br />
              <label htmlFor="dropdown" style={{ color: 'white' }}>Alegeți orașul:</label>
              <br />
              <br />
              <select id="dropdown" value={this.state.selectedCity} onChange={this.handleCityChange} style={{
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
              <br />
              <br />

              <label htmlFor="dropdown2" style={{ color: 'white' }}>Alegeți un cartier</label>
              <br />
              <br />
              <select id="dropdown2" value={this.state.selectedOption} onChange={this.handleOptionChange} style={{
                padding: "3px",
                fontSize: "13px",
                backgroundColor: this.state.color,
                border: "none",
                borderRadius: "4px",
                boxShadow: "none",
                outline: "none",
                width: "120px",
                color: 'white',

              }} disabled={!this.state.visible}>
                {this.state.options.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <br />
              <p>Ați ales: <b><i>{this.state.selectedCity}, {this.state.selectedOption}</i></b></p>
              <p style={{color:'red', fontSize: '12px'}}>{this.state.errorText}</p>
              <button style={{ backgroundColor: this.state.color, color: 'white' }} onClick={this.checkAvailable} disabled={!this.state.visible}>Traseu</button>
            </div>
          }

          {!this.state.isLogged &&
            <div
              style={{
                marginTop: '20px',
                textAlign: 'center',
                width: "500px",
                height: "70px",
                backgroundColor: "black",
                borderRadius: "10px",
                padding: "20px",
                color: "white",
              }}
            >
              <p>Optimizarea traseului unei mașini de salubrizare.</p>
            </div>
          }

        </div>
      </div>
    )
  }
}
export default Home;
