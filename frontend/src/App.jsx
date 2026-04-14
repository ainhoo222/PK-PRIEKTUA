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
  const [newMovie, setNewMovie] = useState({ title: '', description: '', poster: '', posterFile: null, duration: '', category_id: '' })
  const [searchTerm, setSearchTerm] = useState('')
  const [categories, setCategories] = useState([])
  const [newCategoryName, setNewCategoryName] = useState('')
  const [selectedCategoryId, setSelectedCategoryId] = useState('')
  const [selectedDuration, setSelectedDuration] = useState('')
  const [seenMovieIds, setSeenMovieIds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('seenMovieIds')) || []
    } catch {
      return []
    }
  })
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [editFormData, setEditFormData] = useState({ username: '', email: '', password: '', avatar: '' })
  const [profileMessage, setProfileMessage] = useState('')
  const [editingMovie, setEditingMovie] = useState(null)
  const [editMovieForm, setEditMovieForm] = useState({ title: '', description: '', poster: '', duration: '' })
  
  const AVATAR_OPTIONS = ['👤', '😊', '😎', '🎨', '📚', '⭐', '🎭', '🚀', '💻', '🎮', '🏆', '🌟']

  const getFallbackPoster = (title) => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="520" height="780" viewBox="0 0 520 780">
        <defs>
          <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#001f4d" />
            <stop offset="100%" stop-color="#002f6e" />
          </linearGradient>
        </defs>
        <rect width="520" height="780" fill="url(%23bg)" />
        <rect x="20" y="20" width="480" height="640" rx="28" ry="28" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.18)" stroke-width="4" />
        <text x="50%" y="280" text-anchor="middle" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="42" fill="#ffffff" font-weight="700">${title.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</text>
        <text x="50%" y="340" text-anchor="middle" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="22" fill="#cfd8ff">POSTER</text>
        <text x="50%" y="700" text-anchor="middle" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="18" fill="#a8bff6">Fallback image</text>
      </svg>
    `
    return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
  }

  const getMoviePoster = (movie) => {
    if (movie.poster && movie.poster.startsWith('/uploads/')) {
      return `http://localhost:5000${movie.poster}`
    }
    return movie.poster || getFallbackPoster(movie.title)
  }
  const isFavoriteMovie = (movieId) => favorites.some(fav => fav.id === movieId)
  const isSeenMovie = (movieId) => seenMovieIds.includes(movieId)
  const [previewMovie, setPreviewMovie] = useState(null)
  const [languageSelectionMovie, setLanguageSelectionMovie] = useState(null)
  const [selectedLanguage, setSelectedLanguage] = useState('')
  const [selectedCommentMovie, setSelectedCommentMovie] = useState(null)
  const [commentText, setCommentText] = useState('')
  const [commentMessage, setCommentMessage] = useState('')

  const openPreview = (movie) => {
    setLanguageSelectionMovie(movie)
    setSelectedLanguage('')
  }

  const openCommentModal = async (movie) => {
    const latestMovies = await fetchMovies()
    const targetMovie = latestMovies.find(m => m.id === movie.id) || movie
    setSelectedCommentMovie(targetMovie)
    setCommentMessage('')
    setCommentText('')
  }

  const closeCommentModal = () => {
    setSelectedCommentMovie(null)
    setCommentText('')
    setCommentMessage('')
  }

  const confirmLanguageAndPreview = () => {
    if (!selectedLanguage) {
      alert('Mesedez, hautatu hizkuntza bat lehenengo.')
      return
    }
    setPreviewMovie(languageSelectionMovie)
    setLanguageSelectionMovie(null)
  }

  const closePreview = () => {
    setPreviewMovie(null)
    setSelectedLanguage('')
    setCommentText('')
    setCommentMessage('')
  }

  const closeLanguageSelection = () => {
    setLanguageSelectionMovie(null)
    setSelectedLanguage('')
    setCommentText('')
    setCommentMessage('')
  }

  const toggleSeenMovie = (movieId) => {
    const updatedIds = isSeenMovie(movieId)
      ? seenMovieIds.filter(id => id !== movieId)
      : [...seenMovieIds, movieId]

    setSeenMovieIds(updatedIds)
    localStorage.setItem('seenMovieIds', JSON.stringify(updatedIds))
  }

  const fetchProfile = async () => {
    try {
      const res = await axios.get('http://localhost:5000/profile', { headers: { Authorization: token } })
      setUserData(res.data); setRole(res.data.role)
    } catch (e) { console.error(e) }
  }

  const fetchMovies = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/movies')
      const uniqueMovies = Array.from(new Map(res.data.map(movie => [movie.id, movie])).values())
      setMovies(uniqueMovies)
      return uniqueMovies
    } catch (e) { console.error(e); return [] }
  }

  const fetchFavorites = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/favorites', { headers: { Authorization: token } })
      setFavorites(res.data)
    } catch (e) { console.error(e) }
  }

  const fetchCategories = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/categories')
      setCategories(res.data)
    } catch (e) { console.error('Errorea kategoriak kargatzean', e) }
  }

  useEffect(() => {
    if (token) {
      fetchProfile()
      fetchMovies()
      fetchFavorites()
      fetchCategories()
    }
  }, [token])

  useEffect(() => {
    if (token && (currentView === 'movies' || currentView === 'seen')) {
      fetchMovies()
    }
  }, [currentView, token])

  const handleLogin = async (e) => {
    e.preventDefault()
    
    if (!formData.username.trim()) {
      setMessage('❌ Erabiltzailearen izena beharrezkoa')
      return
    }
    if (!formData.password.trim()) {
      setMessage('❌ Pasahitza beharrezkoa')
      return
    }
    
    try {
      const res = await axios.post('http://localhost:5000/login', { username: formData.username, password: formData.password })
      setToken(res.data.token)
      setRole(res.data.role)
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('role', res.data.role)
      setCurrentView('profile')
      setMessage('')
    } catch (e) { 
      const errorMsg = e.response?.data?.message || 'Errorea saioa hastean'
      setMessage('❌ ' + errorMsg)
    }
  }

  const handleAddMovie = async (e) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append('title', newMovie.title)
      formData.append('description', newMovie.description)
      formData.append('category_id', newMovie.category_id)
      formData.append('duration', newMovie.duration)
      if (newMovie.poster) {
        formData.append('poster', newMovie.poster)
      }
      if (newMovie.posterFile) {
        formData.append('poster_file', newMovie.posterFile)
      }
      await axios.post('http://localhost:5000/api/movies', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      setNewMovie({ title: '', description: '', poster: '', posterFile: null, duration: '', category_id: '' })
      fetchMovies()
      setMessage('Filma ongi gehitu da!')
    } catch (e) { console.error(e) }
  }

  const handleDeleteMovie = async (id) => {
    if (window.confirm("Ziur zaude pelikula hau guztiz ezabatu nahi duzula?")) {
      await axios.delete(`http://localhost:5000/api/movies/${id}`)
      fetchMovies(); fetchFavorites()
    }
  }

  const handleEditMovie = (movie) => {
    setEditingMovie(movie)
    setEditMovieForm({ title: movie.title, description: movie.description, poster: movie.poster || '', duration: movie.duration || 120 })
  }

  const handleSaveEditMovie = async () => {
    try {
      await axios.put(`http://localhost:5000/api/movies/${editingMovie.id}`, editMovieForm)
      setEditingMovie(null)
      fetchMovies()
      alert("Pelikula eguneratua!")
    } catch (e) {
      console.error(e)
      alert("Errorea eguneratzean")
    }
  }

  const handleCancelEdit = () => {
    setEditingMovie(null)
  }

  const handleAddFavorite = async (movieId) => {
    try {
      await axios.post('http://localhost:5000/api/favorites', { movie_id: movieId }, { headers: { Authorization: token } })
      fetchFavorites(); alert("Gogokoetara gehituta!")
    } catch (e) { console.error(e) }
  }

  const toggleFavorite = async (movieId) => {
    if (isFavoriteMovie(movieId)) {
      await handleRemoveFavorite(movieId)
    } else {
      await handleAddFavorite(movieId)
    }
  }

  const handleRemoveFavorite = async (movieId) => {
    try {
      await axios.delete(`http://localhost:5000/api/favorites/${movieId}`, { headers: { Authorization: token } })
      fetchFavorites()
    } catch (e) { console.error(e) }
  }

  const handleAddComment = async (movieId) => {
    if (!commentText.trim()) {
      setCommentMessage('❌ Mesedez, idatzi zure iruzkina')
      return
    }
    try {
      await axios.post(`http://localhost:5000/api/movies/${movieId}/comments`, { text: commentText }, { headers: { Authorization: token } })
      setCommentText('')
      setCommentMessage('✅ Iruzkin gehitu da!')
      const updatedMovies = await fetchMovies()
      const updatedMovie = updatedMovies.find(m => m.id === movieId)
      if (updatedMovie) {
        setSelectedCommentMovie(updatedMovie)
      }
    } catch (e) {
      const errorMsg = e.response?.data?.message || 'Errorea iruzkin bat gehitzean'
      setCommentMessage('❌ ' + errorMsg)
    }
  }

  const handleDeleteComment = async (commentId, movieId) => {
    if (role !== 'admin') {
      setCommentMessage('❌ Admin bakarrik iruzkinak ezabatu daitezke')
      return
    }
    if (!window.confirm('Ziur zaude iruzkin hau guztiz ezabatu nahi duzula?')) {
      return
    }
    try {
      await axios.delete(`http://localhost:5000/api/comments/${commentId}`, { headers: { Authorization: token } })
      setCommentMessage('✅ Iruzkinak ezabatua!')
      const updatedMovies = await fetchMovies()
      const updatedMovie = updatedMovies.find(m => m.id === movieId)
      if (updatedMovie) {
        setSelectedCommentMovie(updatedMovie)
      }
    } catch (e) {
      const errorMsg = e.response?.data?.message || 'Errorea iruzkinak ezabatzean'
      setCommentMessage('❌ ' + errorMsg)
    }
  }

  const handleLogout = () => {
    setToken(''); setRole(''); localStorage.clear(); setCurrentView('profile')
  }

  const handleUpdateProfile = async (e) => {
    e.preventDefault()
    
    // Validación
    if (editFormData.username && editFormData.username.trim() === '') {
      setProfileMessage('❌ Erabiltzailea hutsik ez daiteke egon')
      return
    }
    if (editFormData.email && editFormData.email.trim() === '') {
      setProfileMessage('❌ Emaila hutsik ez daiteke egon')
      return
    }
    if (editFormData.email && !editFormData.email.includes('@')) {
      setProfileMessage('❌ Email baliozkoa ez da')
      return
    }
    if (editFormData.password && editFormData.password.length < 4) {
      setProfileMessage('❌ Pasahitza gutxienez 4 karaktere izan behar du')
      return
    }
    
    try {
      const res = await axios.put('http://localhost:5000/profile', editFormData, { headers: { Authorization: token } })
      setUserData(res.data)
      setProfileMessage('✅ Profila eguneratuta!')
      setIsEditingProfile(false)
      setEditFormData({ username: '', email: '', password: '', avatar: '' })
      setTimeout(() => setProfileMessage(''), 2000)
    } catch (e) {
      const errorMsg = e.response?.data?.message || 'Errorea profilean eguneratzean'
      setProfileMessage('❌ ' + errorMsg)
    }
  }

  const handleAddCategory = async (e) => {
    e.preventDefault()
    try {
      await axios.post('http://localhost:5000/api/categories', 
        { name: newCategoryName },
        { headers: { Authorization: token } }
      )
      setNewCategoryName('')
      fetchCategories()
      alert('Kategoria sortu da!')
    } catch (e) {
      console.error(e)
      alert('Errorea kategoria sortzean')
    }
  }

  const getDurationCategory = (minutes) => {
    if (!minutes || minutes < 1) return 'Denbora ez'
    if (minutes < 90) return 'Laburra'
    if (minutes <= 120) return 'Ertaina'
    return 'Luzea'
  }

  const filteredMovies = movies
    .filter(m => m.title.toLowerCase().includes(searchTerm.toLowerCase()))
    .filter(m => selectedCategoryId === '' || String(m.category?.id || '') === selectedCategoryId)
    .filter(m => selectedDuration === '' || (m.duration && getDurationCategory(m.duration) === selectedDuration))

  const handleRegister = async (e) => {
    e.preventDefault()
    
    // Validación en el cliente
    if (!formData.username.trim()) {
      setMessage('❌ Erabiltzailearen izena beharrezkoa')
      return
    }
    if (!formData.email.trim()) {
      setMessage('❌ Emaila beharrezkoa')
      return
    }
    if (!formData.email.includes('@')) {
      setMessage('❌ Email baliozkoa ez da')
      return
    }
    if (!formData.password.trim()) {
      setMessage('❌ Pasahitza beharrezkoa')
      return
    }
    
    try {
      const res = await axios.post('http://localhost:5000/register', formData)
      setMessage('✅ Erregistratuta! Saioa hasteko formulariora bueltatzen...')
      setTimeout(() => {
        setIsRegister(false)
        setFormData({ username: '', email: '', password: '' })
        setMessage('')
      }, 1500)
    } catch (e) {
      const errorMsg = e.response?.data?.message || 'Errorea erregistratzean'
      setMessage('❌ ' + errorMsg)
    }
  }

  const groupMoviesByCategory = (moviesList) => {
    const groups = {}
    moviesList.forEach(movie => {
      const catName = movie.category?.name || 'Sin categoría'
      if (!groups[catName]) groups[catName] = []
      groups[catName].push(movie)
    })
    return groups
  }

  if (token) {
    return (
      <div className="app app-logged">
        <div className="navbar">
          <button onClick={() => setCurrentView('profile')}>Profila</button>
          <button onClick={() => { fetchMovies(); setSelectedCategoryId(''); setSearchTerm(''); setCurrentView('movies') }}>Filmak</button>
          <button onClick={() => { fetchMovies(); setCurrentView('seen') }}>Ikusitakoak</button>
          <button onClick={() => {fetchFavorites(); setCurrentView('favorites')}}>Gogokoenak</button>
        </div>

        <div className="content">
          {currentView === 'profile' && (
            <div className="profile-container">
              <div className="profile-card">
                <div className="profile-header">
                  <div className="profile-avatar">{userData.avatar || '👤'}</div>
                  <div className="profile-info">
                    <h2>Nire Profila</h2>
                    <p className="profile-role">{role === 'admin' ? '👑 Administratzailea' : '👤 Erabiltzailea'}</p>
                  </div>
                </div>

                {profileMessage && (
                  <div className={`profile-message ${profileMessage.includes('Errorea') || profileMessage.includes('❌') ? 'error' : 'success'}`}>
                    {profileMessage}
                  </div>
                )}

                {!isEditingProfile ? (
                  <div className="profile-view">
                    <div className="profile-field">
                      <label>Erabiltzailea:</label>
                      <p>{userData.username}</p>
                    </div>
                    <div className="profile-field">
                      <label>Emaila:</label>
                      <p>{userData.email}</p>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleUpdateProfile} className="profile-edit">
                    <div className="edit-field">
                      <label>Erabiltzailea:</label>
                      <input 
                        type="text" 
                        value={editFormData.username}
                        onChange={(e) => setEditFormData({...editFormData, username: e.target.value})}
                        placeholder="Utzi hutsik ez bada aldatu nahi"
                      />
                    </div>

                    <div className="edit-field">
                      <label>Emaila:</label>
                      <input 
                        type="email" 
                        value={editFormData.email}
                        onChange={(e) => setEditFormData({...editFormData, email: e.target.value})}
                        placeholder="Utzi hutsik ez bada aldatu nahi"
                      />
                    </div>

                    <div className="edit-field">
                      <label>Argazkia:</label>
                      <div className="avatar-selector">
                        {AVATAR_OPTIONS.map(avatar => (
                          <button
                            key={avatar}
                            type="button"
                            className={`avatar-option ${editFormData.avatar === avatar ? 'selected' : ''}`}
                            onClick={() => setEditFormData({...editFormData, avatar})}
                          >
                            {avatar}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="edit-field">
                      <label>Pasahitza Berria:</label>
                      <input 
                        type="password" 
                        value={editFormData.password}
                        onChange={(e) => setEditFormData({...editFormData, password: e.target.value})}
                        placeholder="Utzi hutsik ez bada aldatu nahi"
                      />
                    </div>

                    <div className="edit-buttons">
                      <button type="submit" className="save-btn">💾 Gorde</button>
                      <button 
                        type="button" 
                        onClick={() => {
                          setIsEditingProfile(false)
                          setEditFormData({ username: '', email: '', password: '', avatar: '' })
                          setProfileMessage('')
                        }}
                        className="cancel-btn"
                      >
                        ❌ Utzi
                      </button>
                    </div>
                  </form>
                )}

                <button 
                  onClick={() => {
                    setIsEditingProfile(true)
                    setEditFormData({ username: userData.username, email: userData.email, password: '', avatar: userData.avatar || '👤' })
                    setProfileMessage('')
                  }}
                  className="edit-btn"
                >
                  ✏️ Editatu Profila
                </button>

                <button onClick={handleLogout} className="logout-btn">🚪 Saioa amaitu</button>
              </div>
            </div>
          )}

          {currentView === 'movies' && (
            <div className="movies">
              {(role === 'admin') && (
                <>
                  {/* Kategoria sortzeko kutxa */}
                  <div className="admin-box">
                    <h3>Sortu kategoria berria</h3>
                    <form onSubmit={handleAddCategory}>
                      <input 
                        type="text" 
                        placeholder="Kategoria izena" 
                        value={newCategoryName} 
                        onChange={(e) => setNewCategoryName(e.target.value)} 
                        required 
                      />
                      <button type="submit">Sortu</button>
                    </form>
                  </div>

                  {/* Pelikula gehitzeko kutxa */}
                  <div className="admin-box">
                    <h3>Gehitu Filma</h3>
                    <form onSubmit={handleAddMovie} encType="multipart/form-data">
                      <input type="text" placeholder="Izenburua" value={newMovie.title} onChange={(e)=>setNewMovie({...newMovie, title: e.target.value})} required />
                      <textarea placeholder="Deskribapena" value={newMovie.description} onChange={(e)=>setNewMovie({...newMovie, description: e.target.value})} />
                      <input type="number" placeholder="Iraupena (minutuak) (aukerakoa)" value={newMovie.duration} onChange={(e)=>setNewMovie({...newMovie, duration: e.target.value})} min="1" />
                      <input type="url" placeholder="Poster URLa (aukerakoa)" value={newMovie.poster} onChange={(e)=>setNewMovie({...newMovie, poster: e.target.value})} />
                      <input type="file" accept="image/*" onChange={(e)=>setNewMovie({...newMovie, posterFile: e.target.files[0]})} />
                      <select value={newMovie.category_id} onChange={(e)=>setNewMovie({...newMovie, category_id: e.target.value})} required>
                        <option value="">Hautatu kategoria</option>
                        {categories.map(cat => (
                          <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                      </select>
                      <button type="submit">Gorde</button>
                    </form>
                  </div>
                </>
              )}

              <div className="search-filter-row">
                <input
                  type="text"
                  placeholder="Bilatu pelikula..."
                  value={searchTerm}
                  onChange={(e)=>setSearchTerm(e.target.value)}
                  className="search-bar"
                />
                <select
                  className="category-filter"
                  value={selectedCategoryId}
                  onChange={(e) => setSelectedCategoryId(e.target.value)}
                >
                  <option value="">Kategoria guztiak</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
                <select
                  className="category-filter"
                  value={selectedDuration}
                  onChange={(e) => setSelectedDuration(e.target.value)}
                >
                  <option value="">Iraupena guztiak</option>
                  <option value="Laburra">Laburra (&lt;90 min)</option>
                  <option value="Ertaina">Ertaina (90-120 min)</option>
                  <option value="Luzea">Luzea (&gt;120 min)</option>
                </select>
              </div>

              {filteredMovies.length === 0 ? (
                <div className="empty-state">
                  <p>Ez da pelikularik aurkitu bilaketaren edo kategoria hautapenaren arabera.</p>
                </div>
              ) : (
                <div className="movies-grid">
                  {filteredMovies.map(m => (
                    <div key={m.id} className="movie-card">
                      <div className="movie-poster">
                        <img
                          src={getMoviePoster(m)}
                          alt={`${m.title} poster`}
                          onError={(e) => {
                            e.target.onerror = null
                            e.target.src = getFallbackPoster(m.title)
                          }}
                          onClick={() => openPreview(m)}
                          style={{ cursor: 'pointer' }}
                        />
                        <div className="movie-overlay">
                          <button
                            onClick={() => toggleFavorite(m.id)}
                            className={`movie-favorite-btn ${isFavoriteMovie(m.id) ? 'active' : ''}`}
                            type="button"
                            aria-label={isFavoriteMovie(m.id) ? 'Quitar de favoritos' : 'Añadir a favoritos'}
                          >
                            {isFavoriteMovie(m.id) ? '★' : '☆'}
                          </button>
                          <button
                            onClick={() => toggleSeenMovie(m.id)}
                            className={`movie-seen-btn ${isSeenMovie(m.id) ? 'active' : ''}`}
                            type="button"
                            aria-label={isSeenMovie(m.id) ? 'Marcar como no visto' : 'Marcar como visto'}
                          >
                            👁️
                          </button>
                          <div className="movie-overlay-body">
                            <div className="movie-description">{m.description}</div>
                          </div>
                          <button type="button" className="watch-btn overlay-watch-btn" onClick={() => openPreview(m)}>
                            Ikusi
                          </button>
                        </div>
                        {isFavoriteMovie(m.id) && <div className="poster-badge">Gogokoa</div>}
                        {isSeenMovie(m.id) && <div className="poster-badge seen-badge">Ikusitakoa</div>}
                      </div>
                      <div className="movie-info">
                        <h3>{m.title}</h3>
                        <p className="movie-category">{m.category?.name || 'Sin categoría'}</p>
                        <p className="movie-duration">{m.duration} min ({getDurationCategory(m.duration)})</p>
                      <div className="movie-comment-actions">
                        <button type="button" className="comment-action-btn" onClick={() => openCommentModal(m)}>
                          Komentarioak
                        </button>
                      </div>
                      </div>
                      {role === 'admin' && (
                        <div className="admin-buttons">
                          <button onClick={() => handleEditMovie(m)} className="edit-btn">Editatu</button>
                          <button onClick={() => handleDeleteMovie(m.id)} className="delete-btn">Ezabatu</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {languageSelectionMovie && (
            <div className="preview-modal" role="dialog" aria-modal="true">
              <div className="preview-backdrop" onClick={closeLanguageSelection}></div>
              <div className="preview-box">
                <div className="preview-screen">
                  <h2>Hautatu hizkuntza</h2>
                  <p style={{ color: '#ddd', marginTop: '12px' }}>
                    {languageSelectionMovie.title} ikusteko, aukeratu hizkuntza bat.
                  </p>
                  <div className="language-options">
                    <button
                      type="button"
                      className={`language-select-btn ${selectedLanguage === 'euskera' ? 'selected' : ''}`}
                      onClick={() => setSelectedLanguage('euskera')}
                    >
                      Euskera
                    </button>
                    <button
                      type="button"
                      className={`language-select-btn ${selectedLanguage === 'castellano' ? 'selected' : ''}`}
                      onClick={() => setSelectedLanguage('castellano')}
                    >
                      Castellano
                    </button>
                    <button
                      type="button"
                      className={`language-select-btn ${selectedLanguage === 'ingles' ? 'selected' : ''}`}
                      onClick={() => setSelectedLanguage('ingles')}
                    >
                      Ingles
                    </button>
                  </div>
                </div>
                <div className="edit-buttons" style={{ justifyContent: 'center', gap: '14px' }}>
                  <button
                    type="button"
                    className="save-btn"
                    onClick={confirmLanguageAndPreview}
                  >
                    Ikusi
                  </button>
                  <button
                    type="button"
                    className="cancel-btn"
                    onClick={closeLanguageSelection}
                  >
                    Itxi
                  </button>
                </div>
              </div>
            </div>
          )}

          {previewMovie && (
            <div className="preview-modal" role="dialog" aria-modal="true">
              <div className="preview-backdrop" onClick={closePreview}></div>
              <div className="preview-box">
                <div className="preview-screen">
                  <h2>Ikusi: {previewMovie.title}</h2>
                  <p style={{ color: '#ddd', marginTop: '10px' }}>
                    Hautatutako hizkuntza: {selectedLanguage === 'euskera' ? 'Euskera' : selectedLanguage === 'castellano' ? 'Castellano' : 'Ingles'}
                  </p>
                  <div className="preview-screen-window">
                    <div className="preview-screen-content">
                      <span>▶</span>
                      <p>{previewMovie.title}</p>
                    </div>
                  </div>
                </div>
                <button className="close-preview-btn" onClick={closePreview}>Itxi</button>
              </div>
            </div>
          )}

          {selectedCommentMovie && (
            <div className="comments-modal" role="dialog" aria-modal="true">
              <div className="preview-backdrop" onClick={closeCommentModal}></div>
              <div className="preview-box">
                <div className="preview-screen">
                  <h2>Komentarioak</h2>
                  <p style={{ color: '#ddd', marginTop: '10px' }}>
                    {selectedCommentMovie.title}
                  </p>
                  <div className="comment-list">
                    {selectedCommentMovie.comments?.length > 0 ? selectedCommentMovie.comments.map(comment => (
                      <div key={comment.id} className="comment-item">
                        <span className="comment-avatar">{comment.user.avatar || '👤'}</span>
                        <div style={{ flex: 1 }}>
                          <p className="comment-author">{comment.user.username}</p>
                          <p className="comment-text">{comment.text}</p>
                        </div>
                        {role === 'admin' && (
                          <button 
                            className="delete-comment-btn" 
                            onClick={() => handleDeleteComment(comment.id, selectedCommentMovie.id)}
                            title="Iruzkinak ezabatu"
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    )) : (
                      <p className="comment-empty">Oraindik ez dago iruzkinik.</p>
                    )}
                  </div>
                  <textarea
                    placeholder="Idatzi zure iruzkina hemen..."
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    rows="4"
                  />
                  <div className="comment-submit-row">
                    {commentMessage && (
                      <div className={`profile-message ${commentMessage.includes('❌') ? 'error' : 'success'}`}>
                        {commentMessage}
                      </div>
                    )}
                    <button type="button" className="save-btn" onClick={() => handleAddComment(selectedCommentMovie.id)}>
                      Bidali
                    </button>
                  </div>
                </div>
                <button className="close-preview-btn" onClick={closeCommentModal}>Itxi</button>
              </div>
            </div>
          )}

          {editingMovie && (
            <div className="edit-modal" role="dialog" aria-modal="true">
              <div className="edit-backdrop" onClick={handleCancelEdit}></div>
              <div className="edit-box">
                <h2>Editatu Pelikula</h2>
                <form onSubmit={(e) => { e.preventDefault(); handleSaveEditMovie(); }}>
                  <div className="form-group">
                    <label>Izenburua:</label>
                    <input
                      type="text"
                      value={editMovieForm.title}
                      onChange={(e) => setEditMovieForm({ ...editMovieForm, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Deskribapena:</label>
                    <textarea
                      value={editMovieForm.description}
                      onChange={(e) => setEditMovieForm({ ...editMovieForm, description: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Poster URLa:</label>
                    <input
                      type="url"
                      value={editMovieForm.poster}
                      onChange={(e) => setEditMovieForm({ ...editMovieForm, poster: e.target.value })}
                      placeholder="https://..."
                    />
                  </div>
                  <div className="form-group">
                    <label>Iraupena (minutuak):</label>
                    <input
                      type="number"
                      value={editMovieForm.duration}
                      onChange={(e) => setEditMovieForm({ ...editMovieForm, duration: e.target.value })}
                      min="1"
                    />
                  </div>
                  <div className="edit-buttons">
                    <button type="submit" className="save-btn">Gorde</button>
                    <button type="button" onClick={handleCancelEdit} className="cancel-btn">Utzi</button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {currentView === 'favorites' && (
            <div className="favorites">
              <h2>Zure Gogokoenak</h2>
              {Object.entries(groupMoviesByCategory(favorites)).map(([catName, favList]) => (
                <div key={catName}>
                  <h3 style={{ marginLeft: '30px', color: '#000080' }}>{catName}</h3>
                  <div className="movies-grid">
                    {favList.map(m => (
                      <div key={m.id} className="movie-card">
                        <div className="movie-poster">
                          <img
                          src={getMoviePoster(m)}
                            alt={`${m.title} poster`}
                            onError={(e) => {
                              e.target.onerror = null
                              e.target.src = getFallbackPoster(m.title)
                            }}
                          />
                          <div className="movie-overlay movie-overlay-favorite">
                            <div className="movie-description">{m.description}</div>
                          </div>
                        </div>
                        <div className="movie-info">
                          <h3>{m.title}</h3>
                          <p className="movie-category">{m.category?.name || 'Sin categoría'}</p>
                          <p className="movie-duration">{m.duration} min ({getDurationCategory(m.duration)})</p>
                        </div>
                        <div className="card-buttons">
                          <button onClick={() => handleRemoveFavorite(m.id)} className="remove-fav-btn">❌ Kendu</button>
                          <button onClick={() => toggleSeenMovie(m.id)} className={`movie-seen-btn ${isSeenMovie(m.id) ? 'active' : ''}`}>{isSeenMovie(m.id) ? '👁️ Ikusita' : '👁️ Ikusi'}</button>
                        </div>
                        {isSeenMovie(m.id) && <div className="poster-badge seen-badge">Ikusitakoa</div>}
                        {isFavoriteMovie(m.id) && <div className="poster-badge">Gogokoa</div>}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {favorites.length === 0 && <p>Hutsa... Gehitu pelikulak!</p>}
            </div>
          )}
          {currentView === 'seen' && (
            <div className="seen">
              <h2>Ikusitakoak</h2>
              {seenMovieIds.length === 0 ? (
                <p>Oraindik ez duzu pelikularik ikusi.</p>
              ) : (
                Object.entries(groupMoviesByCategory(
                  movies.filter(m => seenMovieIds.includes(m.id))
                )).map(([catName, seenList]) => (
                  <div key={catName}>
                    <h3 style={{ marginLeft: '30px', color: '#000080' }}>{catName}</h3>
                    <div className="movies-grid">
                      {seenList.map(m => (
                        <div key={m.id} className="movie-card">
                          <div className="movie-poster">
                            <img
                              src={getMoviePoster(m)}
                              alt={`${m.title} poster`}
                              onError={(e) => {
                                e.target.onerror = null
                                e.target.src = getFallbackPoster(m.title)
                              }}
                            />
                            <div className="movie-overlay movie-overlay-favorite">
                              <div className="movie-description">{m.description}</div>
                            </div>
                          </div>
                          <div className="movie-info">
                            <h3>{m.title}</h3>
                            <p className="movie-category">{m.category?.name || 'Sin categoría'}</p>
                            <p className="movie-duration">{m.duration} min ({getDurationCategory(m.duration)})</p>
                          </div>
                          <div className="card-buttons">
                            <button onClick={() => toggleSeenMovie(m.id)} className="remove-fav-btn">👁️ Kendu</button>
                            <button onClick={() => toggleFavorite(m.id)} className={`movie-favorite-btn ${isFavoriteMovie(m.id) ? 'active' : ''}`} type="button" aria-label={isFavoriteMovie(m.id) ? 'Quitar de favoritos' : 'Añadir a favoritos'}>
                              {isFavoriteMovie(m.id) ? '★' : '☆'}
                            </button>
                          </div>
                          {isSeenMovie(m.id) && <div className="poster-badge seen-badge">Ikusitakoa</div>}
                          {isFavoriteMovie(m.id) && <div className="poster-badge">Gogokoa</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="app-login">
      <h2>{isRegister ? '✨ Erregistratu' : '🎬 Saioa hasi'}</h2>
      
      {message && (
        <div className={`message ${message.includes('Errorea') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <form onSubmit={isRegister ? handleRegister : handleLogin}>
        <input 
          type="text" 
          placeholder="👤 Erabiltzailea" 
          value={formData.username}
          onChange={(e) => setFormData({...formData, username: e.target.value})} 
          required 
        />
        
        {isRegister && (
          <input 
            type="email" 
            placeholder="📧 Email" 
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})} 
            required 
          />
        )}
        
        <input 
          type="password" 
          placeholder="🔒 Pasahitza" 
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})} 
          required 
        />
        
        <button type="submit">
          {isRegister ? 'Erregistratu' : 'Hasi'}
        </button>
      </form>

      {isRegister && (
        <div style={{ 
          background: '#f0f8ff', 
          padding: '15px', 
          borderRadius: '10px', 
          marginBottom: '20px',
          border: '2px solid #000080',
          fontSize: '13px',
          color: '#333',
          lineHeight: '1.6'
        }}>
          <strong>💡 Administradorea izateko:</strong><br/>
          Erabiltzailea: <code style={{background: '#fff', padding: '2px 6px', borderRadius: '4px'}}>Admin</code><br/>
          Pasahitza: <code style={{background: '#fff', padding: '2px 6px', borderRadius: '4px'}}>Admin</code>
        </div>
      )}

      <button onClick={() => {
        setIsRegister(!isRegister)
        setMessage('')
        setFormData({ username: '', email: '', password: '' })
      }} className="toggle-btn">
        {isRegister ? '← Badut kontua, saioa hasi' : 'Ez dut konturik, erregistratu →'}
      </button>
    </div>
  )
}

export default App
