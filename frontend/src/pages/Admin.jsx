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

    // Al inicio del componente Admin:
    const [newUser, setNewUser] = useState({ username: '', email: '', password: '', confirm_password: '', is_superuser: false });
    const [creating, setCreating] = useState(false);
    const [artistError, setArtistError] = useState("");
    const [artistSuccess, setArtistSuccess] = useState("");
    const [genreError, setGenreError] = useState("");
    const [genreSuccess, setGenreSuccess] = useState("");
    const [moodError, setMoodError] = useState("");
    const [moodSuccess, setMoodSuccess] = useState("");
    const [trackError, setTrackError] = useState("");
    const [trackSuccess, setTrackSuccess] = useState("");
    const [newTrack, setNewTrack] = useState({ title: '', artist: '', genre: '', mood: '', bpm: '', duration: '', file: null });
    const [analysisError, setAnalysisError] = useState("");

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
        // Crear usuario
        const handleCreateUser = async () => {
            setCreating(true);
            try {
                await api.post('/api/admin/users/', newUser);
                setNewUser({ username: '', email: '', password: '', confirm_password: '', is_superuser: false });
                loadTabData();
            } catch (err) {
                alert('Error al crear usuario: ' + (err.response?.data?.detail || err.message));
            } finally {
                setCreating(false);
            }
        };

        // Eliminar usuario
        const handleDeleteUser = async (id) => {
            if (!window.confirm('¿Eliminar este usuario?')) return;
            try {
                await api.delete(`/api/admin/users/${id}/`);
                loadTabData();
            } catch (err) {
                alert('Error al eliminar usuario: ' + (err.response?.data?.detail || err.message));
            }
        };

        // Cambiar admin
        const handleToggleAdmin = async (user) => {
            try {
                await api.patch(`/api/admin/users/${user.id}/`, { is_superuser: !user.is_superuser });
                loadTabData();
            } catch (err) {
                alert('Error al cambiar privilegios: ' + (err.response?.data?.detail || err.message));
            }
        };

        return (
            <div className="users-container">
                <h2>Gestión de Usuarios</h2>
                <div className="user-form">
                    <h3>Crear nuevo usuario</h3>
                    <input type="text" placeholder="Usuario" value={newUser.username} onChange={e => setNewUser({ ...newUser, username: e.target.value })} />
                    <input type="email" placeholder="Email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} />
                    <input type="password" placeholder="Contraseña" value={newUser.password} onChange={e => setNewUser({ ...newUser, password: e.target.value })} />
                    <input type="password" placeholder="Confirmar contraseña" value={newUser.confirm_password} onChange={e => setNewUser({ ...newUser, confirm_password: e.target.value })} />
                    <label style={{marginTop: '0.5rem'}}>
                        <input type="checkbox" checked={newUser.is_superuser} onChange={e => setNewUser({ ...newUser, is_superuser: e.target.checked })} />
                        {' '}Admin
                    </label>
                    <button className="crud-button create-button" onClick={handleCreateUser} disabled={creating}>
                        {creating ? 'Creando...' : 'Crear Usuario'}
                    </button>
                </div>
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Usuario</th>
                                <th>Email</th>
                                <th>Admin</th>
                                <th>Fecha de registro</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id}>
                                    <td>{user.id}</td>
                                    <td>{user.username}</td>
                                    <td>{user.email}</td>
                                    <td>
                                        <input type="checkbox" checked={user.is_superuser} onChange={() => handleToggleAdmin(user)} />
                                    </td>
                                    <td>{user.date_joined ? formatDate(user.date_joined) : 'Sin fecha'}</td>
                                    <td>
                                        <button className="crud-button delete-button" onClick={() => handleDeleteUser(user.id)}>
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
        // Crear artista
        const handleCreateArtist = async () => {
            setArtistError(""); setArtistSuccess("");
            if (!newItem.name) { setArtistError("El nombre es obligatorio"); return; }
            try {
                await api.post('/api/admin/crud/artists/', newItem);
                setArtistSuccess("¡Artista creado!");
                setNewItem({});
                loadTabData();
            } catch (err) {
                setArtistError("Error al crear artista: " + (err.response?.data?.detail || err.message));
            }
        };
        // Eliminar artista
        const handleDeleteArtist = async (id) => {
            if (!window.confirm("¿Eliminar este artista?")) return;
            try {
                await api.delete(`/api/admin/crud/artists/${id}/`);
                loadTabData();
            } catch (err) {
                setArtistError("Error al eliminar artista: " + (err.response?.data?.detail || err.message));
            }
        };

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
                        onClick={handleCreateArtist}
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
                                                    onClick={() => handleDeleteArtist(artist.id)}
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
        // Crear género
        const handleCreateGenre = async () => {
            setGenreError(""); setGenreSuccess("");
            if (!newItem.name) { setGenreError("El nombre es obligatorio"); return; }
            try {
                await api.post('/api/admin/crud/genres/', newItem);
                setGenreSuccess("¡Género creado!");
                setNewItem({});
                loadTabData();
            } catch (err) {
                setGenreError("Error al crear género: " + (err.response?.data?.detail || err.message));
            }
        };
        // Eliminar género
        const handleDeleteGenre = async (id) => {
            if (!window.confirm("¿Eliminar este género?")) return;
            try {
                await api.delete(`/api/admin/crud/genres/${id}/`);
                loadTabData();
            } catch (err) {
                setGenreError("Error al eliminar género: " + (err.response?.data?.detail || err.message));
            }
        };

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
                        onClick={handleCreateGenre}
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
                                                    onClick={() => handleDeleteGenre(genre.id)}
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
        // Crear mood
        const handleCreateMood = async () => {
            setMoodError(""); setMoodSuccess("");
            if (!newItem.name) { setMoodError("El nombre es obligatorio"); return; }
            try {
                await api.post('/api/admin/crud/moods/', newItem);
                setMoodSuccess("¡Estado de ánimo creado!");
                setNewItem({});
                loadTabData();
            } catch (err) {
                setMoodError("Error al crear estado de ánimo: " + (err.response?.data?.detail || err.message));
            }
        };
        // Eliminar mood
        const handleDeleteMood = async (id) => {
            if (!window.confirm("¿Eliminar este estado de ánimo?")) return;
            try {
                await api.delete(`/api/admin/crud/moods/${id}/`);
                loadTabData();
            } catch (err) {
                setMoodError("Error al eliminar estado de ánimo: " + (err.response?.data?.detail || err.message));
            }
        };

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
                        onClick={handleCreateMood}
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
                                                    onClick={() => handleDeleteMood(mood.id)}
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
        const handleTrackFileChange = (e) => {
            const file = e.target.files[0];
            if (file) {
                // Validación del lado del cliente para archivos MP3 y WAV
                const fileName = file.name.toLowerCase();
                if (!fileName.endsWith('.mp3') && !fileName.endsWith('.wav')) {
                    setTrackError("Error: Solo se permiten archivos MP3 y WAV");
                    return;
                }
                setTrackError('');
                setNewTrack({...newTrack, file: file});
            }
        };

        const handleCreateTrack = async () => {
            setTrackError(""); setTrackSuccess("");
            if (!newTrack.title || !newTrack.artist || !newTrack.file) {
                setTrackError("Los campos Título, Artista y Archivo son obligatorios");
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
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                setTrackSuccess("¡Pista creada!");
                setNewTrack({ title: '', artist: '', genre: '', mood: '', bpm: '', duration: '', file: null });
                setTrackError("");
                loadTabData();
            } catch (error) {
                const errorMessage = error.response?.data?.error || "Error al crear la pista";
                setTrackError(errorMessage);
            }
        };

        const handleDeleteTrack = async (id) => {
            if (!window.confirm("¿Eliminar esta pista?")) return;
            try {
                await api.delete(`/api/admin/crud/tracks/${id}/`);
                loadTabData();
            } catch (err) {
                setTrackError("Error al eliminar pista: " + (err.response?.data?.detail || err.message));
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
                                onChange={(e) => {
                                    let value = e.target.value;
                                    if (value < 0) value = 0;
                                    if (value > 200) value = 200;
                                    setNewTrack({...newTrack, bpm: value});
                                }}
                                min={0}
                                max={200}
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
                    
                    {trackError && (
                        <div className="form-error">
                            <span className="error-icon">⚠️</span>
                            {trackError}
                        </div>
                    )}
                    
                    {trackSuccess && (
                        <div className="form-success">
                            <span className="success-icon">✅</span>
                            {trackSuccess}
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
                                    <td>{typeof track.artist === 'object' ? track.artist?.name : (artists.find(a => a.id === track.artist)?.name || track.artist)}</td>
                                    <td>{typeof track.genre === 'object' ? track.genre?.name : (genres.find(g => g.id === track.genre)?.name || track.genre)}</td>
                                    <td>{typeof track.mood === 'object' ? track.mood?.name : (moods.find(m => m.id === track.mood)?.name || track.mood)}</td>
                                    <td>{track.bpm}</td>
                                    <td>{track.duration}s</td>
                                    <td>{formatDate(track.uploaded_at)}</td>
                                    <td className="action-buttons">
                                        <button 
                                            className="crud-button view-button"
                                            onClick={() => window.open(track.file, '_blank')}
                                        >
                                            Ver
                                        </button>
                                        <button 
                                            className="crud-button delete-button"
                                            onClick={() => handleDeleteTrack(track.id)}
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
        // Eliminar análisis
        const handleDeleteAnalysis = async (id) => {
            if (!window.confirm("¿Eliminar este análisis?")) return;
            try {
                await api.delete(`/api/admin/crud/analyses/${id}/`);
                loadTabData();
            } catch (err) {
                setAnalysisError("Error al eliminar análisis: " + (err.response?.data?.detail || err.message));
            }
        };

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
                                            onClick={() => handleDeleteAnalysis(analysis.id)}
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