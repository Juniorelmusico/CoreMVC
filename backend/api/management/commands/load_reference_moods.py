from django.core.management.base import BaseCommand
from api.models import Mood

MOODS = [
    {"name": "Happy", "description": "Canciones alegres, positivas, energéticas."},
    {"name": "Sad", "description": "Canciones tristes, melancólicas, nostálgicas."},
    {"name": "Energetic", "description": "Canciones con mucha energía, motivadoras."},
    {"name": "Calm", "description": "Canciones relajantes, tranquilas, chill."},
    {"name": "Romantic", "description": "Canciones románticas, amorosas."},
    {"name": "Dark", "description": "Canciones oscuras, misteriosas, intensas."},
    {"name": "Party", "description": "Canciones para fiesta, bailar, celebrar."},
    {"name": "Epic", "description": "Canciones épicas, grandiosas, cinematográficas."},
    {"name": "Groovy", "description": "Canciones con groove, funky, bailables."},
    {"name": "Aggressive", "description": "Canciones agresivas, potentes, intensas."},
]

class Command(BaseCommand):
    help = 'Carga moods (estados de ánimo) musicales de ejemplo en la base de datos.'

    def handle(self, *args, **kwargs):
        for mood in MOODS:
            obj, created = Mood.objects.get_or_create(name=mood["name"], defaults={"description": mood["description"]})
            if created:
                self.stdout.write(self.style.SUCCESS(f'Mood creado: {obj.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Mood ya existente: {obj.name}'))
        self.stdout.write(self.style.SUCCESS('¡Moods precargados correctamente!')) 