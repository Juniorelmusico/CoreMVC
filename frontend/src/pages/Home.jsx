import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import "../styles/Home.css";
import api from "../api";
import { ACCESS_TOKEN } from "../constants";
import { FaSpotify, FaApple, FaMusic, FaHistory } from 'react-icons/fa';

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
    const [showAnalysisHistory, setShowAnalysisHistory] = useState(false);
    const [analysisHistory, setAnalysisHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

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
                
                // ✅ CORREGIDO: Verificar si ya tenemos recognition_preview
                if (response.data.recognition_preview) {
                    const preview = response.data.recognition_preview;
                    console.log("🎯 Recognition preview encontrado:", preview);
                    
                    if (preview.status === 'found') {
                        // Ya tenemos el resultado completo, no hacer polling
                        setComparison({
                            recognition: true,
                            track: preview.track, // Puede ser null si no está en BD
                            confidence: preview.confidence,
                            processing_time: preview.processing_time,
                            recognition_id: preview.recognition_id,
                            audd_identified: preview.audd_identified,
                            comparison: preview.comparison,
                            message: preview.message
                        });
                        setAnalysisPolling(false);
                        // Guardar análisis
                        saveAnalysis({
                            id: response.data.id,
                            ...preview
                        });
                    } else if (preview.status === 'not_found') {
                        // Canción no encontrada
                        setComparison({
                            not_found: true,
                            processing_time: preview.processing_time,
                            message: preview.message
                        });
                        setMessage(preview.message || "Canción no encontrada en AudD.");
                        setAnalysisPolling(false);
                    } else if (preview.status === 'error') {
                        // Error en reconocimiento
                        if (preview.quota_exceeded) {
                            // Cuota agotada
                            setComparison({
                                quota_exceeded: true,
                                processing_time: preview.processing_time,
                                message: preview.message,
                                error: preview.error
                            });
                            setMessage("🚫 Límite diario de AudD alcanzado");
                        } else {
                            // Otro tipo de error
                            setPollingError("Error en el reconocimiento: " + preview.error);
                        }
                        setAnalysisPolling(false);
                    } else {
                        // Status desconocido, hacer polling por seguridad
                        console.log("⚠️ Status desconocido en preview, iniciando polling");
                        if (response.data.id) {
                            pollForRecognition(response.data.id);
                        }
                    }
                } else if (response.data && response.data.id) {
                    // No hay recognition_preview, hacer polling tradicional
                    console.log("🎯 No hay preview, iniciando polling para file ID:", response.data.id);
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
            
            // ✅ CORREGIDO: Verificar si ya tenemos resultado en el upload inicial
            if (comparison && comparison.recognition) {
                console.log("🎯 Ya tenemos resultado del upload inicial, no hacer polling");
                setAnalysisPolling(false);
                return;
            }
            
            // CASO 1: Canción reconocida (con o sin track en BD)
            if (res.data && res.data.status === 'found') {
                setComparison({
                    recognition: true,
                    track: res.data.track, // Puede ser null si no está en BD
                    confidence: res.data.confidence,
                    processing_time: res.data.processing_time,
                    recognition_id: res.data.recognition_id,
                    // *** NUEVA: Información real de AudD ***
                    audd_identified: res.data.audd_identified,
                    comparison: res.data.comparison,
                    message: res.data.message
                });
                setMessage(res.data.message || "¡Canción reconocida exitosamente!");
                setAnalysisPolling(false);
                // Guardar análisis
                saveAnalysis({
                    id: res.data.id,
                    ...res.data
                });
            } else if (res.data && res.data.status === 'not_found') {
                // CASO 2: Canción no encontrada en AudD
                setComparison({
                    not_found: true,
                    processing_time: res.data.processing_time,
                    message: res.data.message || "Canción no encontrada en la base de datos de AudD."
                });
                setMessage("Canción no encontrada en AudD.");
                setAnalysisPolling(false);
            } else if (res.data && res.data.status === 'processing') {
                // CASO 3: Aún procesando
                if (tries < maxTries) {
                    setTimeout(() => pollForRecognition(fileId, tries + 1), delay);
                } else {
                    setPollingError("El reconocimiento está tardando demasiado. Intenta más tarde.");
                    setAnalysisPolling(false);
                }
            } else if (res.data && res.data.status === 'error') {
                // CASO 4: Error en reconocimiento
                if (res.data.quota_exceeded) {
                    // Cuota agotada
                    setComparison({
                        quota_exceeded: true,
                        processing_time: res.data.processing_time,
                        message: res.data.message,
                        error: res.data.error
                    });
                    setMessage("🚫 Límite diario de AudD alcanzado");
                } else {
                    // Otro error
                    setPollingError("Error en el reconocimiento: " + (res.data.error || "Error desconocido"));
                }
                setAnalysisPolling(false);
            } else if (tries < maxTries) {
                // CASO 5: Respuesta inesperada, reintentar
                setTimeout(() => pollForRecognition(fileId, tries + 1), delay);
            } else {
                // CASO 6: Máximo de intentos alcanzado
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

    // Función para guardar análisis
    const saveAnalysis = async (analysisData) => {
        try {
            const token = localStorage.getItem(ACCESS_TOKEN);
            if (!token) {
                console.error('❌ No hay token de autenticación');
                return;
            }

            // Decodificar el token para obtener el ID del usuario
            const decodedToken = jwtDecode(token);
            const userId = decodedToken.user_id;

            if (!userId) {
                console.error('❌ No se pudo obtener el ID del usuario del token');
                return;
            }

            // Asegurarnos de que todos los campos requeridos estén presentes
            const data = {
                uploaded_file: analysisData.uploaded_file || analysisData.id,
                track: analysisData.track?.id || null,
                title: analysisData.track?.title || analysisData.audd_identified?.title || '',
                artist: analysisData.track?.artist || analysisData.audd_identified?.artist || '',
                genre: analysisData.track?.genre || null,
                mood: analysisData.track?.mood || null,
                spotify_id: analysisData.audd_identified?.spotify_id || null,
                apple_music_url: analysisData.audd_identified?.apple_music_url || null,
                confidence: analysisData.confidence || 0,
                processing_time: analysisData.processing_time || 0,
                user: userId  // Agregar el ID del usuario
            };

            console.log('📤 Enviando datos de análisis:', data);

            const response = await api.post('/api/save-music-analysis/', data);
            console.log('✅ Análisis guardado:', response.data);
        } catch (error) {
            console.error('❌ Error guardando análisis:', error);
            if (error.response) {
                console.error('Detalles del error:', error.response.data);
            }
        }
    };

    // Función para cargar historial de análisis
    const loadAnalysisHistory = async () => {
        setLoadingHistory(true);
        try {
            const response = await api.get('/api/music-analyses/');
            setAnalysisHistory(response.data);
        } catch (error) {
            console.error('Error cargando historial:', error);
        } finally {
            setLoadingHistory(false);
        }
    };

    // Modificar el useEffect para cargar historial cuando se muestra
    useEffect(() => {
        if (showAnalysisHistory) {
            loadAnalysisHistory();
        }
    }, [showAnalysisHistory]);

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
                <button 
                    className={`tab ${showAnalysisHistory ? 'active' : ''}`}
                    onClick={() => setShowAnalysisHistory(!showAnalysisHistory)}
                >
                    <FaHistory style={{marginRight: '0.5rem'}} />
                    Historial de Análisis
                </button>
                
                {isSuperuser && (
                    <Link to="/admin" className="admin-link">
                        Panel de Administración
                    </Link>
                )}
            </div>

            {showAnalysisHistory ? (
                <div className="analysis-history">
                    <h2>Historial de Análisis de Música</h2>
                    {loadingHistory ? (
                        <div className="loading">Cargando historial...</div>
                    ) : analysisHistory.length > 0 ? (
                        <div className="analysis-list">
                            {analysisHistory.map((analysis) => (
                                <div key={analysis.id} className="analysis-card">
                                    <div className="analysis-header">
                                        <h3>{analysis.title}</h3>
                                        <span className="analysis-date">
                                            {formatDate(analysis.created_at)}
                                        </span>
                                    </div>
                                    <div className="analysis-details">
                                        <p><b>Artista:</b> {analysis.artist}</p>
                                        <p><b>Género:</b> {analysis.genre || 'Sin clasificar'}</p>
                                        <p><b>Mood:</b> {analysis.mood || 'Sin clasificar'}</p>
                                        <p><b>Confianza:</b> {(analysis.confidence * 100).toFixed(1)}%</p>
                                    </div>
                                    <div className="analysis-links">
                                        {analysis.spotify_id && (
                                            <a 
                                                href={`https://open.spotify.com/track/${analysis.spotify_id}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="streaming-link spotify"
                                            >
                                                <FaSpotify /> Spotify
                                            </a>
                                        )}
                                        {analysis.apple_music_url && (
                                            <a 
                                                href={analysis.apple_music_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="streaming-link apple"
                                            >
                                                <FaApple /> Apple Music
                                            </a>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="no-analyses">
                            <p>No hay análisis guardados aún.</p>
                        </div>
                    )}
                </div>
            ) : (
                activeTab === 'upload' ? (
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
                                            <h2 style={{color: '#19e2c4'}}>🎵 Canción Identificada</h2>
                                            
                                            {/* INFORMACIÓN DE LA BASE DE DATOS */}
                                            {comparison.track && (
                                                <div style={{background: '#1a4741', borderRadius: '8px', padding: '1rem', marginTop: '1rem', border: '2px solid #19e2c4'}}>
                                                    <h3 style={{color: '#19e2c4', marginBottom: '0.5rem', display: 'flex', alignItems: 'center'}}>
                                                        <FaMusic style={{marginRight: '0.5rem'}} /> Información de la Canción
                                                    </h3>
                                                    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.95em'}}>
                                                        <p><b>📝 Título:</b> {comparison.track.title}</p>
                                                        <p><b>👨‍🎤 Artista:</b> {comparison.track.artist}</p>
                                                        <p><b>🎸 Género:</b> {comparison.track.genre || 'Sin clasificar'}</p>
                                                        <p><b>😊 Mood:</b> {comparison.track.mood || 'Sin clasificar'}</p>
                                                    </div>

                                                    {/* Enlaces de Streaming */}
                                                    {comparison.audd_identified && (
                                                        <div style={{marginTop: '1rem', display: 'flex', gap: '1rem', justifyContent: 'center'}}>
                                                            {comparison.audd_identified.spotify_id && (
                                                                <a 
                                                                    href={`https://open.spotify.com/track/${comparison.audd_identified.spotify_id}`}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    style={{
                                                                        background: '#1DB954',
                                                                        color: 'white',
                                                                        padding: '0.5rem 1rem',
                                                                        borderRadius: '20px',
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        gap: '0.5rem',
                                                                        textDecoration: 'none',
                                                                        transition: 'transform 0.2s'
                                                                    }}
                                                                    onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                                                                    onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                                                                >
                                                                    <FaSpotify size={20} />
                                                                    <span>Escuchar en Spotify</span>
                                                                </a>
                                                            )}
                                                            
                                                            {comparison.audd_identified.apple_music_url && (
                                                                <a 
                                                                    href={comparison.audd_identified.apple_music_url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    style={{
                                                                        background: '#FB2D3F',
                                                                        color: 'white',
                                                                        padding: '0.5rem 1rem',
                                                                        borderRadius: '20px',
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        gap: '0.5rem',
                                                                        textDecoration: 'none',
                                                                        transition: 'transform 0.2s'
                                                                    }}
                                                                    onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                                                                    onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                                                                >
                                                                    <FaApple size={20} />
                                                                    <span>Escuchar en Apple Music</span>
                                                                </a>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {/* MENSAJE CUANDO NO HAY TRACK EN BD */}
                                            {!comparison.track && (
                                                <div style={{background: '#2a1810', borderRadius: '8px', padding: '1rem', marginTop: '1rem', border: '1px solid #ffa500'}}>
                                                    <h3 style={{color: '#ffa500', marginBottom: '0.5rem'}}>ℹ️ Información</h3>
                                                    <div style={{fontSize: '0.9em', textAlign: 'center', color: '#ffa500'}}>
                                                        <p>🔍 Esta canción no existe en tu base de datos</p>
                                                        <p style={{fontSize: '0.8em', color: '#ccc', marginTop: '0.5rem'}}>
                                                            Puedes agregar esta información a tu BD manualmente si lo deseas.
                                                        </p>
                                                    </div>
                                                </div>
                                            )}
                                            
                                            <div style={{marginTop: '1rem', padding: '0.75rem', background: '#0f1419', borderRadius: '6px', border: '1px solid #19e2c4'}}>
                                                <p style={{margin: 0, color: '#19e2c4', textAlign: 'center'}}>
                                                    {comparison.message || `✨ ¡Canción identificada con éxito!`}
                                                </p>
                                            </div>
                                        </>
                                    ) : comparison.not_found ? (
                                        // Mostrar mensaje de canción no encontrada
                                        <>
                                            <h2 style={{color: '#f39c12'}}>❓ Canción No Encontrada en AudD</h2>
                                            <div style={{background: '#1a2332', borderRadius: '8px', padding: '1rem', marginTop: '1rem'}}>
                                                <p style={{textAlign: 'center', fontSize: '1.1em', margin: '1rem 0'}}>
                                                    {comparison.message || 'Esta canción no está en la base de datos de AudD.'}
                                                </p>
                                                {comparison.processing_time && (
                                                    <p><b>Tiempo de procesamiento:</b> {comparison.processing_time.toFixed(2)}s</p>
                                                )}
                                                <div style={{marginTop: '1rem', padding: '0.75rem', background: '#0f1419', borderRadius: '6px', border: '1px solid #f39c12'}}>
                                                    <p style={{margin: 0, color: '#f39c12', textAlign: 'center'}}>
                                                        💡 AudD no pudo identificar esta canción. Puede ser muy nueva, muy rara, o de calidad de audio insuficiente.
                                                    </p>
                                                </div>
                                            </div>
                                        </>
                                    ) : comparison.quota_exceeded ? (
                                        // Mostrar mensaje de cuota agotada
                                        <>
                                            <h2 style={{color: '#e74c3c'}}>🚫 Límite de API Alcanzado</h2>
                                            <div style={{background: '#2c1810', borderRadius: '8px', padding: '1.5rem', marginTop: '1rem', border: '2px solid #e74c3c'}}>
                                                <div style={{textAlign: 'center'}}>
                                                    <h3 style={{color: '#e74c3c', marginBottom: '1rem'}}>⏰ Cuota Diaria Agotada</h3>
                                                    <p style={{fontSize: '1.1em', margin: '1rem 0', color: '#fff'}}>
                                                        Has alcanzado el límite de <strong>25 reconocimientos gratuitos</strong> por día de AudD.
                                                    </p>
                                                    
                                                    <div style={{background: '#1a1210', borderRadius: '6px', padding: '1rem', margin: '1rem 0', border: '1px solid #e74c3c'}}>
                                                        <h4 style={{color: '#ffa500', marginBottom: '0.5rem'}}>📋 Opciones:</h4>
                                                        <ul style={{textAlign: 'left', color: '#ccc', fontSize: '0.9em'}}>
                                                            <li>⏳ <strong>Esperar hasta mañana</strong> (la cuota se renueva cada 24 horas)</li>
                                                            <li>💳 <strong>Crear cuenta AudD premium</strong> para más reconocimientos</li>
                                                            <li>🔄 <strong>Usar ACRCloud</strong> (más preciso pero comercial)</li>
                                                            <li>🎵 <strong>Usar tu base de datos local</strong> para canciones que ya tienes</li>
                                                        </ul>
                                                    </div>
                                                    
                                                    {comparison.processing_time && (
                                                        <p style={{fontSize: '0.8em', color: '#888'}}>
                                                            Tiempo de procesamiento: {comparison.processing_time.toFixed(2)}s
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        </>
                                    ) : null}
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
                )
            )}
        </div>
    );
}

export default Home;
