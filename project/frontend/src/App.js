import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './Home';
import Login from './Login';
import Register from './Register';
import MapComponent from './MapComponent';
import AddNeighbourhood from './AddNeighbourhood';
import React, { useEffect } from 'react';

function App() {
    useEffect(() => {
        document.title = 'Route Ranger';
    }, []);
    return (
        <Router>
            <Navbar />
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/map" element={<MapComponent />} />
                <Route path="/management" element={<AddNeighbourhood />} />
            </Routes>
        </Router>
    );
}

export default App;
