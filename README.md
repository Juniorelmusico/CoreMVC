# 🎵 Sistema de Reconocimiento de Música

Un sistema full-stack para el reconocimiento y análisis de música, construido con Django y React.

## 🌟 Características Principales

- 🎯 Reconocimiento de música en tiempo real
- 🔄 Integración con AudD API
- 🎨 Interfaz moderna con efectos visuales
- 📊 Análisis detallado de canciones
- 🔒 Sistema de autenticación seguro
- 🎧 Soporte para múltiples formatos de audio
- 📱 Diseño responsive

## 🛠️ Tecnologías Utilizadas

### Backend
- Python 3.8+
- Django 4.2
- Django REST Framework
- PostgreSQL
- AudD API
- Librosa (procesamiento de audio)

### Frontend
- React 18
- Vite
- Axios
- React Router
- Styled Components
- Material-UI

## 📋 Requisitos Previos

- Python 3.8 o superior
- Node.js 16 o superior
- PostgreSQL
- API Key de AudD

## 🚀 Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/music-recognition-system.git
cd music-recognition-system
```

2. **Configurar el Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configurar la Base de Datos**
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Configurar Variables de Entorno**
Crear un archivo `.env` en la carpeta `backend`:
```env
DEBUG=True
SECRET_KEY=tu_secret_key
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nombre_db
AUDD_API_TOKEN=tu_token_audd
```

5. **Configurar el Frontend**
```bash
cd frontend
npm install
```

## 🏃‍♂️ Ejecución

1. **Iniciar el Backend**
```bash
cd backend
python manage.py runserver
```

2. **Iniciar el Frontend**
```bash
cd frontend
npm run dev
```

## 📁 Estructura del Proyecto

```
music-recognition-system/
├── backend/
│   ├── api/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── services/
│   ├── config/
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   └── package.json
└── README.md
```

## 🔍 Funcionalidades Detalladas

### Reconocimiento de Música
- Subida de archivos de audio
- Procesamiento en tiempo real
- Comparación con base de datos local
- Integración con AudD API
- Visualización de resultados

### Gestión de Usuarios
- Registro y autenticación
- Perfiles de usuario
- Historial de reconocimientos
- Gestión de favoritos

### Análisis de Audio
- Extracción de características
- Fingerprinting de audio
- Comparación de similitud
- Visualización de espectrogramas

## 🔒 Seguridad

- Autenticación JWT
- Validación de archivos
- Protección contra ataques
- Manejo seguro de API keys
- Cifrado de datos sensibles

## 🧪 Testing

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```

## 📈 Optimizaciones

- Caché de fingerprints
- Procesamiento asíncrono
- Lazy loading
- Compresión de archivos
- Optimización de consultas

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles.

## 👥 Autores

- Tu Nombre - [@tu-usuario](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- AudD API por el servicio de reconocimiento de música
- La comunidad de Django y React
- Todos los contribuidores del proyecto

## 📞 Soporte

Para soporte, email tu@email.com o crear un issue en el repositorio.

## 🔄 Actualizaciones Futuras

- [ ] Integración con más servicios de música
- [ ] Análisis de letras
- [ ] Recomendaciones personalizadas
- [ ] Aplicación móvil
- [ ] API pública

---

⭐️ Si te gusta el proyecto, no olvides darle una estrella en GitHub!

⌨️ with ❤️ by Junior Espin 

## 🎤 Deploy
https://d4a892c7-6446-4a2d-b9de-cee972a1db3a.e1-us-east-azure.choreoapps.dev

## 🎵 Video Youtube
https://youtu.be/fBV4Kan45R4




