import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import "../styles/Auth.css";

function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [remember, setRemember] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            const res = await api.post("/api/token/", { username, password });
            localStorage.setItem(ACCESS_TOKEN, res.data.access);
            localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
            navigate("/");
        } catch (error) {
            setError(error.response?.data?.detail || "Error al iniciar sesión");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-bg">
            <div className="auth-header">
                <h1 className="auth-title">Melocuore</h1>
                <p className="auth-subtitle">Plataforma de análisis de audio para DJs y productores</p>
            </div>
            <div className="auth-card">
                <h2 className="auth-card-title">Bienvenido de nuevo</h2>
                <form onSubmit={handleSubmit}>
                    {error && <div className="auth-error">{error}</div>}
                    <label className="auth-label" htmlFor="username">Nombre de usuario</label>
                    <input
                        className="auth-input"
                        id="username"
                        type="text"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        placeholder="Tu nombre de usuario"
                        required
                    />
                    <label className="auth-label" htmlFor="password">Contraseña</label>
                    <input
                        className="auth-input"
                        id="password"
                        type="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                    />
                    <div className="auth-row">
                        {/* Eliminado: Checkbox y etiqueta 'Recuérdame' */}
                    </div>
                    <button className="auth-button" type="submit" disabled={loading}>
                        {loading ? "Iniciando sesión..." : "Iniciar sesión"}
                    </button>
                </form>
                <div className="auth-footer">
                    ¿No tienes una cuenta? <a className="auth-link" href="/register">Regístrate</a>
                </div>
            </div>
            <footer className="auth-copyright">© 2025 Melocuore. Todos los derechos reservados.</footer>
        </div>
    );
}

export default Login;