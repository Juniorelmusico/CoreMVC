from django.core.management.base import BaseCommand
from api.models import Track, Artist, Genre, Mood, Analysis
import random

# Ejemplos realistas
TRACKS = [
    {"title": "Sunset Drive", "artist": "Daft Punk", "genre": "Electronic", "mood": "Energetic", "bpm": 124, "duration": 210},
    {"title": "Morning Jazz", "artist": "Miles Davis", "genre": "Jazz", "mood": "Calm", "bpm": 98, "duration": 320},
    {"title": "Rock Anthem", "artist": "Queen", "genre": "Rock", "mood": "Energetic", "bpm": 140, "duration": 250},
    {"title": "Chill Vibes", "artist": "Bonobo", "genre": "Ambient", "mood": "Calm", "bpm": 90, "duration": 300},
    {"title": "Latin Heat", "artist": "Shakira", "genre": "Latin", "mood": "Happy", "bpm": 110, "duration": 230},
    {"title": "Night City", "artist": "The Weeknd", "genre": "Electronic", "mood": "Energetic", "bpm": 128, "duration": 200},
    {"title": "Blue Moon", "artist": "Norah Jones", "genre": "Jazz", "mood": "Calm", "bpm": 85, "duration": 260},
    {"title": "Power Rock", "artist": "AC/DC", "genre": "Rock", "mood": "Energetic", "bpm": 150, "duration": 240},
    {"title": "Ambient Dreams", "artist": "Brian Eno", "genre": "Ambient", "mood": "Calm", "bpm": 70, "duration": 400},
    {"title": "Fiesta Latina", "artist": "J Balvin", "genre": "Latin", "mood": "Happy", "bpm": 105, "duration": 220},
    {"title": "Electro Rush", "artist": "Calvin Harris", "genre": "Electronic", "mood": "Energetic", "bpm": 130, "duration": 215},
    {"title": "Smooth Jazz", "artist": "Kenny G", "genre": "Jazz", "mood": "Calm", "bpm": 95, "duration": 310},
    {"title": "Classic Rock", "artist": "The Beatles", "genre": "Rock", "mood": "Happy", "bpm": 120, "duration": 210},
    {"title": "Deep Space", "artist": "Moby", "genre": "Ambient", "mood": "Calm", "bpm": 80, "duration": 350},
    {"title": "Samba Party", "artist": "Sergio Mendes", "genre": "Latin", "mood": "Happy", "bpm": 115, "duration": 240},
    {"title": "Techno Beat", "artist": "Charlotte de Witte", "genre": "Electronic", "mood": "Energetic", "bpm": 132, "duration": 220},
    {"title": "Jazz Night", "artist": "John Coltrane", "genre": "Jazz", "mood": "Calm", "bpm": 100, "duration": 330},
    {"title": "Hard Rock", "artist": "Metallica", "genre": "Rock", "mood": "Energetic", "bpm": 145, "duration": 260},
    {"title": "Ocean Waves", "artist": "Tycho", "genre": "Ambient", "mood": "Calm", "bpm": 75, "duration": 370},
    {"title": "Baila Conmigo", "artist": "Selena", "genre": "Latin", "mood": "Happy", "bpm": 108, "duration": 225},
    {"title": "Future Bass", "artist": "Flume", "genre": "Electronic", "mood": "Energetic", "bpm": 135, "duration": 205},
    {"title": "Jazz Sunrise", "artist": "Herbie Hancock", "genre": "Jazz", "mood": "Calm", "bpm": 92, "duration": 315},
    {"title": "Pop Rock", "artist": "Maroon 5", "genre": "Rock", "mood": "Happy", "bpm": 122, "duration": 215},
    {"title": "Silent Night", "artist": "Ólafur Arnalds", "genre": "Ambient", "mood": "Calm", "bpm": 60, "duration": 410},
    {"title": "Ritmo Latino", "artist": "Marc Anthony", "genre": "Latin", "mood": "Happy", "bpm": 112, "duration": 235},
    {"title": "Synthwave Ride", "artist": "The Midnight", "genre": "Electronic", "mood": "Energetic", "bpm": 126, "duration": 218},
    {"title": "Jazz Lounge", "artist": "Esperanza Spalding", "genre": "Jazz", "mood": "Calm", "bpm": 97, "duration": 325},
    {"title": "Garage Rock", "artist": "The Strokes", "genre": "Rock", "mood": "Energetic", "bpm": 138, "duration": 245},
    {"title": "Dreamscape", "artist": "Aphex Twin", "genre": "Ambient", "mood": "Calm", "bpm": 78, "duration": 390},
    {"title": "Fiesta en la Playa", "artist": "Carlos Vives", "genre": "Latin", "mood": "Happy", "bpm": 118, "duration": 228},
    {"title": "EDM Party", "artist": "Martin Garrix", "genre": "Electronic", "mood": "Energetic", "bpm": 140, "duration": 212},
    {"title": "Jazz Fusion", "artist": "Pat Metheny", "genre": "Jazz", "mood": "Calm", "bpm": 102, "duration": 335},
    {"title": "Indie Rock", "artist": "Arctic Monkeys", "genre": "Rock", "mood": "Energetic", "bpm": 128, "duration": 225},
    {"title": "Ambient Light", "artist": "Nils Frahm", "genre": "Ambient", "mood": "Calm", "bpm": 72, "duration": 360},
    {"title": "Salsa Night", "artist": "Rubén Blades", "genre": "Latin", "mood": "Happy", "bpm": 114, "duration": 238},
    {"title": "Electro Pop", "artist": "Robyn", "genre": "Electronic", "mood": "Energetic", "bpm": 125, "duration": 208},
    {"title": "Jazz Ballad", "artist": "Bill Evans", "genre": "Jazz", "mood": "Calm", "bpm": 88, "duration": 340},
    {"title": "Classic Rock 2", "artist": "The Rolling Stones", "genre": "Rock", "mood": "Energetic", "bpm": 132, "duration": 255},
    {"title": "Ambient Forest", "artist": "Sigur Rós", "genre": "Ambient", "mood": "Calm", "bpm": 68, "duration": 380},
    {"title": "Cumbia Party", "artist": "Los Ángeles Azules", "genre": "Latin", "mood": "Happy", "bpm": 120, "duration": 232},
]

GENRES = ["Electronic", "Jazz", "Rock", "Ambient", "Latin"]
MOODS = ["Energetic", "Calm", "Happy"]

class Command(BaseCommand):
    help = 'Carga pistas y análisis realistas de ejemplo en la base de datos.'

    def handle(self, *args, **kwargs):
        # Crea géneros y moods si no existen
        for genre in GENRES:
            Genre.objects.get_or_create(name=genre)
        for mood in MOODS:
            Mood.objects.get_or_create(name=mood)

        for t in TRACKS:
            artist, _ = Artist.objects.get_or_create(name=t["artist"], defaults={"user_id": 1})
            genre = Genre.objects.get(name=t["genre"])
            mood = Mood.objects.get(name=t["mood"])
            track, created = Track.objects.get_or_create(
                title=t["title"],
                artist=artist,
                genre=genre,
                mood=mood,
                bpm=t["bpm"],
                duration=t["duration"],
                defaults={"file": "tracks/fake.mp3", "analysis_status": "completed"}
            )
            if created:
                # Crea un análisis con datos aleatorios realistas
                Analysis.objects.create(
                    track=track,
                    energy=random.uniform(0.3, 0.9),
                    danceability=random.uniform(0.3, 0.9),
                    valence=random.uniform(0.3, 0.9),
                    acousticness=random.uniform(0.1, 0.7),
                    instrumentalness=random.uniform(0.1, 0.7),
                    liveness=random.uniform(0.1, 0.7),
                    speechiness=random.uniform(0.1, 0.7),
                    spectral_centroid=random.uniform(1000, 4000),
                    spectral_bandwidth=random.uniform(1000, 4000),
                    spectral_rolloff=random.uniform(1000, 4000),
                )
                self.stdout.write(self.style.SUCCESS(f'Pista creada: {track.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Pista ya existente: {track.title}'))
        self.stdout.write(self.style.SUCCESS('¡Pistas realistas precargadas correctamente!')) 