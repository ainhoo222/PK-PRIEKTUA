import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [isRegister, setIsRegister] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [message, setMessage] = useState('')
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [role, setRole] = useState(localStorage.getItem('role') || '')
  const [currentView, setCurrentView] = useState('profile')
  const [userData, setUserData] = useState({})

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const fetchProfile = async () => {
    try {
      const response = await axios.get('http://localhost:5000/profile', {
        headers: { Authorization: token }
      })
      setUserData(response.data)
    } catch (error) {
      console.error('Error fetching profile:', error)
    }
  }

  useEffect(() => {
    if (token) {
      fetchProfile()
    }
  }, [token])

  const handleRegister = async (e) => {
    e.preventDefault()
    try {
      const response = await axios.post('http://localhost:5000/register', formData)
      setMessage('Erabiltzailea ongi erregistratu da')
    } catch (error) {
      setMessage(error.response?.data?.message || 'Errorea erregistratzean')
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const response = await axios.post('http://localhost:5000/login', {
        username: formData.username,
        password: formData.password
      })
      setToken(response.data.token)
      setRole(response.data.role)
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('role', response.data.role)
      const roleText = response.data.role === 'user' ? 'Erabiltzaile' : 'Administratzaile'
      setMessage(`${roleText} gisa hasi duzu saioa`)
    } catch (error) {
      setMessage(error.response?.data?.message || 'Errorea saioa hastean')
    }
  }

  const handleLogout = () => {
    setToken('')
    setRole('')
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setMessage('Saioa amaitu da')
  }

  if (token) {
    return (
      <div className="app app-logged">
        <img src="/Streamix logo.png" alt="Streamix Logo" className="logo" />
        <div className="navbar">
          <button onClick={() => setCurrentView('profile')} className={currentView === 'profile' ? 'active' : ''}>Nire Profila</button>
          <button onClick={() => setCurrentView('movies')} className={currentView === 'movies' ? 'active' : ''}>Filmak</button>
          <button onClick={() => setCurrentView('favorites')} className={currentView === 'favorites' ? 'active' : ''}>Gogokoenak</button>
          <button onClick={() => setCurrentView('watched')} className={currentView === 'watched' ? 'active' : ''}>Ikusitakoak</button>
        </div>
        <div className="content">
          {currentView === 'profile' && (
            <div className="profile">
              <h2>Nire Profila</h2>
              <p><strong>Erabiltzaile-izena:</strong> {userData.username}</p>
              <p><strong>Helbide elektronikoa:</strong> {userData.email}</p>
              <p><strong>Rola:</strong> {role === 'user' ? 'Erabiltzaile' : 'Administratzaile'}</p>
              <button className="logout-btn" onClick={handleLogout}>Saioa amaitu</button>
            </div>
          )}
          {currentView === 'movies' && (
            <div className="movies">
              <h2>Filmak</h2>
              <p>Hemen filmak zerrenda agertuko da.</p>
              {/* Placeholder para lista de películas */}
            </div>
          )}
          {currentView === 'favorites' && (
            <div className="favorites">
              <h2>Gogokoenak</h2>
              <p>Zure gogoko filmak hemen.</p>
            </div>
          )}
          {currentView === 'watched' && (
            <div className="watched">
              <h2>Ikusitakoak</h2>
              <p>Ikusitako filmak zerrenda.</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="app app-login">
      <img src="/Streamix logo.png" alt="Streamix Logo" className="logo" />
      <div className="tabs">
        <button onClick={() => setIsRegister(false)} className={!isRegister ? 'active' : ''}>Saioa hasi</button>
        <button onClick={() => setIsRegister(true)} className={isRegister ? 'active' : ''}>Erregistratu</button>
      </div>
      {isRegister ? (
        <form onSubmit={handleRegister}>
          <input type="text" name="username" placeholder="Erabiltzaile-izena" value={formData.username} onChange={handleChange} required />
          <input type="email" name="email" placeholder="Helbide elektronikoa" value={formData.email} onChange={handleChange} required />
          <input type="password" name="password" placeholder="Pasahitza" value={formData.password} onChange={handleChange} required />
          <button type="submit">Erregistratu</button>
        </form>
      ) : (
        <form onSubmit={handleLogin}>
          <input type="text" name="username" placeholder="Erabiltzaile-izena" value={formData.username} onChange={handleChange} required />
          <input type="password" name="password" placeholder="Pasahitza" value={formData.password} onChange={handleChange} required />
          <button type="submit">Saioa hasi</button>
        </form>
      )}
      {message && <p>{message}</p>}
    </div>
  )
}

export default App
