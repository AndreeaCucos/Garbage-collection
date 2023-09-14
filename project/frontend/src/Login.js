import React, { useState } from 'react';

const Login = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [errorMsg, setErrorMsg] = useState("");

    const handleSubmit = async (event) => {
        event.preventDefault();
        // trimitem informațiile la backend
        console.log(`username: ${username}, password: ${password}`)
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (response.ok) {
            const data = await response.json();
            console.log(data);
            const info = {
                "username": username,
                "token": data.response,
            };
            localStorage.setItem('user', JSON.stringify(info));
            window.location.href = '/';
        }
        else if (response.status === 401) {
            setErrorMsg("Parolă greșită.");
        }
        else if (response.status === 404) {
            setErrorMsg("Numele utilizatorului nu există.")
        }
    };

    return (
        <div
            style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
            }}>
            <div style={{
                marginTop: '90px',
                textAlign: 'center',
                width: "300px",
                height: "240px",
                backgroundColor: "black",
                borderRadius: "10px",
                padding: "20px",
                color: "white",
            }}>
                <form onSubmit={handleSubmit} style={{fontSize:'14px'}}>
                    <label>
                        Nume:&nbsp;
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </label>
                    <br />
                    <br />
                    <label>
                        Parolă:&nbsp;
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </label>
                    <br />
                    <br />
                    <p style={{ color: 'red', padding: '0px', fontSize: '14px' }}>{errorMsg}</p>
                    <button type="submit" onClick={handleSubmit} style={{ color: 'white', width:'100px' }}>Autentificare</button>
                </form>
                <br />
                <div style={{display: 'flex', justifyContent: 'center', marginTop:'30px', fontSize:'13px'}}>
                    <p>Nu aveți cont?</p>
                    <a href='/register' style={{ color: 'red', marginTop:'14px', marginLeft:'10px' }}>Înscrieți-vă</a>
                </div>

            </div>
        </div>
    );
}
export default Login;