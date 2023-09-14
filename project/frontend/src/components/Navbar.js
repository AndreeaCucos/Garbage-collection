import React, { useState } from 'react';
import { Link } from "react-router-dom";
import './Navbar.css';


function DropdownMenu({ isLogged, isAdmin, handleLogout, deleteAccount}) {
  const info = JSON.parse(localStorage.getItem('user'));
  let height, width;

  if (isLogged) {
    if (isAdmin) {
      height = "30%";
      width = "15%";
    } else {
      height = "24%";
      width = "13%";
    }
  } else {
    height = "13%";
    width = "13%";
  }

  return (
    <div className="dropdown-menu" style={{ width, height }}>
      {isLogged && !isAdmin &&
        <div>
          <p className='dropdown-text'>Autentificat drept: <b>{info["username"]}</b></p>
          <hr/>
          <button onClick={handleLogout} style={{ width: '90px', height: '10px', color: 'black', fontSize:'12px',backgroundColor:'#e0dfdf'}}>Deconectare</button>
          <hr/>
          <button onClick={deleteAccount} style={{ width: '100px',  height: '10px', color: 'black', fontSize:'12px', backgroundColor:'#e0dfdf'}}>Șterge contul</button>
        </div>
      }

      {isLogged && isAdmin &&
        <div>
          <p className='dropdown-text'>Autentificat drept <span style={{ color: 'red' }}><b>administrator</b></span>: <b>{info["username"]}</b></p>
          <hr/>
          <a href='/management' style={{color:'black',  fontSize:'12px'}}>Management</a>
          <hr/>
          <button onClick={handleLogout} style={{ width: '90px', height: '10px', color: 'black', fontSize:'12px',backgroundColor:'#e0dfdf'}}>Deconectare</button>
          <hr/>
          <button onClick={deleteAccount} style={{ width: '200px',  height: '10px', color: 'black', fontSize:'12px', backgroundColor:'#e0dfdf'}}>Șterge contul</button>
        </div>
      }

      {isLogged === false && (
        <div>
          <p className='dropdown-text'>Accesați contul:</p>
          <a href="/login" style={{color:'red', textDecoration: 'underline', fontSize:'13px'}}>Autentificați-vă</a>
        </div>
      )}
    </div>
  );
}

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLogged, setIsLogged] = useState(false);
  const [isLoggedOut, setLoggedOut] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);


  const toggleDropdown = () => {
    setIsOpen(!isOpen);
    console.log(isLogged);
    console.log(isLoggedOut);
    console.log(localStorage.getItem('user'));
    if (localStorage.getItem('user') == null) {
      setLoggedOut(true);
      setIsLogged(false);
    }
    else {
      setIsLogged(true);
      setLoggedOut(false);
      checkRole();
    }
  };

  const handleLogout = async (event) => {
    event.preventDefault();
    // trimit informatiile la backend
    const dict = JSON.parse(localStorage.getItem('user'));
    const response = await fetch('/api/logout', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + dict["token"],
        'Content-Type': 'application/json'
      }
    });
    if (response.ok) {
      const data = await response.json();
      console.log(data);
      localStorage.removeItem("user");
      window.location.href = '/login';
    } else if (response.status === 401) {
      localStorage.removeItem("user");
      window.location.href = '/login';
    }
  };

  const checkRole = () => {
    fetch('/api/users', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
        'Content-Type': 'application/json'
      }
    }).then(response => 
      {
        if(!response.ok)
        {
          throw new Error('expirat');
        }
        return response.json()
      }
      )
      .then(message => {
        const role = message['response'];
        if (role === 'admin') {
          setIsAdmin(true);
        }
      }).catch(error => {
        console.log('expirat');
        localStorage.removeItem("user");
        window.location.href = '/login';
      });
  }

  const deleteAccount = async () => {
    const response = await fetch('/api/users',
      {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('user'))["token"],
          'Content-Type': 'application/json'
        }
      });
    if (response.ok) {
      setIsLogged(false);
      setLoggedOut(true);
      localStorage.removeItem("user");
      window.location.reload();
      window.location.href = '/';
    } 
    else if (response.status === 401)
    {
      localStorage.removeItem("user");
      window.location.href = '/login'
    }
  }


  return (
    <nav>
      <ul>
        <li>
          <Link to="/">
            <img src="./home_icon.png" alt="home" style={{ float: 'left', height: "23px", padding: '4px', marginTop: '10px', marginLeft: '8px'}} />
          </Link>
        </li>
        <li className="nav-text"><b><i>Route Ranger</i></b></li>
        <li>
          <img src="./avatar.png" alt="account" onClick={toggleDropdown} style={{ height: "23px", float: "right", marginTop: '-18px', marginBottom: '16px', marginRight: '14px' }} />
          {isOpen && (
            <DropdownMenu
              isLogged={isLogged}
              isAdmin={isAdmin}
              handleLogout={handleLogout}
              deleteAccount={deleteAccount}
            />
          )}
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
