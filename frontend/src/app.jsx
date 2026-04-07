import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [isRegister, setIsRegister] = useState(false)
  const [formData, setFormData] = useState({ username: '', email: '', password: '' })
  const [message, setMessage] = useState('')
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [role, setRole] = useState(localStorage.getItem('role') || '')
  const [currentView, setCurrentView] = useState('profile')
  const [userData, setUserData] = useState({})
  const [movies, setMovies] = useState([])
  const [favorites, setFavorites] = useState([])
  const [newMovie, setNewMovie] = useState({ title: '', description: '' })
  const [searchTerm, setSearchTerm] = useState('')

  const fetchProfile = async () => {
    try {
      const res = await axios.get('http://localhost:5000/profile', { headers: { Authorization: token } })
      setUserData(res.data); setRole(res.data.role)
    } catch (e) { console.error(e) }
  }

  const fetchMovies = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/movies')
      setMovies(res.data)
    } catch (e) { console.error(e) }
  }

  const fetchFavorites = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/favorites', { headers: { Authorization: token } })
      setFavorites(res.data)
    } catch (e) { console.error(e) }
  }

  useEffect(() => {
    if (token) {
      fetchProfile(); fetchMovies(); fetchFavorites()
    }
  }, [token])

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const res = await axios.post('http://localhost:5000/login', { username: formData.username, password: formData.password })
      setToken(res.data.token); setRole(res.data.role)
      localStorage.setItem('token', res.data.token); localStorage.setItem('role', res.data.role)
      setCurrentView('profile')
    } catch (e) { setMessage('Errorea saioa hastean') }
  }

  const handleAddMovie = async (e) => {
    e.preventDefault()
    try {
      await axios.post('http://localhost:5000/api/movies', newMovie)
      setNewMovie({ title: '', description: '' }); fetchMovies()
      setMessage('Filma ongi gehitu da!')
    } catch (e) { console.error(e) }
  }

  const handleDeleteMovie = async (id) => {
    if (window.confirm("Ziur zaude pelikula hau guztiz ezabatu nahi duzula?")) {
      await axios.delete(`http://localhost:5000/api/movies/${id}`)
      fetchMovies(); fetchFavorites()
    }
  }

  const handleAddFavorite = async (movieId) => {
    try {
      await axios.post('http://localhost:5000/api/favorites', { movie_id: movieId }, { headers: { Authorization: token } })
      fetchFavorites(); alert("Gogokoetara gehituta!")
    } catch (e) { console.error(e) }
  }

  const handleRemoveFavorite = async (movieId) => {
    try {
      await axios.delete(`http://localhost:5000/api/favorites/${movieId}`, { headers: { Authorization: token } })
      fetchFavorites()
    } catch (e) { console.error(e) }
  }

  const handleLogout = () => {
    setToken(''); setRole(''); localStorage.clear(); setCurrentView('profile')
  }

  if (token) {
    return (
      <div className="app app-logged">
        <div className="navbar">
          <button onClick={() => setCurrentView('profile')}>Profila</button>
          <button onClick={() => setCurrentView('movies')}>Filmak</button>
          <button onClick={() => {fetchFavorites(); setCurrentView('favorites')}}>Gogokoenak</button>
        </div>

        <div className="content">
          {currentView === 'profile' && (
            <div className="profile">
              <h2>Nire Profila</h2>
              <p>Kaixo, <strong>{userData.username}</strong></p>
              <p>Rola: {role === 'admin' ? 'Administratzailea' : 'Erabiltzailea'}</p>
              <button onClick={handleLogout} className="logout-btn">Saioa amaitu</button>
            </div>
          )}

          {currentView === 'movies' && (
            <div className="movies">
              {(role === 'admin') && (
                <div className="admin-box">
                  <h3>Gehitu Filma</h3>
                  <form onSubmit={handleAddMovie}>
                    <input type="text" placeholder="Izenburua" value={newMovie.title} onChange={(e)=>setNewMovie({...newMovie, title: e.target.value})} required />
                    <textarea placeholder="Deskribapena" value={newMovie.description} onChange={(e)=>setNewMovie({...newMovie, description: e.target.value})} />
                    <button type="submit">Gorde</button>
                  </form>
                </div>
              )}
              <div className="search-container">
                <input type="text" placeholder="Bilatu pelikula..." onChange={(e)=>setSearchTerm(e.target.value)} className="search-bar" />
              </div>
              <div className="movies-grid">
                {movies.filter(m => m.title.toLowerCase().includes(searchTerm.toLowerCase())).map(m => (
                  <div key={m.id} className="movie-card">
                    <h3>{m.title}</h3>
                    <p>{m.description}</p>
                    <div className="card-buttons">
                      <button onClick={() => handleAddFavorite(m.id)} className="fav-add-btn">⭐ Gogokoa</button>
                      {role === 'admin' && <button onClick={() => handleDeleteMovie(m.id)} className="delete-btn">Ezabatu</button>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentView === 'favorites' && (
            <div className="favorites">
              <h2>Zure Gogokoenak</h2>
              <div className="movies-grid">
                {favorites.length === 0 ? <p>Hutsa... Gehitu pelikulak!</p> : favorites.map(m => (
                  <div key={m.id} className="movie-card">
                    <h3>{m.title}</h3>
                    <p>{m.description}</p>
                    <button onClick={() => handleRemoveFavorite(m.id)} className="remove-fav-btn">❌ Kendu</button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="app-login">
      <h2>{isRegister ? 'Erregistratu' : 'Saioa hasi'}</h2>
      <form onSubmit={isRegister ? (e)=>{e.preventDefault(); axios.post('http://localhost:5000/register', formData).then(()=>setIsRegister(false))} : handleLogin}>
        <input type="text" placeholder="Username" onChange={(e)=>setFormData({...formData, username: e.target.value})} required />
        <input type="password" placeholder="Password" onChange={(e)=>setFormData({...formData, password: e.target.value})} required />
        <button type="submit">{isRegister ? 'Erregistratu' : 'Hasi'}</button>
      </form>
      <button onClick={() => setIsRegister(!isRegister)} className="toggle-btn">
        {isRegister ? 'Badut kontua, saioa hasi' : 'Ez dut konturik, erregistratu'}
      </button>
    </div>
  )
}

export default App