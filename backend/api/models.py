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

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Mood(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

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
    analysis_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('error', 'Error')
        ],
        default='pending'
    )
    analysis_error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.artist.name}"

class Analysis(models.Model):
    track = models.OneToOneField(Track, on_delete=models.CASCADE, related_name='analysis')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Características acústicas
    energy = models.FloatField(null=True, blank=True)
    danceability = models.FloatField(null=True, blank=True)
    valence = models.FloatField(null=True, blank=True)  # Positividad de la canción
    acousticness = models.FloatField(null=True, blank=True)
    instrumentalness = models.FloatField(null=True, blank=True)
    liveness = models.FloatField(null=True, blank=True)
    speechiness = models.FloatField(null=True, blank=True)
    
    # Detalles técnicos
    key = models.CharField(max_length=10, null=True, blank=True)
    mode = models.CharField(max_length=10, null=True, blank=True)
    time_signature = models.IntegerField(null=True, blank=True)
    
    # Análisis espectral
    spectral_centroid = models.FloatField(null=True, blank=True)
    spectral_bandwidth = models.FloatField(null=True, blank=True)
    spectral_rolloff = models.FloatField(null=True, blank=True)
    
    # Resultado de comparación
    comparison_result = JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Analysis for {self.track.title}"

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_files")
    
    def __str__(self):
        return self.name

class MusicFile(models.Model):
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