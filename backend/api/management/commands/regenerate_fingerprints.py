from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Track, Analysis
from api.tasks import fingerprint_track
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Regenera fingerprints para todos los tracks de referencia'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar regeneración incluso para tracks con fingerprints completados',
        )
        parser.add_argument(
            '--track-id',
            type=int,
            help='Regenerar fingerprint solo para un track específico',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎵 Iniciando regeneración de fingerprints...'))
        
        # Filtrar tracks
        if options['track_id']:
            tracks = Track.objects.filter(id=options['track_id'])
            if not tracks.exists():
                self.stdout.write(self.style.ERROR(f'❌ Track con ID {options["track_id"]} no encontrado'))
                return
        else:
            tracks = Track.objects.filter(is_reference_track=True)
            
            if not options['force']:
                tracks = tracks.exclude(fingerprint_status='completed')
        
        total_tracks = tracks.count()
        self.stdout.write(f'📊 Tracks a procesar: {total_tracks}')
        
        if total_tracks == 0:
            self.stdout.write(self.style.WARNING('⚠️  No hay tracks para procesar'))
            return
        
        success_count = 0
        error_count = 0
        
        for i, track in enumerate(tracks, 1):
            self.stdout.write(f'\n🔄 [{i}/{total_tracks}] Procesando: {track.title} - {track.artist.name}')
            
            try:
                # Resetear estado del track
                track.fingerprint_status = 'pending'
                track.fingerprint_error = None
                track.fingerprints_count = 0
                track.save()
                
                # Ejecutar fingerprinting
                result = fingerprint_track(track.id)
                
                if result and result.get('success'):
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Éxito: {result.get("fingerprints_count", 0)} fingerprints generados'))
                else:
                    error_count += 1
                    error_msg = result.get('error', 'Error desconocido') if result else 'Sin resultado'
                    self.stdout.write(self.style.ERROR(f'   ❌ Error: {error_msg}'))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'   ❌ Excepción: {str(e)}'))
        
        # Resumen final
        self.stdout.write(f'\n📊 Resumen de regeneración:')
        self.stdout.write(f'   ✅ Exitosos: {success_count}')
        self.stdout.write(f'   ❌ Errores: {error_count}')
        self.stdout.write(f'   📈 Total procesados: {success_count + error_count}')
        
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS('🎉 ¡Regeneración completada!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Ningún fingerprint regenerado exitosamente')) 