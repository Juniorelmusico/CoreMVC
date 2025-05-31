import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Time zone configuration
TIME_ZONE = 'UTC'

# Configuración de Celery para modo desarrollo (sin Redis)
CELERY_TASK_ALWAYS_EAGER = True  # Ejecutar tareas síncronamente
CELERY_TASK_EAGER_PROPAGATES = True  # Propagar errores
CELERY_BROKER_URL = None  # No usar broker en modo desarrollo
CELERY_RESULT_BACKEND = None  # No usar backend en modo desarrollo

# Configuración antigua (comentada para desarrollo)
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB 