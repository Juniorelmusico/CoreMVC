from celery import shared_task
from .models import Track, Analysis, Genre, Mood
import librosa
import numpy as np
import logging
from django.db.models import Avg

logger = logging.getLogger(__name__)

# Inicializar variables para los modelos
genre_model = None
mood_model = None

# Campos a comparar
COMPARISON_FIELDS = [
    'energy', 'danceability', 'valence', 'acousticness', 'instrumentalness', 'liveness', 'speechiness',
    'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff'
]

@shared_task
def analyze_track(track_id):
    try:
        track = Track.objects.get(id=track_id)
        track.analysis_status = 'processing'
        track.save()

        # Load audio file
        y, sr = librosa.load(track.file.path)

        # Extract features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        duration = float(librosa.get_duration(y=y, sr=sr))

        # Update track with basic info
        track.duration = duration
        track.bpm = float(tempo)

        # Predict genre and mood using simplified rules
        analysis_data = {
            'tempo': float(tempo),
            'spectral_centroid_mean': float(np.mean(spectral_centroids)),
            'spectral_centroid_std': float(np.std(spectral_centroids)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            'spectral_rolloff_std': float(np.std(spectral_rolloff)),
            'mfcc_mean': [float(x) for x in np.mean(mfccs, axis=1)],
            'mfcc_std': [float(x) for x in np.std(mfccs, axis=1)],
            'duration': duration
        }
        genre = predict_genre(analysis_data)
        mood = predict_mood(analysis_data)
        track.genre = genre
        track.mood = mood

        # Crear el análisis de la canción subida
        analysis = Analysis.objects.create(
            track=track,
            energy=float(np.mean(librosa.feature.rms(y=y))),
            danceability=float(np.mean(librosa.feature.tempo(y=y, sr=sr))),
            valence=float(np.mean(librosa.feature.spectral_contrast(y=y, sr=sr))),
            acousticness=float(np.mean(librosa.feature.zero_crossing_rate(y))),
            instrumentalness=float(np.mean(mfccs[1:])),
            liveness=float(np.mean(librosa.feature.spectral_flatness(y=y))),
            speechiness=float(np.mean(mfccs[0])),
            spectral_centroid=float(np.mean(spectral_centroids)),
            spectral_bandwidth=float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))),
            spectral_rolloff=float(np.mean(spectral_rolloff))
        )

        track.analysis = analysis
        track.analysis_status = 'completed'
        track.save()

        # --- COMPARACIÓN AUTOMÁTICA ---
        # 1. Comparar con todos los análisis existentes (excepto el actual)
        all_analyses = Analysis.objects.exclude(id=analysis.id)
        min_distance = None
        most_similar = None
        this_vec = np.array([getattr(analysis, f) or 0 for f in COMPARISON_FIELDS])
        for other in all_analyses:
            other_vec = np.array([getattr(other, f) or 0 for f in COMPARISON_FIELDS])
            dist = np.linalg.norm(this_vec - other_vec)
            if min_distance is None or dist < min_distance:
                min_distance = dist
                most_similar = other

        # 2. Calcular promedio de cada campo
        avg_dict = Analysis.objects.exclude(id=analysis.id).aggregate(**{f: Avg(f) for f in COMPARISON_FIELDS})
        avg_comparison = {f: (getattr(analysis, f) or 0) - (avg_dict[f] or 0) for f in COMPARISON_FIELDS}

        # 3. Guardar resultado en comparison_result
        comparison_result = {
            'most_similar_track': most_similar.track.title if most_similar else None,
            'most_similar_artist': most_similar.track.artist.name if most_similar else None,
            'most_similar_id': most_similar.track.id if most_similar else None,
            'distance': min_distance,
            'fields': COMPARISON_FIELDS,
            'values_this': {f: getattr(analysis, f) for f in COMPARISON_FIELDS},
            'values_similar': {f: getattr(most_similar, f) if most_similar else None for f in COMPARISON_FIELDS},
            'diff_with_similar': {f: (getattr(analysis, f) or 0) - (getattr(most_similar, f) or 0) if most_similar else None for f in COMPARISON_FIELDS},
            'avg_all': avg_dict,
            'diff_with_avg': avg_comparison,
            'duration': track.duration,
            'bpm': track.bpm,
            'genre': track.genre.name if track.genre else None,
            'mood': track.mood.name if track.mood else None
        }
        analysis.comparison_result = comparison_result
        analysis.save()

        return True

    except Exception as e:
        track.analysis_status = 'failed'
        track.analysis_error = str(e)
        track.save()
        raise

def predict_genre(analysis_data):
    # Simplified genre prediction based on tempo and spectral features
    tempo = analysis_data['tempo']
    spectral_mean = analysis_data['spectral_centroid_mean']
    
    if tempo > 120 and spectral_mean > 3000:
        return Genre.objects.get_or_create(name='Electronic')[0]
    elif tempo > 100 and spectral_mean > 2000:
        return Genre.objects.get_or_create(name='Rock')[0]
    else:
        return Genre.objects.get_or_create(name='Ambient')[0]

def predict_mood(analysis_data):
    # Simplified mood prediction based on spectral features
    spectral_mean = analysis_data['spectral_centroid_mean']
    spectral_std = analysis_data['spectral_centroid_std']
    
    if spectral_mean > 3000 and spectral_std > 1000:
        return Mood.objects.get_or_create(name='Energetic')[0]
    elif spectral_mean > 2000:
        return Mood.objects.get_or_create(name='Happy')[0]
    else:
        return Mood.objects.get_or_create(name='Calm')[0] 