import random
from django.core.management.base import BaseCommand
from api.models import Track, Artist, Genre, Mood

TITLES = [
    "Sunrise Beat", "Night Drive", "Electric Dreams", "Chill Vibes", "Funky Town", "Jazz in Paris", "Rock the World", "Pop Star", "Hip-Hop Flow", "Ambient Space",
    "Classical Morning", "Metal Storm", "Reggaeton Party", "Soul Groove", "Techno Pulse", "Trance Vision", "House Party", "Downtempo Chill", "Latin Heat", "Urban Nights",
    "Synthwave Ride", "Disco Fever", "Punk Energy", "Orchestral Suite", "Trap City", "Smooth Jazz", "Hard Rock", "Deep House", "Electro Swing", "Chillstep",
    "Future Bass", "Moody Blues", "Dancefloor", "Acoustic Sunset", "Vocal House", "Dream Pop", "Garage Rock", "Dubstep Drop", "Indie Anthem", "Lo-Fi Study"
]

def random_or_none(qs):
    return random.choice(list(qs)) if qs.exists() else None

class Command(BaseCommand):
    help = 'Carga 40 pistas de ejemplo en la base de datos, asociadas a artistas, géneros y moods aleatorios.'

    def handle(self, *args, **kwargs):
        artists = Artist.objects.all()
        genres = Genre.objects.all()
        moods = Mood.objects.all()
        if not artists.exists() or not genres.exists() or not moods.exists():
            self.stdout.write(self.style.ERROR('Debes tener al menos un artista, género y mood en la base de datos antes de cargar tracks.'))
            return

        for i, title in enumerate(TITLES):
            artist = random_or_none(artists)
            genre = random_or_none(genres)
            mood = random_or_none(moods)
            bpm = random.randint(80, 160)
            duration = round(random.uniform(120, 360), 2)  # entre 2 y 6 minutos
            track, created = Track.objects.get_or_create(
                title=title,
                defaults={
                    'artist': artist,
                    'genre': genre,
                    'mood': mood,
                    'bpm': bpm,
                    'duration': duration,
                    'analysis_status': 'completed',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Track creado: {track.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Track ya existente: {track.title}'))
        self.stdout.write(self.style.SUCCESS('¡40 pistas de ejemplo precargadas correctamente!')) 