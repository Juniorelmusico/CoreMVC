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
        Compara dos fingerprints y retorna un score de similitud mejorado
        
        Args:
            features1 (Dict): Características del primer audio
            features2 (Dict): Características del segundo audio
            
        Returns:
            float: Score de similitud (0-1, donde 1 es idéntico)
        """
        try:
            # Validar que ambos conjuntos de características existan
            required_keys = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
            for key in required_keys:
                if key not in features1 or key not in features2:
                    logger.warning(f"Clave faltante en fingerprints: {key}")
                    return 0.0
            
            # Extraer características principales y validar
            mfcc1 = np.array(features1['mfcc_mean'])
            mfcc2 = np.array(features2['mfcc_mean'])
            
            chroma1 = np.array(features1['chroma_mean'])
            chroma2 = np.array(features2['chroma_mean'])
            
            contrast1 = np.array(features1['contrast_mean'])
            contrast2 = np.array(features2['contrast_mean'])
            
            # Validar que los arrays tengan el mismo tamaño
            if mfcc1.shape != mfcc2.shape:
                logger.warning(f"MFCC shapes no coinciden: {mfcc1.shape} vs {mfcc2.shape}")
                return 0.0
            
            if chroma1.shape != chroma2.shape:
                logger.warning(f"Chroma shapes no coinciden: {chroma1.shape} vs {chroma2.shape}")
                return 0.0
                
            if contrast1.shape != contrast2.shape:
                logger.warning(f"Contrast shapes no coinciden: {contrast1.shape} vs {contrast2.shape}")
                return 0.0
            
            # Función auxiliar para similitud coseno robusta
            def cosine_similarity(a, b):
                if np.allclose(a, 0) or np.allclose(b, 0):
                    return 0.0
                norm_a = np.linalg.norm(a)
                norm_b = np.linalg.norm(b)
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                return np.dot(a, b) / (norm_a * norm_b)
            
            # Calcular similitudes usando similitud coseno (más robusta)
            mfcc_similarity = cosine_similarity(mfcc1, mfcc2)
            chroma_similarity = cosine_similarity(chroma1, chroma2)
            contrast_similarity = cosine_similarity(contrast1, contrast2)
            
            # Similitud de tempo (más estricta)
            tempo_diff = abs(features1['tempo'] - features2['tempo'])
            # Considerar tempos similares dentro de un 10% de diferencia
            tempo_threshold = max(features1['tempo'], features2['tempo']) * 0.1
            tempo_similarity = max(0.0, 1.0 - (tempo_diff / max(tempo_threshold, 10.0)))
            
            # Similitud espectral (más estricta)
            spectral_diff = abs(features1['spectral_centroid_mean'] - features2['spectral_centroid_mean'])
            # Normalizar por el valor más alto
            spectral_max = max(features1['spectral_centroid_mean'], features2['spectral_centroid_mean'])
            spectral_similarity = max(0.0, 1.0 - (spectral_diff / max(spectral_max, 1000.0)))
            
            # Calcular similitud total con pesos más balanceados
            # MFCC sigue siendo el más importante, pero reducimos su peso
            total_similarity = (
                mfcc_similarity * 0.35 +      # MFCC reducido
                chroma_similarity * 0.25 +    # Chroma aumentado
                contrast_similarity * 0.20 +  # Contrast igual
                tempo_similarity * 0.10 +     # Tempo igual
                spectral_similarity * 0.10    # Spectral igual
            )
            
            # Log de debugging para análisis
            logger.info(f"🔍 Comparación de fingerprints:")
            logger.info(f"   MFCC similarity: {mfcc_similarity:.4f}")
            logger.info(f"   Chroma similarity: {chroma_similarity:.4f}")
            logger.info(f"   Contrast similarity: {contrast_similarity:.4f}")
            logger.info(f"   Tempo similarity: {tempo_similarity:.4f} (diff: {tempo_diff:.2f})")
            logger.info(f"   Spectral similarity: {spectral_similarity:.4f} (diff: {spectral_diff:.2f})")
            logger.info(f"   🎯 Total similarity: {total_similarity:.4f}")
            
            # Asegurar que el resultado esté entre 0 y 1
            final_similarity = max(0.0, min(1.0, total_similarity))
            
            return final_similarity
            
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
            logger.info(f"🎵 Iniciando reconocimiento de audio: {audio_path}")
            logger.info(f"📊 Tracks de referencia disponibles: {len(reference_tracks)}")
            
            # Extraer características del audio a reconocer
            query_result = self.fingerprint.extract_features(audio_path)
            
            if not query_result['success']:
                logger.error(f"❌ Error extrayendo características del query: {query_result.get('error')}")
                return query_result
            
            query_features = query_result['features']
            logger.info(f"✅ Características extraídas del query:")
            logger.info(f"   Tempo: {query_features.get('tempo', 'N/A'):.2f} BPM")
            logger.info(f"   Centroide espectral: {query_features.get('spectral_centroid_mean', 'N/A'):.2f} Hz")
            logger.info(f"   Duración: {query_features.get('duration', 'N/A'):.2f} s")
            
            best_match = None
            best_similarity = 0.0
            all_similarities = []
            
            # Comparar con todos los tracks de referencia
            for i, track in enumerate(reference_tracks):
                if 'fingerprint_features' not in track:
                    logger.warning(f"⚠️  Track {track.get('id', 'N/A')} - {track.get('title', 'N/A')} no tiene fingerprint_features")
                    continue
                
                logger.info(f"\n🔍 Comparando con track {i+1}/{len(reference_tracks)}: {track.get('title', 'N/A')} - {track.get('artist', 'N/A')}")
                
                # Log de características del track de referencia
                ref_features = track['fingerprint_features']
                logger.info(f"   Ref Tempo: {ref_features.get('tempo', 'N/A'):.2f} BPM")
                logger.info(f"   Ref Centroide: {ref_features.get('spectral_centroid_mean', 'N/A'):.2f} Hz")
                logger.info(f"   Ref Duración: {ref_features.get('duration', 'N/A'):.2f} s")
                
                similarity = self.fingerprint.compare_fingerprints(
                    query_features, 
                    track['fingerprint_features']
                )
                
                all_similarities.append({
                    'track_id': track['id'],
                    'title': track['title'],
                    'artist': track['artist'],
                    'similarity': similarity
                })
                
                logger.info(f"   📈 Similitud calculada: {similarity:.4f}")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = track
                    logger.info(f"   🎯 ¡Nueva mejor coincidencia! Similitud: {similarity:.4f}")
            
            # Ordenar por similitud para mostrar el ranking
            all_similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"\n📊 Ranking de similitudes:")
            for i, sim in enumerate(all_similarities[:5]):  # Top 5
                logger.info(f"   {i+1}. {sim['title']} - {sim['artist']}: {sim['similarity']:.4f}")
            
            # Umbral mínimo de similitud más estricto
            similarity_threshold = 0.85  # Aumentado de 0.75 a 0.85 para mayor precisión
            
            logger.info(f"\n🎯 Mejor similitud: {best_similarity:.4f}")
            logger.info(f"🎯 Umbral requerido: {similarity_threshold:.4f}")
            
            if best_match and best_similarity >= similarity_threshold:
                logger.info(f"✅ ¡RECONOCIMIENTO EXITOSO! Track: {best_match['title']} - {best_match['artist']}")
                return {
                    'success': True,
                    'recognized': True,
                    'track_id': best_match['id'],
                    'song_name': best_match['title'],
                    'artist': best_match['artist'],
                    'similarity': best_similarity,
                    'confidence': best_similarity,
                    'query_features': query_features,
                    'all_similarities': all_similarities[:10]  # Top 10 para análisis
                }
            else:
                logger.info(f"❌ No se encontró coincidencia suficiente. Mejor similitud: {best_similarity:.4f} < {similarity_threshold:.4f}")
                return {
                    'success': True,
                    'recognized': False,
                    'message': 'No se encontró coincidencia',
                    'best_similarity': best_similarity,
                    'threshold': similarity_threshold,
                    'query_features': query_features,
                    'all_similarities': all_similarities[:10],  # Top 10 para análisis
                    'best_match_info': {
                        'title': best_match['title'] if best_match else None,
                        'artist': best_match['artist'] if best_match else None,
                        'similarity': best_similarity
                    } if best_match else None
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