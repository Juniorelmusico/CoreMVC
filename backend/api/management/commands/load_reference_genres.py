from django.core.management.base import BaseCommand
from api.models import Genre

GENRES = [
    {"name": "Electronic", "description": "Música electrónica, EDM, techno, house, trance, etc."},
    {"name": "Rock", "description": "Rock clásico, alternativo, hard rock, punk, etc."},
    {"name": "Pop", "description": "Pop internacional y latino, éxitos comerciales."},
    {"name": "Hip-Hop", "description": "Rap, trap, hip-hop clásico y moderno."},
    {"name": "Jazz", "description": "Jazz tradicional, smooth jazz, jazz fusión."},
    {"name": "Ambient", "description": "Música ambiental, chillout, downtempo."},
    {"name": "Reggaeton", "description": "Reggaeton, urbano latino, dembow."},
    {"name": "Classical", "description": "Música clásica, orquestal, sinfónica."},
    {"name": "Funk", "description": "Funk, soul, groove."},
    {"name": "Metal", "description": "Metal, heavy metal, death metal, power metal."},
]

class Command(BaseCommand):
    help = 'Carga géneros musicales de ejemplo en la base de datos.'

    def handle(self, *args, **kwargs):
        for genre in GENRES:
            obj, created = Genre.objects.get_or_create(name=genre["name"], defaults={"description": genre["description"]})
            if created:
                self.stdout.write(self.style.SUCCESS(f'Género creado: {obj.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Género ya existente: {obj.name}'))
        self.stdout.write(self.style.SUCCESS('¡Géneros precargados correctamente!')) 