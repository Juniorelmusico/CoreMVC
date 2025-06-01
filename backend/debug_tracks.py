#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melocuore.settings')
django.setup()

from api.models import Track, Analysis

print('=== ESTADO DE TRACKS ===')
all_tracks = Track.objects.all()
print(f'Total tracks: {all_tracks.count()}')
print(f'Tracks de referencia: {Track.objects.filter(is_reference_track=True).count()}')
print(f'Tracks completados: {Track.objects.filter(fingerprint_status="completed").count()}')
print()

print('=== TRACKS EN DETALLE ===')
for track in all_tracks:
    print(f'ID: {track.id}, Título: {track.title}, Artista: {track.artist.name}')
    print(f'  Status: {track.fingerprint_status}, Es referencia: {track.is_reference_track}')
    if hasattr(track, 'analysis') and track.analysis and track.analysis.fingerprint_result:
        features = track.analysis.fingerprint_result.get('features', {})
        print(f'  Tiene análisis: Sí')
        print(f'  Tempo: {features.get("tempo", "N/A")}')
        print(f'  Duración: {features.get("duration", "N/A")}')
        print(f'  MFCC length: {len(features.get("mfcc_mean", []))}')
        print(f'  Chroma length: {len(features.get("chroma_mean", []))}')
        print(f'  Contrast length: {len(features.get("contrast_mean", []))}')
    else:
        print(f'  Tiene análisis: No')
        if hasattr(track, 'analysis'):
            if track.analysis:
                print(f'  Analysis existe pero sin fingerprint_result')
            else:
                print(f'  Analysis es None')
        else:
            print(f'  No hay relación analysis')
    print()

print('=== VALIDACIÓN DE FINGERPRINTS ===')
completed_tracks = Track.objects.filter(
    fingerprint_status='completed',
    is_reference_track=True
).select_related('artist', 'analysis')

valid_reference_tracks = 0
for track in completed_tracks:
    if hasattr(track, 'analysis') and track.analysis.fingerprint_result:
        features = track.analysis.fingerprint_result.get('features', {})
        
        # Verificar características principales
        required_keys = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
        missing_keys = [key for key in required_keys if key not in features]
        
        if len(missing_keys) == 0:
            valid_reference_tracks += 1
            print(f'✅ Track válido: {track.title} - {track.artist.name}')
        else:
            print(f'❌ Track inválido: {track.title} - faltan: {missing_keys}')

print(f'\nTracks de referencia válidos: {valid_reference_tracks}') 