import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import { useState, useEffect } from "react";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import api from "../api";

function AdminRoute({ children }) {
    const [isAdmin, setIsAdmin] = useState(null);

    useEffect(() => {
        checkAdmin();
    }, []);

    const refreshToken = async () => {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN);
        try {
            const res = await api.post("/api/token/refresh/", {
                refresh: refreshToken,
            });
            if (res.status === 200) {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                const decodedNew = jwtDecode(res.data.access);
                console.log("Token Refresh - Payload:", decodedNew);
                setIsAdmin(decodedNew.is_superuser === true);
            } else {
                setIsAdmin(false);
            }
        } catch (error) {
            console.log(error);
            setIsAdmin(false);
        }
    };

    const checkAdmin = async () => {
        const token = localStorage.getItem(ACCESS_TOKEN);
        if (!token) {
            setIsAdmin(false);
            return;
        }

        const decoded = jwtDecode(token);
        console.log("Token Decoded - Payload:", decoded);
        const tokenExpiration = decoded.exp;
        const now = Date.now() / 1000;

        if (tokenExpiration < now) {
            await refreshToken();
        } else {
            // Verificar si el usuario es administrador
            console.log("Is Superuser:", decoded.is_superuser);
            setIsAdmin(decoded.is_superuser === true);
        }
    };

    if (isAdmin === null) {
        return <div>Verificando permisos...</div>;
    }

    return isAdmin ? children : <Navigate to="/" />;
}

export default AdminRoute; 