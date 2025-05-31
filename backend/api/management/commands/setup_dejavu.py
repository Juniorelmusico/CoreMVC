"""
Comando de Django para configurar el sistema de reconocimiento de audio personalizado
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models
from api.models import Track, Artist, Genre, Mood
from api.dejavu_service import audio_recognition_service
from api.tasks import fingerprint_track, predict_genre_from_filename, predict_mood_from_filename
import os


class Command(BaseCommand):
    help = 'Configura el sistema de reconocimiento de audio y migra datos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fingerprint-existing',
            action='store_true',
            help='Generar fingerprints para tracks existentes',
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Crear datos de ejemplo',
        )
        parser.add_argument(
            '--test-service',
            action='store_true',
            help='Probar el servicio de reconocimiento',
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Mostrar estadísticas del sistema',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎵 Configurando sistema de reconocimiento de audio para Melocuore...')
        )

        # Probar servicio de reconocimiento
        if options['test_service']:
            self.test_recognition_service()

        # Crear datos de ejemplo
        if options['create_sample_data']:
            self.create_sample_data()

        # Generar fingerprints para tracks existentes
        if options['fingerprint_existing']:
            self.fingerprint_existing_tracks()
            
        # Mostrar estadísticas
        if options['show_stats']:
            self.show_statistics()

        self.stdout.write(
            self.style.SUCCESS('✅ Configuración completada!')
        )

    def test_recognition_service(self):
        """Probar el servicio de reconocimiento"""
        self.stdout.write('🔍 Probando servicio de reconocimiento...')
        
        try:
            # Probar creación de servicio
            service = audio_recognition_service
            
            self.stdout.write(
                self.style.SUCCESS('✅ Servicio de reconocimiento inicializado correctamente')
            )
            
            # Mostrar configuración
            self.stdout.write('📋 Configuración del servicio:')
            self.stdout.write(f'  - Sample rate: {service.fingerprint.sample_rate} Hz')
            self.stdout.write(f'  - FFT size: {service.fingerprint.n_fft}')
            self.stdout.write(f'  - Hop length: {service.fingerprint.hop_length}')
            self.stdout.write(f'  - MEL bands: {service.fingerprint.n_mels}')
            self.stdout.write(f'  - Cache timeout: {service.cache_timeout} segundos')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando servicio: {str(e)}')
            )

    def create_sample_data(self):
        """Crear datos de ejemplo"""
        self.stdout.write('📝 Creando datos de ejemplo...')
        
        # Crear géneros de ejemplo
        genres_data = [
            {'name': 'Electronic', 'description': 'Música electrónica', 'color_code': '#00ff00'},
            {'name': 'Rock', 'description': 'Música rock', 'color_code': '#ff0000'},
            {'name': 'Pop', 'description': 'Música pop', 'color_code': '#ff69b4'},
            {'name': 'Jazz', 'description': 'Música jazz', 'color_code': '#4169e1'},
            {'name': 'Classical', 'description': 'Música clásica', 'color_code': '#8b4513'},
            {'name': 'Hip Hop', 'description': 'Música hip hop', 'color_code': '#ffa500'},
            {'name': 'Reggae', 'description': 'Música reggae', 'color_code': '#32cd32'},
            {'name': 'Country', 'description': 'Música country', 'color_code': '#daa520'},
            {'name': 'Blues', 'description': 'Música blues', 'color_code': '#4682b4'},
            {'name': 'Alternative', 'description': 'Música alternativa', 'color_code': '#9932cc'},
        ]
        
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults=genre_data
            )
            if created:
                self.stdout.write(f'  ✅ Género creado: {genre.name}')

        # Crear moods de ejemplo
        moods_data = [
            {'name': 'Happy', 'description': 'Alegre y positivo', 'valence_score': 0.8},
            {'name': 'Sad', 'description': 'Triste y melancólico', 'valence_score': -0.6},
            {'name': 'Energetic', 'description': 'Energético y motivador', 'valence_score': 0.9},
            {'name': 'Calm', 'description': 'Calmado y relajante', 'valence_score': 0.2},
            {'name': 'Aggressive', 'description': 'Agresivo e intenso', 'valence_score': -0.2},
            {'name': 'Romantic', 'description': 'Romántico y emotivo', 'valence_score': 0.5},
            {'name': 'Mysterious', 'description': 'Misterioso y enigmático', 'valence_score': -0.1},
            {'name': 'Uplifting', 'description': 'Inspirador y elevador', 'valence_score': 0.7},
            {'name': 'Melancholic', 'description': 'Melancólico y reflexivo', 'valence_score': -0.3},
            {'name': 'Powerful', 'description': 'Poderoso y dominante', 'valence_score': 0.6},
        ]
        
        for mood_data in moods_data:
            mood, created = Mood.objects.get_or_create(
                name=mood_data['name'],
                defaults=mood_data
            )
            if created:
                self.stdout.write(f'  ✅ Mood creado: {mood.name}')

        self.stdout.write(
            self.style.SUCCESS('✅ Datos de ejemplo creados!')
        )

    def fingerprint_existing_tracks(self):
        """Generar fingerprints para tracks existentes"""
        self.stdout.write('🎯 Generando fingerprints para tracks existentes...')
        
        # Obtener tracks sin fingerprint
        tracks_without_fingerprint = Track.objects.filter(
            fingerprint_status__in=['pending', 'error']
        )
        
        if not tracks_without_fingerprint.exists():
            self.stdout.write('ℹ️  No hay tracks pendientes de fingerprinting')
            return

        self.stdout.write(
            f'📊 Encontrados {tracks_without_fingerprint.count()} tracks para procesar'
        )

        processed = 0
        errors = 0

        # Procesar cada track
        for track in tracks_without_fingerprint:
            self.stdout.write(f'🎵 Procesando: {track.title} - {track.artist.name}')
            
            # Verificar que el archivo existe
            if not track.file or not os.path.exists(track.file.path):
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Archivo no encontrado para track {track.id}')
                )
                track.fingerprint_status = 'error'
                track.fingerprint_error = 'Archivo no encontrado'
                track.save()
                errors += 1
                continue

            # Asignar género y mood si no los tiene
            if not track.genre:
                track.genre = predict_genre_from_filename(track.file.name)
                self.stdout.write(f'  📂 Género asignado: {track.genre.name}')

            if not track.mood:
                track.mood = predict_mood_from_filename(track.file.name)
                self.stdout.write(f'  😊 Mood asignado: {track.mood.name}')

            # Marcar como track de referencia si no está marcado
            if not track.is_reference_track:
                track.is_reference_track = True
                track.reference_source = 'admin_migration'

            track.save()

            # Ejecutar fingerprinting directamente (sin Celery en desarrollo)
            try:
                self.stdout.write(f'  🚀 Generando fingerprint para track {track.id}...')
                result = fingerprint_track(track.id)  # Llamada directa
                
                if result.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Fingerprint completado: {result.get("fingerprints_count", 0)} features')
                    )
                    processed += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Error en fingerprint: {result.get("error")}')
                    )
                    errors += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error procesando track: {str(e)}')
                )
                errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Fingerprinting completado: {processed} exitosos, {errors} errores'
            )
        )

    def show_statistics(self):
        """Mostrar estadísticas del sistema"""
        self.stdout.write('📊 Estadísticas del sistema:')
        
        total_tracks = Track.objects.count()
        fingerprinted_tracks = Track.objects.filter(fingerprint_status='completed').count()
        pending_tracks = Track.objects.filter(fingerprint_status='pending').count()
        error_tracks = Track.objects.filter(fingerprint_status='error').count()
        reference_tracks = Track.objects.filter(is_reference_track=True).count()
        
        self.stdout.write(f'  📀 Total tracks: {total_tracks}')
        self.stdout.write(f'  ✅ Fingerprinted: {fingerprinted_tracks}')
        self.stdout.write(f'  ⏳ Pendientes: {pending_tracks}')
        self.stdout.write(f'  ❌ Con errores: {error_tracks}')
        self.stdout.write(f'  🎯 Tracks de referencia: {reference_tracks}')
        
        # Estadísticas de reconocimiento
        from api.models import Recognition
        total_recognitions = Recognition.objects.count()
        successful_recognitions = Recognition.objects.filter(recognition_status='found').count()
        failed_recognitions = Recognition.objects.filter(recognition_status='not_found').count()
        
        self.stdout.write(f'  🔍 Total reconocimientos: {total_recognitions}')
        self.stdout.write(f'  ✅ Exitosos: {successful_recognitions}')
        self.stdout.write(f'  ❌ Fallidos: {failed_recognitions}')
        
        if total_recognitions > 0:
            success_rate = (successful_recognitions / total_recognitions) * 100
            self.stdout.write(f'  📈 Tasa de éxito: {success_rate:.1f}%')

        # Estadísticas de géneros y moods
        genres_count = Genre.objects.count()
        moods_count = Mood.objects.count()
        artists_count = Artist.objects.count()
        
        self.stdout.write(f'  🎭 Géneros: {genres_count}')
        self.stdout.write(f'  😊 Moods: {moods_count}')
        self.stdout.write(f'  👨‍🎤 Artistas: {artists_count}')
        
        # Mostrar distribución de géneros
        self.stdout.write('\n📊 Distribución por géneros:')
        genre_stats = Genre.objects.annotate(
            track_count=models.Count('tracks')
        ).order_by('-track_count')[:5]
        
        for genre in genre_stats:
            self.stdout.write(f'  - {genre.name}: {genre.track_count} tracks')
        
        # Mostrar artistas con más tracks
        self.stdout.write('\n🎤 Top artistas:')
        artist_stats = Artist.objects.annotate(
            track_count=models.Count('tracks')
        ).order_by('-track_count')[:5]
        
        for artist in artist_stats:
            self.stdout.write(f'  - {artist.name}: {artist.track_count} tracks') 