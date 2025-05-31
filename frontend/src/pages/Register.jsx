import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/Auth.css";

function Register() {
    const [formData, setFormData] = useState({
        email: "",
        username: "",
        password: "",
        confirmPassword: ""
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            await api.post("/api/user/register/", {
                username: formData.username,
                email: formData.email,
                password: formData.password,
                confirm_password: formData.confirmPassword
            });
            navigate("/login");
        } catch (error) {
            // Mostrar mensaje del backend, o uno genérico
            let msg = error.response?.data?.detail || "Error al registrar usuario";
            // Si el backend devuelve un diccionario de errores
            if (error.response?.data) {
                const data = error.response.data;
                if (typeof data === 'object') {
                    msg = Object.values(data).flat().join(' ');
                }
            }
            setError(msg);
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
                <h2 className="auth-card-title">Crea tu cuenta</h2>
                <form onSubmit={handleSubmit}>
                    {error && <div className="auth-error">{error}</div>}
                    <label className="auth-label" htmlFor="email">Correo electrónico</label>
                    <input
                        className="auth-input"
                        id="email"
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="tu@email.com"
                        required
                    />
                    <label className="auth-label" htmlFor="username">Nombre de usuario</label>
                    <input
                        className="auth-input"
                        id="username"
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        placeholder="Tu nombre de usuario"
                        required
                    />
                    <label className="auth-label" htmlFor="password">Contraseña</label>
                    <input
                        className="auth-input"
                        id="password"
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="••••••••"
                        required
                    />
                    <label className="auth-label" htmlFor="confirmPassword">Confirmar contraseña</label>
                    <input
                        className="auth-input"
                        id="confirmPassword"
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        placeholder="••••••••"
                        required
                    />
                    <button className="auth-button" type="submit" disabled={loading}>
                        {loading ? "Registrando..." : "Crear cuenta"}
                    </button>
                </form>
                <div className="auth-footer">
                    ¿Ya tienes una cuenta? <a className="auth-link" href="/login">Inicia sesión</a>
                </div>
            </div>
            <footer className="auth-copyright">© 2025 Melocuore. Todos los derechos reservados.</footer>
        </div>
    );
}

export default Register;