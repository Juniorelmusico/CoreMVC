import { useState, useEffect } from "react";
import api from "../api";
import "../styles/Admin.css";

function Admin() {
    const [activeTab, setActiveTab] = useState("dashboard");
    const [dashboardData, setDashboardData] = useState(null);
    const [modelStats, setModelStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [files, setFiles] = useState([]);
    
    // Datos de los modelos CRUD
    const [artists, setArtists] = useState([]);
    const [genres, setGenres] = useState([]);
    const [moods, setMoods] = useState([]);
    const [tracks, setTracks] = useState([]);
    const [analyses, setAnalyses] = useState([]);
    
    // Estado para formularios de edición
    const [editItem, setEditItem] = useState(null);
    const [newItem, setNewItem] = useState({});
    
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Cargar datos según la pestaña activa
        loadTabData();
    }, [activeTab]);

    const loadTabData = async () => {
        setLoading(true);
        setError(null);
        
        try {
            if (activeTab === "dashboard") {
                const response = await api.get("/api/admin/dashboard/");
                setDashboardData(response.data);
                
                // También cargar estadísticas de modelos
                const statsResponse = await api.get("/api/admin/model-stats/");
                setModelStats(statsResponse.data);
            } 
            else if (activeTab === "users") {
                const response = await api.get("/api/admin/users/");
                setUsers(response.data);
            } 
            else if (activeTab === "files") {
                const response = await api.get("/api/admin/files/");
                setFiles(response.data);
            }
            // Cargar datos para modelos CRUD
            else if (activeTab === "artists") {
                const response = await api.get("/api/admin/crud/artists/");
                setArtists(response.data);
            }
            else if (activeTab === "genres") {
                const response = await api.get("/api/admin/crud/genres/");
                setGenres(response.data);
            }
            else if (activeTab === "moods") {
                const response = await api.get("/api/admin/crud/moods/");
                setMoods(response.data);
            }
            else if (activeTab === "tracks") {
                const response = await api.get("/api/admin/crud/tracks/");
                setTracks(response.data);
            }
            else if (activeTab === "analyses") {
                const response = await api.get("/api/admin/crud/analyses/");
                setAnalyses(response.data);
            }
        } catch (err) {
            console.error("Error al cargar datos:", err);
            setError("Error al cargar datos. Verifica tu conexión e inténtalo de nuevo.");
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteFile = async (fileId) => {
        if (!window.confirm("¿Estás seguro de que deseas eliminar este archivo?")) {
            return;
        }
        
        try {
            await api.delete(`/api/admin/files/${fileId}/`);
            // Recargar la lista de archivos
            if (activeTab === "files") {
                const response = await api.get("/api/admin/files/");
                setFiles(response.data);
            }
        } catch (err) {
            console.error("Error al eliminar archivo:", err);
            alert("Error al eliminar el archivo");
        }
    };

    // Función para formatear la fecha
    const formatDate = (dateString) => {
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('es-ES', options);
    };

    // Función para renderizar un ícono según el tipo de archivo
    const getFileIcon = (contentType) => {
        if (contentType.startsWith('image/')) {
            return '🖼️';
        } else if (contentType.startsWith('video/')) {
            return '🎬';
        } else if (contentType.startsWith('audio/')) {
            return '🎵';
        } else if (contentType.includes('pdf')) {
            return '📄';
        } else if (contentType.includes('word') || contentType.includes('document')) {
            return '📝';
        } else if (contentType.includes('excel') || contentType.includes('spreadsheet')) {
            return '📊';
        } else if (contentType.includes('zip') || contentType.includes('rar') || contentType.includes('compressed')) {
            return '📦';
        } else {
            return '📁';
        }
    };

    const renderDashboard = () => {
        if (!dashboardData || !modelStats) return null;

        return (
            <div className="dashboard-container">
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon">👥</div>
                        <div className="stat-content">
                            <h3>Usuarios</h3>
                            <div className="stat-value">{dashboardData.users_count}</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon">📁</div>
                        <div className="stat-content">
                            <h3>Archivos</h3>
                            <div className="stat-value">{dashboardData.files_count}</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon">💾</div>
                        <div className="stat-content">
                            <h3>Almacenamiento</h3>
                            <div className="stat-value">{dashboardData.storage_used_mb} MB</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon">🎵</div>
                        <div className="stat-content">
                            <h3>Artistas</h3>
                            <div className="stat-value">{modelStats.artists_count}</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon">🎧</div>
                        <div className="stat-content">
                            <h3>Pistas</h3>
                            <div className="stat-value">{modelStats.tracks_count}</div>
                        </div>
                    </div>
                </div>

                <div className="recent-data-grid">
                    <div className="recent-section">
                        <h3>Usuarios recientes</h3>
                        <div className="recent-list">
                            {dashboardData.recent_users.map(user => (
                                <div className="recent-item" key={user.id}>
                                    <div className="item-icon">👤</div>
                                    <div className="item-details">
                                        <h4>{user.username}</h4>
                                        <p>ID: {user.id}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="recent-section">
                        <h3>Archivos recientes</h3>
                        <div className="recent-list">
                            {dashboardData.recent_files.map(file => (
                                <div className="recent-item" key={file.id}>
                                    <div className="item-icon">{getFileIcon(file.content_type)}</div>
                                    <div className="item-details">
                                        <h4>{file.name}</h4>
                                        <p>Tamaño: {(file.size / 1024).toFixed(2)} KB</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="recent-section">
                        <h3>Artistas recientes</h3>
                        <div className="recent-list">
                            {modelStats.recent_artists.map(artist => (
                                <div className="recent-item" key={artist.id}>
                                    <div className="item-icon">🎤</div>
                                    <div className="item-details">
                                        <h4>{artist.name}</h4>
                                        <p>ID: {artist.id}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const renderUsers = () => {
        return (
            <div className="users-container">
                <h2>Gestión de Usuarios</h2>
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Usuario</th>
                                <th>Admin</th>
                                <th>Fecha de registro</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id}>
                                    <td>{user.id}</td>
                                    <td>{user.username}</td>
                                    <td>{user.is_superuser ? "Sí" : "No"}</td>
                                    <td>{formatDate(user.date_joined)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    const renderFiles = () => {
        return (
            <div className="files-container admin-files">
                <h2>Gestión de Archivos</h2>
                
                <div className="admin-files-grid">
                    {files.map(file => (
                        <div className="admin-file-card" key={file.id}>
                            <div className="file-icon">{getFileIcon(file.content_type)}</div>
                            <div className="file-details">
                                <h3 className="file-name">{file.name}</h3>
                                <p className="file-meta">
                                    <span className="file-size">{(file.size / 1024).toFixed(2)} KB</span> • 
                                    <span className="file-type">{file.content_type}</span>
                                </p>
                                <p className="file-date">Subido el {formatDate(file.uploaded_at)}</p>
                            </div>
                            <div className="file-actions">
                                <a 
                                    href={file.file} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="action-button view-button"
                                >
                                    Ver
                                </a>
                                <button 
                                    className="action-button delete-button"
                                    onClick={() => handleDeleteFile(file.id)}
                                >
                                    Eliminar
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    // Funciones CRUD para modelos
    const handleCreate = async (model, data) => {
        try {
            await api.post(`/api/admin/crud/${model}/`, data);
            loadTabData(); // Recargar datos después de crear
            setNewItem({}); // Limpiar formulario
        } catch (err) {
            console.error(`Error al crear ${model}:`, err);
            alert(`Error al crear: ${err.response?.data?.detail || err.message}`);
        }
    };

    const handleUpdate = async (model, id, data) => {
        try {
            await api.put(`/api/admin/crud/${model}/${id}/`, data);
            loadTabData(); // Recargar datos después de actualizar
            setEditItem(null); // Cerrar formulario de edición
        } catch (err) {
            console.error(`Error al actualizar ${model}:`, err);
            alert(`Error al actualizar: ${err.response?.data?.detail || err.message}`);
        }
    };

    const handleDelete = async (model, id) => {
        if (!window.confirm(`¿Estás seguro de que deseas eliminar este elemento?`)) {
            return;
        }
        
        try {
            await api.delete(`/api/admin/crud/${model}/${id}/`);
            loadTabData(); // Recargar datos después de eliminar
        } catch (err) {
            console.error(`Error al eliminar ${model}:`, err);
            alert(`Error al eliminar: ${err.response?.data?.detail || err.message}`);
        }
    };

    // Renderizado para CRUD de Artistas
    const renderArtistsCRUD = () => {
        return (
            <div className="crud-container">
                <h2>Gestión de Artistas</h2>
                
                {/* Formulario para crear un nuevo artista */}
                <div className="crud-form">
                    <h3>Añadir Nuevo Artista</h3>
                    <div className="form-group">
                        <label>Nombre:</label>
                        <input 
                            type="text" 
                            value={newItem.name || ''} 
                            onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                            placeholder="Nombre del artista"
                        />
                    </div>
                    <button 
                        className="crud-button create-button"
                        onClick={() => handleCreate('artists', newItem)}
                        disabled={!newItem.name}
                    >
                        Crear Artista
                    </button>
                </div>
                
                {/* Tabla de artistas */}
                <div className="table-container">
                    <table className="data-table crud-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Fecha de Creación</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {artists.map(artist => (
                                <tr key={artist.id}>
                                    <td>{artist.id}</td>
                                    <td>
                                        {editItem && editItem.id === artist.id ? (
                                            <input 
                                                type="text" 
                                                value={editItem.name} 
                                                onChange={(e) => setEditItem({...editItem, name: e.target.value})} 
                                            />
                                        ) : (
                                            artist.name
                                        )}
                                    </td>
                                    <td>{formatDate(artist.created_at)}</td>
                                    <td className="action-buttons">
                                        {editItem && editItem.id === artist.id ? (
                                            <>
                                                <button 
                                                    className="crud-button save-button"
                                                    onClick={() => handleUpdate('artists', artist.id, editItem)}
                                                >
                                                    Guardar
                                                </button>
                                                <button 
                                                    className="crud-button cancel-button"
                                                    onClick={() => setEditItem(null)}
                                                >
                                                    Cancelar
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button 
                                                    className="crud-button edit-button"
                                                    onClick={() => setEditItem({...artist})}
                                                >
                                                    Editar
                                                </button>
                                                <button 
                                                    className="crud-button delete-button"
                                                    onClick={() => handleDelete('artists', artist.id)}
                                                >
                                                    Eliminar
                                                </button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    // Renderizado para CRUD de Géneros
    const renderGenresCRUD = () => {
        return (
            <div className="crud-container">
                <h2>Gestión de Géneros</h2>
                
                {/* Formulario para crear un nuevo género */}
                <div className="crud-form">
                    <h3>Añadir Nuevo Género</h3>
                    <div className="form-group">
                        <label>Nombre:</label>
                        <input 
                            type="text" 
                            value={newItem.name || ''} 
                            onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                            placeholder="Nombre del género"
                        />
                    </div>
                    <button 
                        className="crud-button create-button"
                        onClick={() => handleCreate('genres', newItem)}
                        disabled={!newItem.name}
                    >
                        Crear Género
                    </button>
                </div>
                
                {/* Tabla de géneros */}
                <div className="table-container">
                    <table className="data-table crud-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {genres.map(genre => (
                                <tr key={genre.id}>
                                    <td>{genre.id}</td>
                                    <td>
                                        {editItem && editItem.id === genre.id ? (
                                            <input 
                                                type="text" 
                                                value={editItem.name} 
                                                onChange={(e) => setEditItem({...editItem, name: e.target.value})} 
                                            />
                                        ) : (
                                            genre.name
                                        )}
                                    </td>
                                    <td className="action-buttons">
                                        {editItem && editItem.id === genre.id ? (
                                            <>
                                                <button 
                                                    className="crud-button save-button"
                                                    onClick={() => handleUpdate('genres', genre.id, editItem)}
                                                >
                                                    Guardar
                                                </button>
                                                <button 
                                                    className="crud-button cancel-button"
                                                    onClick={() => setEditItem(null)}
                                                >
                                                    Cancelar
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button 
                                                    className="crud-button edit-button"
                                                    onClick={() => setEditItem({...genre})}
                                                >
                                                    Editar
                                                </button>
                                                <button 
                                                    className="crud-button delete-button"
                                                    onClick={() => handleDelete('genres', genre.id)}
                                                >
                                                    Eliminar
                                                </button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    // Renderizado para CRUD de Estados de Ánimo (Moods)
    const renderMoodsCRUD = () => {
        return (
            <div className="crud-container">
                <h2>Gestión de Estados de Ánimo</h2>
                
                {/* Formulario para crear un nuevo estado de ánimo */}
                <div className="crud-form">
                    <h3>Añadir Nuevo Estado de Ánimo</h3>
                    <div className="form-group">
                        <label>Nombre:</label>
                        <input 
                            type="text" 
                            value={newItem.name || ''} 
                            onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                            placeholder="Nombre del estado de ánimo"
                        />
                    </div>
                    <button 
                        className="crud-button create-button"
                        onClick={() => handleCreate('moods', newItem)}
                        disabled={!newItem.name}
                    >
                        Crear Estado de Ánimo
                    </button>
                </div>
                
                {/* Tabla de estados de ánimo */}
                <div className="table-container">
                    <table className="data-table crud-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {moods.map(mood => (
                                <tr key={mood.id}>
                                    <td>{mood.id}</td>
                                    <td>
                                        {editItem && editItem.id === mood.id ? (
                                            <input 
                                                type="text" 
                                                value={editItem.name} 
                                                onChange={(e) => setEditItem({...editItem, name: e.target.value})} 
                                            />
                                        ) : (
                                            mood.name
                                        )}
                                    </td>
                                    <td className="action-buttons">
                                        {editItem && editItem.id === mood.id ? (
                                            <>
                                                <button 
                                                    className="crud-button save-button"
                                                    onClick={() => handleUpdate('moods', mood.id, editItem)}
                                                >
                                                    Guardar
                                                </button>
                                                <button 
                                                    className="crud-button cancel-button"
                                                    onClick={() => setEditItem(null)}
                                                >
                                                    Cancelar
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button 
                                                    className="crud-button edit-button"
                                                    onClick={() => setEditItem({...mood})}
                                                >
                                                    Editar
                                                </button>
                                                <button 
                                                    className="crud-button delete-button"
                                                    onClick={() => handleDelete('moods', mood.id)}
                                                >
                                                    Eliminar
                                                </button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    // Renderizado para CRUD de Pistas
    const renderTracksCRUD = () => {
        const [newTrack, setNewTrack] = useState({
            title: '',
            artist: '',
            genre: '',
            mood: '',
            bpm: '',
            duration: '',
            file: null
        });
        const [uploadError, setUploadError] = useState('');

        const handleTrackFileChange = (e) => {
            const file = e.target.files[0];
            if (file) {
                // Validación del lado del cliente para archivos MP3 y WAV
                const fileName = file.name.toLowerCase();
                if (!fileName.endsWith('.mp3') && !fileName.endsWith('.wav')) {
                    setUploadError("Error: Solo se permiten archivos MP3 y WAV");
                    return;
                }
                setUploadError('');
                setNewTrack({...newTrack, file: file});
            }
        };

        const handleCreateTrack = async () => {
            if (!newTrack.title || !newTrack.artist || !newTrack.file) {
                setUploadError("Los campos Título, Artista y Archivo son obligatorios");
                return;
            }

            try {
                const formData = new FormData();
                formData.append('title', newTrack.title);
                formData.append('artist', newTrack.artist);
                if (newTrack.genre) formData.append('genre', newTrack.genre);
                if (newTrack.mood) formData.append('mood', newTrack.mood);
                formData.append('bpm', newTrack.bpm || 0);
                formData.append('duration', newTrack.duration || 0);
                formData.append('file', newTrack.file);

                await api.post('/api/admin/crud/tracks/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
                
                // Limpiar formulario y recargar datos
                setNewTrack({
                    title: '',
                    artist: '',
                    genre: '',
                    mood: '',
                    bpm: '',
                    duration: '',
                    file: null
                });
                setUploadError('');
                loadTabData();
            } catch (error) {
                console.error('Error creating track:', error);
                const errorMessage = error.response?.data?.error || "Error al crear la pista";
                setUploadError(errorMessage);
            }
        };

        return (
            <div className="crud-container">
                <h2>Gestión de Pistas</h2>
                
                {/* Formulario para crear una nueva pista */}
                <div className="crud-form">
                    <h3>Añadir Nueva Pista</h3>
                    <div className="form-grid">
                        <div className="form-group">
                            <label>Título: *</label>
                            <input 
                                type="text" 
                                value={newTrack.title} 
                                onChange={(e) => setNewTrack({...newTrack, title: e.target.value})}
                                placeholder="Título de la pista"
                            />
                        </div>
                        <div className="form-group">
                            <label>Artista: *</label>
                            <select 
                                value={newTrack.artist} 
                                onChange={(e) => setNewTrack({...newTrack, artist: e.target.value})}
                            >
                                <option value="">Seleccione un artista</option>
                                {artists.map(artist => (
                                    <option key={artist.id} value={artist.id}>{artist.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Género:</label>
                            <select 
                                value={newTrack.genre} 
                                onChange={(e) => setNewTrack({...newTrack, genre: e.target.value})}
                            >
                                <option value="">Seleccione un género</option>
                                {genres.map(genre => (
                                    <option key={genre.id} value={genre.id}>{genre.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Estado de ánimo:</label>
                            <select 
                                value={newTrack.mood} 
                                onChange={(e) => setNewTrack({...newTrack, mood: e.target.value})}
                            >
                                <option value="">Seleccione un estado</option>
                                {moods.map(mood => (
                                    <option key={mood.id} value={mood.id}>{mood.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>BPM:</label>
                            <input 
                                type="number" 
                                value={newTrack.bpm} 
                                onChange={(e) => setNewTrack({...newTrack, bpm: e.target.value})}
                                placeholder="Beats por minuto"
                            />
                        </div>
                        <div className="form-group">
                            <label>Duración (segundos):</label>
                            <input 
                                type="number" 
                                value={newTrack.duration} 
                                onChange={(e) => setNewTrack({...newTrack, duration: e.target.value})}
                                placeholder="Duración en segundos"
                            />
                        </div>
                        <div className="form-group file-input-group">
                            <label>Archivo: * (Solo MP3 o WAV)</label>
                            <input 
                                type="file" 
                                onChange={handleTrackFileChange}
                                accept=".mp3,.wav"
                            />
                        </div>
                    </div>
                    
                    {uploadError && (
                        <div className="error-message form-error">
                            {uploadError}
                        </div>
                    )}
                    
                    <button 
                        className="crud-button create-button"
                        onClick={handleCreateTrack}
                        disabled={!newTrack.title || !newTrack.artist || !newTrack.file}
                    >
                        Crear Pista
                    </button>
                </div>
                
                {/* Tabla de pistas */}
                <div className="table-container">
                    <table className="data-table crud-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Título</th>
                                <th>Artista</th>
                                <th>Género</th>
                                <th>Estado</th>
                                <th>BPM</th>
                                <th>Duración</th>
                                <th>Fecha</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tracks.map(track => (
                                <tr key={track.id}>
                                    <td>{track.id}</td>
                                    <td>{track.title}</td>
                                    <td>{artists.find(a => a.id === track.artist)?.name || track.artist}</td>
                                    <td>{genres.find(g => g.id === track.genre)?.name || track.genre}</td>
                                    <td>{moods.find(m => m.id === track.mood)?.name || track.mood}</td>
                                    <td>{track.bpm}</td>
                                    <td>{track.duration}s</td>
                                    <td>{formatDate(track.created_at)}</td>
                                    <td className="action-buttons">
                                        <button 
                                            className="crud-button view-button"
                                            onClick={() => window.open(track.file, '_blank')}
                                        >
                                            Ver
                                        </button>
                                        <button 
                                            className="crud-button delete-button"
                                            onClick={() => handleDelete('tracks', track.id)}
                                        >
                                            Eliminar
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    // Renderizado para CRUD de Análisis
    const renderAnalysesCRUD = () => {
        return (
            <div className="crud-container">
                <h2>Gestión de Análisis</h2>
                
                {/* Tabla de análisis */}
                <div className="table-container">
                    <table className="data-table crud-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Pista</th>
                                <th>Fecha de Análisis</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {analyses.map(analysis => (
                                <tr key={analysis.id}>
                                    <td>{analysis.id}</td>
                                    <td>{tracks.find(t => t.id === analysis.track)?.title || analysis.track}</td>
                                    <td>{formatDate(analysis.analyzed_at)}</td>
                                    <td className="action-buttons">
                                        <button 
                                            className="crud-button view-button"
                                            onClick={() => alert(JSON.stringify(analysis.details, null, 2))}
                                        >
                                            Ver Detalles
                                        </button>
                                        <button 
                                            className="crud-button delete-button"
                                            onClick={() => handleDelete('analyses', analysis.id)}
                                        >
                                            Eliminar
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    return (
        <div className="admin-container">
            <div className="admin-header">
                <h1>Panel de Administración</h1>
            </div>
            
            <div className="admin-content">
                <div className="admin-sidebar">
                    <button 
                        className={`sidebar-button ${activeTab === 'dashboard' ? 'active' : ''}`}
                        onClick={() => setActiveTab('dashboard')}
                    >
                        Dashboard
                    </button>
                    <button 
                        className={`sidebar-button ${activeTab === 'users' ? 'active' : ''}`}
                        onClick={() => setActiveTab('users')}
                    >
                        Usuarios
                    </button>
                    <button 
                        className={`sidebar-button ${activeTab === 'files' ? 'active' : ''}`}
                        onClick={() => setActiveTab('files')}
                    >
                        Archivos
                    </button>

                    <div className="sidebar-divider"></div>
                    <div className="sidebar-title">Gestión de Contenido</div>
                    
                    <button 
                        className={`sidebar-button ${activeTab === 'artists' ? 'active' : ''}`}
                        onClick={() => setActiveTab('artists')}
                    >
                        Artistas
                    </button>
                    <button 
                        className={`sidebar-button ${activeTab === 'genres' ? 'active' : ''}`}
                        onClick={() => setActiveTab('genres')}
                    >
                        Géneros
                    </button>
                    <button 
                        className={`sidebar-button ${activeTab === 'moods' ? 'active' : ''}`}
                        onClick={() => setActiveTab('moods')}
                    >
                        Estados de Ánimo
                    </button>
                    <button 
                        className={`sidebar-button ${activeTab === 'tracks' ? 'active' : ''}`}
                        onClick={() => setActiveTab('tracks')}
                    >
                        Pistas
                    </button>
                    <button 
                        className={`sidebar-button ${activeTab === 'analyses' ? 'active' : ''}`}
                        onClick={() => setActiveTab('analyses')}
                    >
                        Análisis
                    </button>
                </div>
                
                <div className="admin-main">
                    {loading ? (
                        <div className="loading-container">
                            <div className="loading-spinner"></div>
                            <p>Cargando datos...</p>
                        </div>
                    ) : error ? (
                        <div className="error-container">
                            <p>{error}</p>
                            <button onClick={loadTabData}>Reintentar</button>
                        </div>
                    ) : (
                        <>
                            {activeTab === 'dashboard' && renderDashboard()}
                            {activeTab === 'users' && renderUsers()}
                            {activeTab === 'files' && renderFiles()}
                            {activeTab === 'artists' && renderArtistsCRUD()}
                            {activeTab === 'genres' && renderGenresCRUD()}
                            {activeTab === 'moods' && renderMoodsCRUD()}
                            {activeTab === 'tracks' && renderTracksCRUD()}
                            {activeTab === 'analyses' && renderAnalysesCRUD()}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Admin; 