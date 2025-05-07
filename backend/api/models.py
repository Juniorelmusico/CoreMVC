from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    def __str__(self):
        return self.title


class Artist(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Mood(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Track(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    mood = models.ForeignKey(Mood, on_delete=models.SET_NULL, null=True)
    duration = models.FloatField()  # Duration in seconds
    bpm = models.IntegerField()
    file = models.FileField(upload_to='tracks/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Analysis(models.Model):
    track = models.OneToOneField(Track, on_delete=models.CASCADE)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField()  # Store analysis details as JSON

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