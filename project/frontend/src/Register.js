import React, { useState } from 'react';

const Register = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [email, setEmail] = useState("");

    const handleSubmit = async (event) => {
        event.preventDefault();
        // trimit informatiile la backend
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, email })
        });
        if (response.ok) {
            const data = await response.json();
            window.location.href = '/login';
        } else {
            var msg = await response.json();
            if (response.status === 409) {
                setError("Denumirea utilizatorului există deja!");
            } else if (response.status === 400) {
                if (msg["error"] === 'Email') {
                    setError("Formatul adresei de email este greșită!");
                }
                else if (msg["error"] === 'Username') {
                    setError("Format numelui este greșit!");
                }
            }
        }
    };


    return (
        <div style={{
            marginTop: '50px',
            textAlign: 'center',
            width: "300px",
            height: "200px",
            backgroundColor: "black",
            borderRadius: "10px",
            padding: "20px",
            color: "white",
            marginLeft: '470px'
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
                <label>
                    Email:&nbsp;
                    <input
                        type="text"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </label>
                <br />
                <br />
                <br />
            
                <button type="submit" style={{color:'white', width: '100px'}}>Crează contul</button>
                <p style={{ color: 'red', fontSize: '11px' }}>{error}</p>
            </form>
        </div>
    );
}
export default Register;