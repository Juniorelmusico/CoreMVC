from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Track, Artist, Analysis, User
import numpy as np

class Command(BaseCommand):
    help = 'Crea tracks de referencia de prueba con fingerprints simulados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Número de tracks a crear',
        )
    
    def create_test_track(self, title, artist_name, user):
        """Crear un track de prueba con fingerprint simulado"""
        
        # Crear o obtener artista
        artist, _ = Artist.objects.get_or_create(
            name=artist_name,
            user=user
        )
        
        # Verificar si el track ya existe
        if Track.objects.filter(title=title, artist=artist).exists():
            self.stdout.write(f"Track '{title}' ya existe, saltando...")
            return None
        
        # Crear track
        track = Track.objects.create(
            title=title,
            artist=artist,
            fingerprint_status='completed',
            is_reference_track=True,
            reference_source='test_data',
            fingerprints_count=100,
            duration=180.0  # 3 minutos
        )
        
        # Crear análisis con fingerprint simulado pero realista
        analysis = Analysis.objects.create(
            track=track,
            duration_ms=180000,
            frame_rate=22050,
            channels_count=2
        )
        
        # Generar fingerprint simulado con variaciones realistas
        base_tempo = np.random.uniform(80, 140)  # BPM realista
        base_centroid = np.random.uniform(1000, 4000)  # Hz realista
        
        # MFCC simulado (13 coeficientes)
        mfcc_mean = np.random.normal(0, 1, 13).tolist()
        mfcc_std = np.random.uniform(0.1, 2.0, 13).tolist()
        
        # Chroma simulado (12 dimensiones)
        chroma_mean = np.random.uniform(0, 1, 12).tolist()
        
        # Spectral contrast simulado (7 dimensiones)
        contrast_mean = np.random.uniform(0, 1, 7).tolist()
        
        fingerprint_features = {
            'tempo': float(base_tempo),
            'duration': 180.0,
            'spectral_centroid_mean': float(base_centroid),
            'spectral_centroid_std': float(np.random.uniform(100, 500)),
            'spectral_rolloff_mean': float(base_centroid * 1.5),
            'spectral_rolloff_std': float(np.random.uniform(200, 800)),
            'zero_crossing_rate_mean': float(np.random.uniform(0.01, 0.15)),
            'zero_crossing_rate_std': float(np.random.uniform(0.005, 0.05)),
            'mfcc_mean': mfcc_mean,
            'mfcc_std': mfcc_std,
            'chroma_mean': chroma_mean,
            'contrast_mean': contrast_mean
        }
        
        analysis.fingerprint_result = {
            'fingerprint_hash': f'test_hash_{track.id}',
            'features': fingerprint_features
        }
        analysis.save()
        
        self.stdout.write(self.style.SUCCESS(f"✅ Creado: {title} - {artist_name} (ID: {track.id})"))
        return track
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎵 Creando tracks de referencia de prueba...'))
        
        # Obtener usuario admin
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('❌ No se encontró usuario administrador'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error obteniendo usuario admin: {str(e)}'))
            return
        
        # Lista de tracks de prueba con diferentes características
        test_tracks = [
            ("Blinding Lights", "The Weeknd"),
            ("Shape of You", "Ed Sheeran"),
            ("Despacito", "Luis Fonsi"),
            ("Bohemian Rhapsody", "Queen"),
            ("Hotel California", "Eagles"),
            ("Imagine", "John Lennon"),
            ("Billie Jean", "Michael Jackson"),
            ("Sweet Child O' Mine", "Guns N' Roses"),
            ("Smells Like Teen Spirit", "Nirvana"),
            ("Wonderwall", "Oasis"),
            ("Go Loko", "YG"),
            ("Bad Guy", "Billie Eilish"),
            ("Sunflower", "Post Malone"),
            ("Old Town Road", "Lil Nas X"),
            ("Someone You Loved", "Lewis Capaldi")
        ]
        
        created_count = 0
        with transaction.atomic():
            for title, artist in test_tracks[:options['count']]:
                track = self.create_test_track(title, artist, admin_user)
                if track:
                    created_count += 1
        
        self.stdout.write(f'\n📊 Resumen:')
        self.stdout.write(f'   ✅ Tracks creados: {created_count}')
        self.stdout.write(f'   📈 Total tracks: {Track.objects.count()}')
        self.stdout.write(f'   🎯 Tracks de referencia: {Track.objects.filter(is_reference_track=True).count()}')
        self.stdout.write(f'   ✅ Tracks completados: {Track.objects.filter(fingerprint_status="completed").count()}')
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS('🎉 ¡Tracks de prueba creados exitosamente!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  No se crearon nuevos tracks')) 