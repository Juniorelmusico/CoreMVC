#!/usr/bin/env python
import os
import django
import sys

# Add backend to Python path
sys.path.append('/c%3A/Users/junio/OneDrive/Documents/Django-React-Full-Stack-App/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melocuore.settings')
django.setup()

try:
    from api.models import Track, Analysis
    
    print('=== TRACKS CON FINGERPRINTS VÁLIDOS ===')
    completed = Track.objects.filter(fingerprint_status='completed', is_reference_track=True)
    print(f'Tracks completados: {completed.count()}')
    
    valid_count = 0
    for t in completed:
        has_analysis = hasattr(t, 'analysis') and t.analysis and t.analysis.fingerprint_result
        print(f'ID {t.id}: {t.title} - {t.artist.name} | Análisis: {has_analysis}')
        
        if has_analysis:
            features = t.analysis.fingerprint_result.get('features', {})
            required = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
            missing = [k for k in required if k not in features]
            if not missing:
                valid_count += 1
                print(f'  ✅ VÁLIDO | Tempo: {features.get("tempo", "N/A"):.2f} BPM')
            else:
                print(f'  ❌ INVÁLIDO | Faltan claves: {missing}')
        else:
            print(f'  ❌ SIN ANÁLISIS')
    
    print(f'\n📊 RESUMEN:')
    print(f'   Total tracks: {Track.objects.count()}')
    print(f'   Tracks completados: {completed.count()}') 
    print(f'   Tracks válidos para reconocimiento: {valid_count}')
    
    if valid_count <= 1:
        print(f'\n⚠️  PROBLEMA IDENTIFICADO: Solo hay {valid_count} track(s) válido(s)!')
        print('   Esto explica por qué siempre devuelve la misma canción.')
        
except Exception as e:
    print(f'Error: {e}') 