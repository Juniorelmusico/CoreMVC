import { useState, useEffect } from "react";
import api from "../api";
import "../styles/Admin.css";

function Admin() {
    const [activeTab, setActiveTab] = useState("dashboard");
    const [dashboardData, setDashboardData] = useState(null);
    const [users, setUsers] = useState([]);
    const [files, setFiles] = useState([]);
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
            } else if (activeTab === "users") {
                const response = await api.get("/api/admin/users/");
                setUsers(response.data);
            } else if (activeTab === "files") {
                const response = await api.get("/api/admin/files/");
                setFiles(response.data);
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
        if (!dashboardData) return null;

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
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Admin; 