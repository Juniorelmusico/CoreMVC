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
            // Create FormData object para reconocimiento
            const formData = new FormData();
            formData.append("file", file);

            // Realizar la subida real al endpoint de reconocimiento
            const response = await api.post("/api/upload/", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            
            if (response.status === 201) {
                console.log("📦 Upload response data:", response.data);
                setMessage("¡Archivo subido con éxito! Reconociendo...");
                setUploadedFiles(prev => [response.data, ...prev]);
                setFile(null);
                setPreview(null);
                // Iniciar polling para reconocimiento
                if (response.data && response.data.id) {
                    console.log("🎯 Starting recognition for file ID:", response.data.id);
                    pollForRecognition(response.data.id);
                } else {
                    console.log("❌ No ID found in upload response:", response.data);
                    setMessage("Archivo subido, pero no se pudo iniciar el reconocimiento (falta ID)");
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

    // Polling para reconocimiento
    const pollForRecognition = async (fileId, tries = 0) => {
        setAnalysisPolling(true);
        setComparison(null);
        setPollingError("");
        const maxTries = 5; // Más intentos para reconocimiento
        const delay = 3000; // 3 segundos entre intentos
        try {
            console.log(`🔍 Attempting to fetch recognition for file ${fileId}, try ${tries + 1}`);
            const res = await api.get(`/api/recognition-status/${fileId}/`);
            
            if (res.data && res.data.status === 'found' && res.data.track) {
                // Canción reconocida exitosamente
                setComparison({
                    recognition: true,
                    track: res.data.track,
                    confidence: res.data.confidence,
                    processing_time: res.data.processing_time,
                    recognition_id: res.data.recognition_id
                });
                setMessage("¡Canción reconocida exitosamente!");
                setAnalysisPolling(false);
            } else if (res.data && res.data.status === 'not_found') {
                // Canción no encontrada en la base de datos
                setComparison({
                    not_found: true,
                    processing_time: res.data.processing_time
                });
                setMessage("Canción no encontrada en la base de datos.");
                setAnalysisPolling(false);
            } else if (res.data && res.data.status === 'processing') {
                // Aún procesando
                if (tries < maxTries) {
                    setTimeout(() => pollForRecognition(fileId, tries + 1), delay);
                } else {
                    setPollingError("El reconocimiento está tardando demasiado. Intenta más tarde.");
                    setAnalysisPolling(false);
                }
            } else if (res.data && res.data.status === 'error') {
                setPollingError("Error en el reconocimiento: " + (res.data.error || "Error desconocido"));
                setAnalysisPolling(false);
            } else if (tries < maxTries) {
                setTimeout(() => pollForRecognition(fileId, tries + 1), delay);
            } else {
                setPollingError("No se pudo completar el reconocimiento.");
                setAnalysisPolling(false);
            }
        } catch (err) {
            console.error(`❌ Recognition attempt ${tries + 1} failed:`, err);
            if (tries < maxTries) {
                setTimeout(() => pollForRecognition(fileId, tries + 1), delay);
            } else {
                setPollingError("Error de conexión durante el reconocimiento.");
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
                                {comparison.recognition ? (
                                    // Mostrar información de reconocimiento exitoso
                                    <>
                                        <h2 style={{color: '#19e2c4'}}>🎵 ¡Canción Reconocida!</h2>
                                        <div style={{background: '#1a2332', borderRadius: '8px', padding: '1rem', marginTop: '1rem'}}>
                                            <h3 style={{color: '#19e2c4', marginBottom: '0.5rem'}}>📝 Información de la Canción</h3>
                                            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.95em'}}>
                                                <p><b>Título:</b> {comparison.track.title}</p>
                                                <p><b>Artista:</b> {comparison.track.artist}</p>
                                                <p><b>Género:</b> {comparison.track.genre || 'Sin clasificar'}</p>
                                                <p><b>Mood:</b> {comparison.track.mood || 'Sin clasificar'}</p>
                                            </div>
                                        </div>
                                        
                                        <div style={{background: '#1a2332', borderRadius: '8px', padding: '1rem', marginTop: '1rem'}}>
                                            <h3 style={{color: '#19e2c4', marginBottom: '0.5rem'}}>📊 Estadísticas de Reconocimiento</h3>
                                            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.95em'}}>
                                                <p><b>Confianza:</b> {(comparison.confidence * 100).toFixed(1)}%</p>
                                                <p><b>Tiempo de procesamiento:</b> {comparison.processing_time?.toFixed(2)}s</p>
                                                <p><b>ID de reconocimiento:</b> {comparison.recognition_id}</p>
                                                <p><b>ID del track:</b> {comparison.track.id}</p>
                                            </div>
                                        </div>

                                        <div style={{marginTop: '1rem', padding: '0.75rem', background: '#0f1419', borderRadius: '6px', border: '1px solid #19e2c4'}}>
                                            <p style={{margin: 0, color: '#19e2c4', textAlign: 'center'}}>
                                                ✨ ¡Canción identificada con éxito! Confianza: {(comparison.confidence * 100).toFixed(1)}%
                                            </p>
                                        </div>
                                    </>
                                ) : comparison.not_found ? (
                                    // Mostrar mensaje de canción no encontrada
                                    <>
                                        <h2 style={{color: '#f39c12'}}>❓ Canción No Encontrada</h2>
                                        <div style={{background: '#1a2332', borderRadius: '8px', padding: '1rem', marginTop: '1rem'}}>
                                            <p style={{textAlign: 'center', fontSize: '1.1em', margin: '1rem 0'}}>
                                                Esta canción no está en nuestra base de datos de referencia.
                                            </p>
                                            {comparison.processing_time && (
                                                <p><b>Tiempo de procesamiento:</b> {comparison.processing_time.toFixed(2)}s</p>
                                            )}
                                            <div style={{marginTop: '1rem', padding: '0.75rem', background: '#0f1419', borderRadius: '6px', border: '1px solid #f39c12'}}>
                                                <p style={{margin: 0, color: '#f39c12', textAlign: 'center'}}>
                                                    💡 Puede ser una canción nueva o no incluida en nuestra base de datos
                                                </p>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    // Mostrar mensaje de procesamiento
                                    <>
                                        <h2 style={{color: '#19e2c4'}}>🎵 Procesando Reconocimiento</h2>
                                        <div style={{background: '#1a2332', borderRadius: '8px', padding: '1rem', marginTop: '1rem'}}>
                                            <p><b>📝 Título:</b> {comparison.track.track_title}</p>
                                            <p><b>🎤 Artista:</b> {comparison.track.artist_name}</p>
                                            <p><b>🔢 ID del Track:</b> {comparison.track.track_id}</p>
                                            <div style={{marginTop: '1rem', padding: '0.75rem', background: '#0f1419', borderRadius: '6px', border: '1px solid #19e2c4'}}>
                                                <p style={{margin: 0, color: '#19e2c4'}}>ℹ️ {comparison.message}</p>
                                            </div>
                                        </div>
                                        <div style={{marginTop: '1rem', fontSize: '0.9em', color: '#bbb'}}>
                                            <p>💡 El reconocimiento está tardando. Por favor, espera.</p>
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
