from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    def __str__(self):
        return self.title


class Artist(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artists')
    created_at = models.DateTimeField(auto_now_add=True)
    # Campos adicionales para metadatos
    description = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['name', 'user']


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Color para visualización en frontend
    color_code = models.CharField(max_length=7, default='#3498db')  # Hex color

    def __str__(self):
        return self.name


class Mood(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Valor numérico para análisis (ej: -1 a 1, donde -1 es triste, 1 es alegre)
    valence_score = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class Track(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='tracks')
    file = models.FileField(upload_to='tracks/')
    duration = models.FloatField(null=True, blank=True)  # in seconds
    bpm = models.FloatField(null=True, blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='tracks')
    mood = models.ForeignKey(Mood, on_delete=models.SET_NULL, null=True, related_name='tracks')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # CAMPOS NUEVOS PARA DEJAVU
    # ID único para vincular con Dejavu (song_name en Dejavu)
    dejavu_song_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Estado del fingerprinting
    fingerprint_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('completed', 'Completado'),
            ('error', 'Error'),
            ('not_found', 'No encontrado en base de datos')
        ],
        default='pending'
    )
    
    # Número de fingerprints generados
    fingerprints_count = models.IntegerField(default=0)
    
    # Error en caso de falla
    fingerprint_error = models.TextField(blank=True, null=True)
    
    # Metadatos adicionales de audio
    sample_rate = models.IntegerField(null=True, blank=True)
    channels = models.IntegerField(null=True, blank=True)
    bitrate = models.IntegerField(null=True, blank=True)
    
    # Campos para tracks de referencia (pre-registrados)
    is_reference_track = models.BooleanField(default=False)
    reference_source = models.CharField(max_length=100, blank=True, null=True)  # ej: "manual", "api", "batch"

    def __str__(self):
        return f"{self.title} - {self.artist.name}"

    def save(self, *args, **kwargs):
        # Generar dejavu_song_id si no existe
        if not self.dejavu_song_id:
            self.dejavu_song_id = f"track_{self.id}_{self.title.replace(' ', '_')}"
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['title', 'artist']


class Recognition(models.Model):
    """
    Modelo para almacenar resultados de reconocimiento de audio
    """
    # Audio subido por usuario (para reconocimiento)
    uploaded_file = models.ForeignKey('UploadedFile', on_delete=models.CASCADE, related_name='recognitions')
    
    # Track reconocido (si se encontró)
    recognized_track = models.ForeignKey(Track, on_delete=models.CASCADE, null=True, blank=True, related_name='recognitions')
    
    # Datos del reconocimiento
    confidence = models.FloatField(default=0.0)  # Confianza del reconocimiento (0-1)
    offset_seconds = models.FloatField(default=0.0)  # Offset en la canción original
    fingerprinted_confidence = models.IntegerField(default=0)  # Número de hashes coincidentes
    
    # Estado del reconocimiento
    recognition_status = models.CharField(
        max_length=20,
        choices=[
            ('processing', 'Procesando'),
            ('found', 'Encontrado'),
            ('not_found', 'No encontrado'),
            ('error', 'Error')
        ],
        default='processing'
    )
    
    # Metadatos adicionales
    processing_time = models.FloatField(null=True, blank=True)  # Tiempo de procesamiento en segundos
    recognition_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Resultado completo de Dejavu (JSON)
    dejavu_result = JSONField(null=True, blank=True)

    def __str__(self):
        if self.recognized_track:
            return f"Reconocido: {self.recognized_track.title} (Confianza: {self.confidence})"
        return f"Reconocimiento sin resultado para {self.uploaded_file.name}"

    class Meta:
        ordering = ['-created_at']


class Analysis(models.Model):
    """
    Modelo actualizado para análisis básico (mantenemos compatibilidad)
    """
    track = models.OneToOneField(Track, on_delete=models.CASCADE, related_name='analysis')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Características básicas de audio (usando pydub en lugar de librosa)
    duration_ms = models.IntegerField(null=True, blank=True)  # Duración en milisegundos
    frame_rate = models.IntegerField(null=True, blank=True)   # Sample rate
    channels_count = models.IntegerField(null=True, blank=True)  # Número de canales
    frame_width = models.IntegerField(null=True, blank=True)  # Bytes por sample
    max_amplitude = models.FloatField(null=True, blank=True)  # Amplitud máxima
    rms_amplitude = models.FloatField(null=True, blank=True)  # RMS amplitude
    
    # Metadatos del archivo
    file_format = models.CharField(max_length=10, null=True, blank=True)
    file_size_bytes = models.IntegerField(null=True, blank=True)
    
    # Análisis de calidad
    clipping_detected = models.BooleanField(default=False)
    silence_percentage = models.FloatField(null=True, blank=True)
    
    # Resultado del fingerprinting
    fingerprint_result = JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Analysis for {self.track.title}"


class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_files")
    
    # Nuevos campos para reconocimiento
    # Estado del procesamiento
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('completed', 'Completado'),
            ('error', 'Error')
        ],
        default='pending'
    )
    
    # Tipo de archivo subido
    file_purpose = models.CharField(
        max_length=20,
        choices=[
            ('recognition', 'Para reconocimiento'),
            ('reference', 'Track de referencia'),
            ('other', 'Otro')
        ],
        default='recognition'
    )
    
    def __str__(self):
        return self.name


class MusicFile(models.Model):
    """
    Modelo simplificado para compatibilidad
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='music_files/')
    duration = models.FloatField(null=True)  # Duration in seconds
    tempo = models.FloatField(null=True)  # BPM
    key = models.CharField(max_length=10, null=True)
    loudness = models.FloatField(null=True)  # RMS energy
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.artist}"