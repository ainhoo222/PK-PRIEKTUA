import { useState } from 'react'
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

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

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
      <div className="app">
        <img src="/Streamix logo.png" alt="Streamix Logo" className="logo" />
        <div className="welcome">
          <p>Ongi etorri! {role === 'user' ? 'Erabiltzaile' : 'Administratzaile'} gisa hasi duzu saioa.</p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>Saioa amaitu</button>
        {/* Here add movie list or admin panel */}
      </div>
    )
  }

  return (
    <div className="app">
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
