#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Track, Artist, Genre, Mood
from django.contrib.auth.models import User

# Obtener el usuario admin
admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'is_superuser': True})

# Crear géneros y moods
reggae, _ = Genre.objects.get_or_create(name='Reggae')
chill, _ = Mood.objects.get_or_create(name='Chill', defaults={'valence_score': 0.6})

# Crear el artista correcto
laid_back, _ = Artist.objects.get_or_create(name='Laid Back', user=admin_user)

# Buscar el track de Sunshine Reggae y corregirlo
tracks = Track.objects.filter(title__icontains='Sunshine Reggae')
for track in tracks:
    print(f"Corrigiendo track ID {track.id}: {track.title}")
    track.title = 'Sunshine Reggae'
    track.artist = laid_back
    track.genre = reggae
    track.mood = chill
    track.is_reference_track = True
    track.save()
    print(f"✅ Track corregido: {track.title} - {track.artist.name} - {track.genre.name} - {track.mood.name}")

print("¡Listo!") 