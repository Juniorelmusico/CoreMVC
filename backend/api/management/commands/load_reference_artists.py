from django.core.management.base import BaseCommand
from api.models import Artist
from django.contrib.auth.models import User

ARTISTS = [
    "Daft Punk", "The Beatles", "Queen", "Beyoncé", "Eminem", "Miles Davis", "Armin van Buuren", "Shakira", "Metallica", "Adele",
    "David Guetta", "Coldplay", "Drake", "Hans Zimmer", "Nirvana", "Bad Bunny", "Pink Floyd", "Lady Gaga", "The Weeknd", "Bruno Mars"
]

class Command(BaseCommand):
    help = 'Carga artistas de ejemplo en la base de datos.'

    def handle(self, *args, **kwargs):
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('Debes tener al menos un usuario en la base de datos para asignar como propietario de los artistas.'))
            return
        for name in ARTISTS:
            obj, created = Artist.objects.get_or_create(name=name, user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Artista creado: {obj.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Artista ya existente: {obj.name}'))
        self.stdout.write(self.style.SUCCESS('¡Artistas precargados correctamente!')) 