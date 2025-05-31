# 🎵 Migración a Dejavu - Guía Completa

Esta guía te ayudará a migrar tu proyecto de Librosa a Dejavu para crear un sistema de reconocimiento de audio tipo Shazam.

## 📦 1. Instalación de Dependencias

### Instalar nuevas dependencias:
```bash
cd backend
pip install -r requirements.txt
```

### Dependencias principales agregadas:
- `dejavu==1.0.2` - Librería principal de fingerprinting
- `PyDejavu==0.1.5` - Wrapper adicional
- `pydub==0.25.1` - Procesamiento de audio básico

## 🗄️ 2. Configuración de Base de Datos

### Crear migraciones para los nuevos modelos:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Variables de entorno requeridas (.env):
```env
# Base de datos PostgreSQL (requerido para Dejavu)
DB_HOST=localhost
DB_USER=postgres
DB_PWD=tu_password
DB_NAME=melocuore_db
DB_PORT=5432

# Redis para Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🔧 3. Configuración Inicial

### Ejecutar comando de configuración:
```bash
# Probar conexión con Dejavu
python manage.py setup_dejavu --test-dejavu

# Crear datos de ejemplo (géneros y moods)
python manage.py setup_dejavu --create-sample-data

# Generar fingerprints para tracks existentes
python manage.py setup_dejavu --fingerprint-existing
```

## 🚀 4. Iniciar Servicios

### Terminal 1 - Redis:
```bash
redis-server
```

### Terminal 2 - Celery Worker:
```bash
cd backend
celery -A melocuore worker -l info
```

### Terminal 3 - Django Server:
```bash
cd backend
python manage.py runserver
```

## 📡 5. Nuevos Endpoints de API

### Reconocimiento de Audio (tipo Shazam):
```http
# Subir archivo para reconocimiento
POST /api/upload/
Content-Type: multipart/form-data
{
  "file": archivo_audio.mp3
}

# Verificar estado del reconocimiento
GET /api/recognition-status/{file_id}/

# Listar reconocimientos del usuario
GET /api/recognitions/

# Detalles de un reconocimiento específico
GET /api/recognitions/{recognition_id}/
```

### Gestión de Tracks de Referencia:
```http
# Subir track de referencia (para fingerprinting)
POST /api/api/tracks/upload/
Content-Type: multipart/form-data
{
  "title": "Nombre de la canción",
  "artist_name": "Nombre del artista",
  "file": archivo_audio.mp3
}

# Regenerar fingerprint de un track
POST /api/api/tracks/{track_id}/regenerate_fingerprint/

# Fingerprinting en batch
POST /api/api/tracks/batch_fingerprint/
{
  "track_ids": [1, 2, 3, 4, 5]
}
```

## 🔄 6. Flujo de Trabajo

### Para Administradores (Registrar canciones de referencia):

1. **Subir track de referencia:**
   ```python
   # El track se guarda con is_reference_track=True
   # Se inicia automáticamente el fingerprinting con Celery
   ```

2. **Monitorear fingerprinting:**
   ```python
   # Estado: pending -> processing -> completed/error
   # Ver progreso en admin panel o API
   ```

### Para Usuarios (Reconocer canciones):

1. **Subir archivo para reconocimiento:**
   ```python
   # El archivo se procesa automáticamente
   # Se busca coincidencia en la base de fingerprints
   ```

2. **Obtener resultados:**
   ```python
   # Si se encuentra: datos del track (título, artista, género, mood)
   # Si no se encuentra: mensaje de "no encontrado"
   ```

## 📊 7. Modelos de Datos Actualizados

### Track (actualizado):
```python
class Track(models.Model):
    # Campos existentes...
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    file = models.FileField(upload_to='tracks/')
    
    # NUEVOS CAMPOS PARA DEJAVU
    dejavu_song_id = models.CharField(max_length=255, unique=True)
    fingerprint_status = models.CharField(max_length=20)  # pending/processing/completed/error
    fingerprints_count = models.IntegerField(default=0)
    fingerprint_error = models.TextField(blank=True, null=True)
    is_reference_track = models.BooleanField(default=False)
```

### Recognition (nuevo):
```python
class Recognition(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    recognized_track = models.ForeignKey(Track, on_delete=models.CASCADE, null=True)
    confidence = models.FloatField(default=0.0)
    offset_seconds = models.FloatField(default=0.0)
    recognition_status = models.CharField(max_length=20)  # processing/found/not_found/error
    dejavu_result = JSONField(null=True, blank=True)
```

## 🛠️ 8. Tareas de Celery

### Fingerprinting de Tracks:
```python
from api.tasks import fingerprint_track

# Generar fingerprint para un track
fingerprint_track.delay(track_id)
```

### Reconocimiento de Audio:
```python
from api.tasks import recognize_audio_file

# Reconocer archivo subido
recognize_audio_file.delay(uploaded_file_id)
```

### Procesamiento en Batch:
```python
from api.tasks import batch_fingerprint_tracks

# Procesar múltiples tracks
batch_fingerprint_tracks.delay([1, 2, 3, 4, 5])
```

## 🔍 9. Ejemplo de Uso Completo

### Registrar canción de referencia:
```python
# 1. Admin sube track de referencia
POST /api/api/tracks/upload/
{
  "title": "Bohemian Rhapsody",
  "artist_name": "Queen",
  "file": bohemian_rhapsody.mp3
}

# 2. Sistema genera fingerprint automáticamente
# 3. Track queda disponible para reconocimiento
```

### Reconocer canción:
```python
# 1. Usuario sube fragmento de audio
POST /api/upload/
{
  "file": fragmento_audio.mp3
}

# 2. Sistema busca coincidencias
# 3. Respuesta:
{
  "success": true,
  "track": {
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "genre": "Rock",
    "mood": "Dramatic"
  },
  "confidence": 0.95,
  "offset_seconds": 45.2
}
```

## 🚨 10. Troubleshooting

### Error de conexión con PostgreSQL:
```bash
# Verificar que PostgreSQL esté corriendo
sudo service postgresql start

# Verificar credenciales en .env
```

### Error de conexión con Redis:
```bash
# Verificar que Redis esté corriendo
redis-cli ping

# Debería responder: PONG
```

### Fingerprinting falla:
```bash
# Verificar formato de archivo (solo MP3/WAV)
# Verificar que el archivo no esté corrupto
# Revisar logs de Celery
```

### No se encuentran coincidencias:
```bash
# Verificar que hay tracks de referencia fingerprinted
python manage.py setup_dejavu --test-dejavu

# Verificar calidad del audio subido
# El fragmento debe ser de al menos 10-15 segundos
```

## 📈 11. Monitoreo y Estadísticas

### Dashboard de administrador:
- Total de tracks fingerprinted
- Reconocimientos exitosos vs fallidos
- Tiempo promedio de procesamiento
- Estadísticas de uso por usuario

### Comandos útiles:
```bash
# Ver estadísticas
python manage.py setup_dejavu --test-dejavu

# Limpiar fingerprints huérfanos
python manage.py shell
>>> from api.tasks import cleanup_orphaned_fingerprints
>>> cleanup_orphaned_fingerprints.delay()
```

## 🎯 12. Diferencias Clave vs Librosa

| Aspecto | Librosa (Anterior) | Dejavu (Nuevo) |
|---------|-------------------|----------------|
| **Propósito** | Análisis de características | Reconocimiento de audio |
| **Salida** | Métricas numéricas | Identificación de canciones |
| **Base de datos** | Análisis individual | Base de fingerprints |
| **Velocidad** | Lento (análisis completo) | Rápido (matching) |
| **Uso** | Análisis musical | Identificación tipo Shazam |

¡Tu sistema ahora funciona como Shazam! 🎵✨ 