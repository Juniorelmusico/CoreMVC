"""
Servicio de fingerprinting de audio personalizado usando Librosa
Una alternativa más simple a Dejavu que es fácil de instalar y usar
"""
import os
import numpy as np
import librosa
import hashlib
import json
import logging
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SimpleFingerprint:
    """
    Sistema de fingerprinting de audio simplificado tipo Shazam
    """
    
    def __init__(self):
        self.sample_rate = 22050
        self.n_fft = 2048
        self.hop_length = 512
        self.n_mels = 128
        
    def extract_features(self, audio_path: str) -> Dict:
        """
        Extrae características de audio para fingerprinting
        
        Args:
            audio_path (str): Ruta al archivo de audio
            
        Returns:
            Dict: Características extraídas
        """
        try:
            # Cargar audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Características espectrales
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # MFCC (características más importantes para identificación)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Chroma features (características tonales)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Spectral contrast
            contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            
            # Tempo y beats
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Crear fingerprint hash único
            features_array = np.concatenate([
                np.mean(mfccs, axis=1),
                np.std(mfccs, axis=1),
                [np.mean(spectral_centroids), np.std(spectral_centroids)],
                [np.mean(spectral_rolloff), np.std(spectral_rolloff)],
                [np.mean(zero_crossing_rate), np.std(zero_crossing_rate)],
                np.mean(chroma, axis=1),
                np.mean(contrast, axis=1),
                [tempo]
            ])
            
            # Generar hash único para este fingerprint
            fingerprint_hash = hashlib.md5(features_array.tobytes()).hexdigest()
            
            return {
                'fingerprint_hash': fingerprint_hash,
                'features': {
                    'mfcc_mean': np.mean(mfccs, axis=1).tolist(),
                    'mfcc_std': np.std(mfccs, axis=1).tolist(),
                    'spectral_centroid_mean': float(np.mean(spectral_centroids)),
                    'spectral_centroid_std': float(np.std(spectral_centroids)),
                    'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
                    'spectral_rolloff_std': float(np.std(spectral_rolloff)),
                    'zero_crossing_rate_mean': float(np.mean(zero_crossing_rate)),
                    'zero_crossing_rate_std': float(np.std(zero_crossing_rate)),
                    'chroma_mean': np.mean(chroma, axis=1).tolist(),
                    'contrast_mean': np.mean(contrast, axis=1).tolist(),
                    'tempo': float(tempo),
                    'duration': float(len(y) / sr)
                },
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo características de {audio_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_fingerprints(self, features1: Dict, features2: Dict) -> float:
        """
        Compara dos fingerprints y retorna un score de similitud
        
        Args:
            features1 (Dict): Características del primer audio
            features2 (Dict): Características del segundo audio
            
        Returns:
            float: Score de similitud (0-1, donde 1 es idéntico)
        """
        try:
            # Extraer arrays de características principales
            mfcc1 = np.array(features1['mfcc_mean'])
            mfcc2 = np.array(features2['mfcc_mean'])
            
            chroma1 = np.array(features1['chroma_mean'])
            chroma2 = np.array(features2['chroma_mean'])
            
            contrast1 = np.array(features1['contrast_mean'])
            contrast2 = np.array(features2['contrast_mean'])
            
            # Calcular similitudes individuales
            mfcc_similarity = 1 - (np.linalg.norm(mfcc1 - mfcc2) / (np.linalg.norm(mfcc1) + np.linalg.norm(mfcc2)))
            chroma_similarity = 1 - (np.linalg.norm(chroma1 - chroma2) / (np.linalg.norm(chroma1) + np.linalg.norm(chroma2)))
            contrast_similarity = 1 - (np.linalg.norm(contrast1 - contrast2) / (np.linalg.norm(contrast1) + np.linalg.norm(contrast2)))
            
            # Similitud de tempo
            tempo_diff = abs(features1['tempo'] - features2['tempo'])
            tempo_similarity = 1 - min(tempo_diff / 200.0, 1.0)  # Normalizar por 200 BPM
            
            # Similitud espectral
            spectral_diff = abs(features1['spectral_centroid_mean'] - features2['spectral_centroid_mean'])
            spectral_similarity = 1 - min(spectral_diff / 5000.0, 1.0)  # Normalizar por 5000 Hz
            
            # Peso promedio de las similitudes
            total_similarity = (
                mfcc_similarity * 0.4 +      # MFCC es más importante
                chroma_similarity * 0.2 +
                contrast_similarity * 0.2 +
                tempo_similarity * 0.1 +
                spectral_similarity * 0.1
            )
            
            return max(0.0, min(1.0, total_similarity))  # Clamp entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error comparando fingerprints: {str(e)}")
            return 0.0


class AudioRecognitionService:
    """
    Servicio principal para reconocimiento de audio tipo Shazam
    """
    
    def __init__(self):
        self.fingerprint = SimpleFingerprint()
        self.cache_timeout = 3600  # 1 hora
        
    def create_fingerprint(self, audio_path: str, song_id: str) -> Dict:
        """
        Crea fingerprint para una canción de referencia
        
        Args:
            audio_path (str): Ruta al archivo de audio
            song_id (str): ID único de la canción
            
        Returns:
            Dict: Resultado del fingerprinting
        """
        try:
            # Extraer características
            result = self.fingerprint.extract_features(audio_path)
            
            if result['success']:
                # Guardar en cache para búsquedas rápidas
                cache_key = f"fingerprint_{song_id}"
                cache.set(cache_key, result['features'], timeout=self.cache_timeout)
                
                logger.info(f"Fingerprint creado para song_id: {song_id}")
                
                return {
                    'success': True,
                    'song_id': song_id,
                    'fingerprint_hash': result['fingerprint_hash'],
                    'features': result['features']
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creando fingerprint para {song_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def recognize_audio(self, audio_path: str, reference_tracks: List[Dict]) -> Dict:
        """
        Reconoce un audio comparándolo con tracks de referencia
        
        Args:
            audio_path (str): Ruta al archivo a reconocer
            reference_tracks (List[Dict]): Lista de tracks de referencia con sus fingerprints
            
        Returns:
            Dict: Resultado del reconocimiento
        """
        try:
            # Extraer características del audio a reconocer
            query_result = self.fingerprint.extract_features(audio_path)
            
            if not query_result['success']:
                return query_result
            
            query_features = query_result['features']
            best_match = None
            best_similarity = 0.0
            
            # Comparar con todos los tracks de referencia
            for track in reference_tracks:
                if 'fingerprint_features' not in track:
                    continue
                    
                similarity = self.fingerprint.compare_fingerprints(
                    query_features, 
                    track['fingerprint_features']
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = track
            
            # Umbral mínimo de similitud para considerar una coincidencia
            similarity_threshold = 0.7
            
            if best_match and best_similarity >= similarity_threshold:
                return {
                    'success': True,
                    'recognized': True,
                    'track_id': best_match['id'],
                    'song_name': best_match['title'],
                    'artist': best_match['artist'],
                    'similarity': best_similarity,
                    'confidence': best_similarity,
                    'query_features': query_features
                }
            else:
                return {
                    'success': True,
                    'recognized': False,
                    'message': 'No se encontró coincidencia',
                    'best_similarity': best_similarity,
                    'threshold': similarity_threshold,
                    'query_features': query_features
                }
                
        except Exception as e:
            logger.error(f"Error reconociendo audio {audio_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_cached_fingerprint(self, song_id: str) -> Optional[Dict]:
        """
        Obtiene fingerprint desde cache
        
        Args:
            song_id (str): ID de la canción
            
        Returns:
            Optional[Dict]: Fingerprint si existe en cache
        """
        cache_key = f"fingerprint_{song_id}"
        return cache.get(cache_key)
    
    def clear_cache(self):
        """
        Limpia cache de fingerprints
        """
        # Esta es una implementación simple, en producción podrías usar un patrón más específico
        cache.clear()


# Instancia global del servicio
audio_recognition_service = AudioRecognitionService() 