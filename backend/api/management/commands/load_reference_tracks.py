from django.core.management.base import BaseCommand
from api.models import Track, Artist, Genre, Mood
from django.contrib.auth.models import User
from api.tasks import analyze_track
from django.conf import settings
import os

REFERENCE_DIR = os.path.join(settings.BASE_DIR, 'reference_tracks')

class Command(BaseCommand):
    help = 'Carga canciones de referencia y las analiza automáticamente.'

    def handle(self, *args, **kwargs):
        if not os.path.exists(REFERENCE_DIR):
            self.stdout.write(self.style.ERROR(f'No existe la carpeta {REFERENCE_DIR}. Crea la carpeta y pon ahí tus archivos .mp3 o .wav de referencia.'))
            return

        user, _ = User.objects.get_or_create(username='referencia', defaults={'password': 'referencia123'})
        artist, _ = Artist.objects.get_or_create(name='Referencia', user=user)
        files = [f for f in os.listdir(REFERENCE_DIR) if f.lower().endswith(('.mp3', '.wav'))]
        if not files:
            self.stdout.write(self.style.WARNING('No se encontraron archivos .mp3 o .wav en la carpeta de referencia.'))
            return

        for filename in files:
            file_path = os.path.join(REFERENCE_DIR, filename)
            title = os.path.splitext(filename)[0]
            # Crea un nuevo Track para cada archivo
            with open(file_path, 'rb') as f:
                django_file = f
                track = Track.objects.create(
                    title=title,
                    file=django_file,
                    artist=artist,
                    analysis_status='pending'
                )
                self.stdout.write(self.style.SUCCESS(f'Track creado: {title}'))
                analyze_track.delay(track.id)
        self.stdout.write(self.style.SUCCESS('¡Canciones de referencia cargadas y en análisis!')) 