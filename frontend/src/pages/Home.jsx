import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import "../styles/Home.css";
import api from "../api";
import { ACCESS_TOKEN } from "../constants";

function Home() {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState("");
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [activeTab, setActiveTab] = useState("upload"); // upload o files
    const [loading, setLoading] = useState(false);
    const [isSuperuser, setIsSuperuser] = useState(false);
    const [comparison, setComparison] = useState(null);
    const [analysisPolling, setAnalysisPolling] = useState(false);
    const [pollingError, setPollingError] = useState("");

    // Verificar si el usuario es superusuario
    useEffect(() => {
        const token = localStorage.getItem(ACCESS_TOKEN);
        if (token) {
            try {
                const decoded = jwtDecode(token);
                setIsSuperuser(decoded.is_superuser === true);
                console.log("Home - Is Superuser:", decoded.is_superuser);
            } catch (error) {
                console.error("Error decodificando token:", error);
            }
        }
    }, []);

    // Cargar los archivos al montar el componente
    useEffect(() => {
        if (activeTab === "files") {
            fetchFiles();
        }
    }, [activeTab]);

    const fetchFiles = async () => {
        setLoading(true);
        try {
            const response = await api.get("/api/files/");
            if (response.status === 200) {
                setUploadedFiles(response.data);
            }
        } catch (error) {
            console.error("Error fetching files:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            
            // Create a preview for the file
            if (selectedFile.type.startsWith("image/")) {
                const reader = new FileReader();
                reader.onloadend = () => {
                    setPreview(reader.result);
                };
                reader.readAsDataURL(selectedFile);
            } else {
                setPreview(null);
            }
        }
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        
        if (!file) {
            setMessage("Por favor selecciona un archivo primero");
            return;
        }

        // Validación del lado del cliente para archivos MP3 y WAV
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.mp3') && !fileName.endsWith('.wav')) {
            setMessage("Error: Solo se permiten archivos MP3 y WAV");
            return;
        }

        setUploading(true);
        setMessage("Subiendo archivo...");

        try {
            // Create FormData object
            const formData = new FormData();
            formData.append("file", file);
            
            // Agregar campos requeridos por TrackUploadSerializer
            const title = file.name.replace(/\.[^/.]+$/, ""); // Quitar extensión del archivo
            formData.append("title", title);
            formData.append("artist_name", "Usuario Anónimo"); // Artista por defecto

            // Realizar la subida real al endpoint
            const response = await api.post("/api/tracks/upload/", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            
            if (response.status === 201) {
                console.log("📦 Upload response data:", response.data);
                setMessage("¡Archivo subido con éxito! Analizando...");
                setUploadedFiles(prev => [response.data, ...prev]);
                setFile(null);
                setPreview(null);
                // Iniciar polling para análisis
                if (response.data && response.data.id) {
                    console.log("🎯 Starting analysis for track ID:", response.data.id);
                    pollForAnalysis(response.data.id);
                } else {
                    console.log("❌ No ID found in upload response:", response.data);
                    setMessage("Archivo subido, pero no se pudo iniciar el análisis (falta ID)");
                }
            } else {
                setMessage("Error al subir el archivo");
            }
            setUploading(false);
        } catch (error) {
            console.error("Error uploading file:", error);
            // Mostrar el mensaje de error específico del backend si está disponible
            const errorMessage = error.response?.data?.error || "Error al subir el archivo";
            setMessage(errorMessage);
            setUploading(false);
        }
    };

    // Polling para análisis
    const pollForAnalysis = async (trackId, tries = 0) => {
        setAnalysisPolling(true);
        setComparison(null);
        setPollingError("");
        const maxTries = 3; // Reducir de 20 a 3 intentos
        const delay = 2000; // Reducir de 3000 a 2000ms
        try {
            console.log(`🔍 Attempting to fetch analysis for track ${trackId}, try ${tries + 1}`);
            const res = await api.get(`/api/tracks/${trackId}/analysis/`);
            
            if (res.data && res.data.comparison_result) {
                // Análisis completo disponible
                setComparison(res.data.comparison_result);
                setMessage("¡Análisis completado!");
                setAnalysisPolling(false);
            } else if (res.data && res.data.track_id) {
                // Información básica del track disponible
                const trackInfo = {
                    basic_info: true,
                    track_id: res.data.track_id,
                    track_title: res.data.track_title,
                    artist_name: res.data.artist_name,
                    fingerprint_status: res.data.fingerprint_status,
                    fingerprints_count: res.data.fingerprints_count,
                    message: res.data.message || 'Información básica del track'
                };
                setComparison(trackInfo);
                setMessage("¡Track subido exitosamente! Información disponible.");
                setAnalysisPolling(false);
            } else if (res.data && res.data.status === "completed") {
                setMessage("¡Análisis completado, pero sin comparación disponible.");
                setAnalysisPolling(false);
            } else if (tries < maxTries) {
                setTimeout(() => pollForAnalysis(trackId, tries + 1), delay);
            } else {
                setPollingError("No se pudo obtener información del análisis en este momento.");
                setAnalysisPolling(false);
            }
        } catch (err) {
            console.error(`❌ Analysis attempt ${tries + 1} failed:`, err);
            if (tries < maxTries) {
                setTimeout(() => pollForAnalysis(trackId, tries + 1), delay);
            } else {
                setPollingError("Error al obtener el análisis. El track se subió correctamente.");
                setAnalysisPolling(false);
            }
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

    // Función para renderizar el icono según tipo de archivo
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

    return (
        <div className="container">
            <div className="tabs">
                <button 
                    className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
                    onClick={() => setActiveTab('upload')}
                >
                    Subir Archivos
                </button>
                <button 
                    className={`tab ${activeTab === 'files' ? 'active' : ''}`}
                    onClick={() => setActiveTab('files')}
                >
                    Mis Archivos
                </button>
                
                {isSuperuser && (
                    <Link to="/admin" className="admin-link">
                        Panel de Administración
                    </Link>
                )}
            </div>

            {activeTab === 'upload' ? (
                <div className="upload-container">
                    <h1 className="upload-title">Subir Archivos</h1>
                    
                    <form onSubmit={handleUpload} className="upload-form">
                        <div className="file-input-container">
                            <label htmlFor="file-upload" className="custom-file-upload">
                                {file ? file.name : "Seleccionar archivo"}
                            </label>
                            <input 
                                id="file-upload"
                                type="file" 
                                onChange={handleFileChange}
                                className="file-input"
                                disabled={uploading}
                            />
                        </div>
                        
                        {preview && (
                            <div className="preview-container">
                                <img src={preview} alt="Preview" className="file-preview" />
                            </div>
                        )}
                        
                        {!preview && file && (
                            <div className="file-info">
                                <p>Tipo: {file.type}</p>
                                <p>Tamaño: {(file.size / 1024).toFixed(2)} KB</p>
                            </div>
                        )}
                        
                        <button 
                            type="submit" 
                            className="upload-button"
                            disabled={uploading || !file}
                        >
                            {uploading ? "Subiendo..." : "Subir Archivo"}
                        </button>
                        
                        {message && (
                            <p className={`message ${message.includes("Error") ? "error-message" : ""}`}>
                                {message}
                            </p>
                        )}
                        {analysisPolling && (
                            <div className="message">Analizando archivo... Por favor espera.</div>
                        )}
                        {pollingError && (
                            <div className="error-message">{pollingError}</div>
                        )}
                        {comparison && (
                            <div className="comparison-result" style={{marginTop: '2rem', background: '#232b43', borderRadius: '12px', padding: '1.5rem', color: '#fff'}}>
                                {comparison.basic_info ? (
                                    // Mostrar información básica del track
                                    <>
                                        <h2 style={{color: '#19e2c4'}}>🎵 Información del Track</h2>
                                        <div style={{background: '#1a2332', borderRadius: '8px', padding: '1rem', marginTop: '1rem'}}>
                                            <p><b>📝 Título:</b> {comparison.track_title}</p>
                                            <p><b>🎤 Artista:</b> {comparison.artist_name}</p>
                                            <p><b>🔑 ID del Track:</b> {comparison.track_id}</p>
                                            <p><b>🔍 Estado del Fingerprint:</b> 
                                                <span style={{
                                                    color: comparison.fingerprint_status === 'completed' ? '#19e2c4' : 
                                                           comparison.fingerprint_status === 'pending' ? '#f39c12' : '#e74c3c',
                                                    fontWeight: 'bold',
                                                    marginLeft: '0.5rem'
                                                }}>
                                                    {comparison.fingerprint_status === 'pending' ? '⏳ Pendiente' :
                                                     comparison.fingerprint_status === 'completed' ? '✅ Completado' :
                                                     comparison.fingerprint_status === 'failed' ? '❌ Fallido' : 
                                                     comparison.fingerprint_status}
                                                </span>
                                            </p>
                                            <p><b>🔢 Fingerprints:</b> {comparison.fingerprints_count}</p>
                                            <div style={{marginTop: '1rem', padding: '0.75rem', background: '#0f1419', borderRadius: '6px', border: '1px solid #19e2c4'}}>
                                                <p style={{margin: 0, color: '#19e2c4'}}>ℹ️ {comparison.message}</p>
                                            </div>
                                        </div>
                                        <div style={{marginTop: '1rem', fontSize: '0.9em', color: '#bbb'}}>
                                            <p>💡 El análisis detallado estará disponible cuando se complete el procesamiento del fingerprint.</p>
                                        </div>
                                    </>
                                ) : (
                                    // Mostrar análisis completo original
                                    <>
                                        <h2 style={{color: '#19e2c4'}}>Comparación de tu canción</h2>
                                        <p><b>Canción más parecida:</b> {comparison.most_similar_track} {comparison.most_similar_artist ? `de ${comparison.most_similar_artist}` : ''}</p>
                                        <p><b>Distancia de similitud:</b> {comparison.distance && comparison.distance.toFixed(2)}</p>
                                        <h3 style={{color: '#19e2c4', marginTop: '1rem'}}>Diferencias campo a campo:</h3>
                                        <ul style={{columns: 2, fontSize: '0.98em'}}>
                                            {comparison.fields && comparison.fields.map(f => (
                                                <li key={f}>
                                                    <b>{f}:</b> {comparison.values_this[f]?.toFixed(3)} (tu canción), {comparison.values_similar[f]?.toFixed(3)} (parecida), Δ {comparison.diff_with_similar[f] && comparison.diff_with_similar[f].toFixed(3)}
                                                </li>
                                            ))}
                                        </ul>
                                        <h3 style={{color: '#19e2c4', marginTop: '1rem'}}>Comparación con el promedio:</h3>
                                        <ul style={{columns: 2, fontSize: '0.98em'}}>
                                            {comparison.fields && comparison.fields.map(f => (
                                                <li key={f}>
                                                    <b>{f}:</b> Δ {comparison.diff_with_avg[f] && comparison.diff_with_avg[f].toFixed(3)} respecto al promedio
                                                </li>
                                            ))}
                                        </ul>
                                        <div style={{marginTop: '1rem'}}>
                                            <b>Duración:</b> {comparison.duration?.toFixed(2)}s<br/>
                                            <b>BPM:</b> {comparison.bpm?.toFixed(2)}<br/>
                                            <b>Género:</b> {comparison.genre}<br/>
                                            <b>Mood:</b> {comparison.mood}
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </form>
                </div>
            ) : (
                <div className="files-container">
                    <h1 className="files-title">Mis Archivos</h1>
                    
                    {loading ? (
                        <div className="loading">Cargando archivos...</div>
                    ) : uploadedFiles.length > 0 ? (
                        <div className="files-list">
                            {uploadedFiles.map((file) => (
                                <div key={file.id} className="file-card">
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
                                            className="download-button"
                                        >
                                            Descargar
                                        </a>
                                        {file.content_type.startsWith('image/') && (
                                            <a 
                                                href={file.file} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                className="view-button"
                                            >
                                                Ver
                                            </a>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="no-files">
                            <p>No has subido ningún archivo aún.</p>
                            <button 
                                className="upload-button-alt"
                                onClick={() => setActiveTab('upload')}
                            >
                                Subir tu primer archivo
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default Home;
