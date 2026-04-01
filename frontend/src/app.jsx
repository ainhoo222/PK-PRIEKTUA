import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [isRegister, setIsRegister] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user'
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
      setMessage(response.data.message)
    } catch (error) {
      setMessage(error.response?.data?.message || 'Error registering')
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
      setMessage(`Logged in as ${response.data.role}`)
    } catch (error) {
      setMessage(error.response?.data?.message || 'Error logging in')
    }
  }

  const handleLogout = () => {
    setToken('')
    setRole('')
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setMessage('Logged out')
  }

  if (token) {
    return (
      <div className="app">
        <h1>Streamix</h1>
        <p>Welcome! You are logged in as {role}.</p>
        <button onClick={handleLogout}>Logout</button>
        {/* Here add movie list or admin panel */}
      </div>
    )
  }

  return (
    <div className="app">
      <h1>Streamix</h1>
      <div className="tabs">
        <button onClick={() => setIsRegister(false)} className={!isRegister ? 'active' : ''}>Login</button>
        <button onClick={() => setIsRegister(true)} className={isRegister ? 'active' : ''}>Register</button>
      </div>
      {isRegister ? (
        <form onSubmit={handleRegister}>
          <input type="text" name="username" placeholder="Username" value={formData.username} onChange={handleChange} required />
          <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} required />
          <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required />
          <select name="role" value={formData.role} onChange={handleChange}>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <button type="submit">Register</button>
        </form>
      ) : (
        <form onSubmit={handleLogin}>
          <input type="text" name="username" placeholder="Username" value={formData.username} onChange={handleChange} required />
          <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required />
          <button type="submit">Login</button>
        </form>
      )}
      {message && <p>{message}</p>}
    </div>
  )
}

export default App
