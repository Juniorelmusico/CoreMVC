"""
Tareas de Celery para fingerprinting y reconocimiento de audio usando nuestro servicio personalizado
"""
from celery import shared_task
from .models import Track, Analysis, Genre, Mood, UploadedFile, Recognition
from .dejavu_service import audio_recognition_service
import os
import time
import logging
from pydub import AudioSegment
from pydub.utils import mediainfo
from django.db import transaction
import json

logger = logging.getLogger(__name__)

@shared_task
def fingerprint_track(track_id):
    """
    Genera fingerprint de un track usando nuestro servicio personalizado
    
    Args:
        track_id (int): ID del track a procesar
    
    Returns:
        dict: Resultado del procesamiento
    """
    try:
        track = Track.objects.get(id=track_id)
        track.fingerprint_status = 'processing'
        track.save()

        # Generar song_id único
        if not track.dejavu_song_id:
            track.dejavu_song_id = f"track_{track.id}_{track.title.replace(' ', '_').replace('/', '_')}"
            track.save()

        # Realizar fingerprinting con nuestro servicio
        result = audio_recognition_service.create_fingerprint(
            track.file.path, 
            track.dejavu_song_id
        )

        if result['success']:
            # Actualizar track con resultado exitoso
            track.fingerprint_status = 'completed'
            track.fingerprint_error = None
            
            # Guardar características en el análisis
            analysis, created = Analysis.objects.get_or_create(track=track)
            analysis.fingerprint_result = {
                'fingerprint_hash': result['fingerprint_hash'],
                'features': result['features']
            }
            
            # Realizar análisis básico con pydub
            basic_analysis = analyze_audio_file(track.file.path)
            if basic_analysis:
                # Actualizar campos del track
                track.duration = basic_analysis.get('duration_seconds')
                track.sample_rate = basic_analysis.get('sample_rate')
                track.channels = basic_analysis.get('channels')
                track.bitrate = basic_analysis.get('bitrate')
                
                # Actualizar análisis con datos de pydub
                analysis.duration_ms = basic_analysis.get('duration_ms')
                analysis.frame_rate = basic_analysis.get('sample_rate')
                analysis.channels_count = basic_analysis.get('channels')
                analysis.frame_width = basic_analysis.get('frame_width')
                analysis.max_amplitude = basic_analysis.get('max_amplitude')
                analysis.rms_amplitude = basic_analysis.get('rms_amplitude')
                analysis.file_format = basic_analysis.get('format')
                analysis.file_size_bytes = basic_analysis.get('file_size')
                analysis.clipping_detected = basic_analysis.get('clipping_detected', False)
                analysis.silence_percentage = basic_analysis.get('silence_percentage', 0)
            
            analysis.save()
            track.save()
            
            # Contar fingerprints (simulado)
            fingerprints_count = len(result['features']['mfcc_mean']) * 10  # Estimación
            track.fingerprints_count = fingerprints_count
            track.save()
            
            logger.info(f"Fingerprint completado para track {track_id}")
            
            return {
                'success': True,
                'track_id': track_id,
                'fingerprints_count': fingerprints_count,
                'song_id': track.dejavu_song_id
            }
        else:
            # Error en fingerprinting
            track.fingerprint_status = 'error'
            track.fingerprint_error = result.get('error', 'Error desconocido')
            track.save()
            
            logger.error(f"Error en fingerprint para track {track_id}: {result.get('error')}")
            
            return {
                'success': False,
                'track_id': track_id,
                'error': result.get('error')
            }

    except Track.DoesNotExist:
        logger.error(f"Track {track_id} no encontrado")
        return {'success': False, 'error': 'Track no encontrado'}
    except Exception as e:
        logger.error(f"Error procesando track {track_id}: {str(e)}")
        # Actualizar estado de error en la base de datos
        try:
            track = Track.objects.get(id=track_id)
            track.fingerprint_status = 'error'
            track.fingerprint_error = str(e)
            track.save()
        except:
            pass
        return {'success': False, 'error': str(e)}


@shared_task
def recognize_audio_file(uploaded_file_id):
    """
    Reconoce un archivo de audio subido usando nuestro servicio personalizado
    
    Args:
        uploaded_file_id (int): ID del archivo subido
    
    Returns:
        dict: Resultado del reconocimiento
    """
    start_time = time.time()
    
    try:
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        uploaded_file.processing_status = 'processing'
        uploaded_file.save()

        # Crear registro de reconocimiento
        recognition = Recognition.objects.create(
            uploaded_file=uploaded_file,
            recognition_status='processing'
        )

        # Obtener tracks de referencia con sus fingerprints
        reference_tracks = []
        completed_tracks = Track.objects.filter(
            fingerprint_status='completed',
            is_reference_track=True
        ).select_related('artist', 'genre', 'mood', 'analysis')
        
        logger.info(f"🎵 Cargando tracks de referencia desde BD...")
        logger.info(f"📊 Tracks con fingerprint completado encontrados: {completed_tracks.count()}")
        
        for track in completed_tracks:
            if hasattr(track, 'analysis') and track.analysis.fingerprint_result:
                fingerprint_features = track.analysis.fingerprint_result.get('features', {})
                
                # Validar que las características estén completas
                required_keys = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
                missing_keys = [key for key in required_keys if key not in fingerprint_features]
                
                if missing_keys:
                    logger.warning(f"⚠️  Track {track.id} - {track.title}: faltan características {missing_keys}")
                    continue
                
                reference_tracks.append({
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist.name,
                    'fingerprint_features': fingerprint_features
                })
                
                logger.info(f"✅ Track {track.id} añadido: {track.title} - {track.artist.name}")
                logger.info(f"   Tempo: {fingerprint_features.get('tempo', 'N/A'):.2f} BPM")
                logger.info(f"   Centroide: {fingerprint_features.get('spectral_centroid_mean', 'N/A'):.2f} Hz")
            else:
                logger.warning(f"⚠️  Track {track.id} - {track.title}: sin análisis o fingerprint_result")
        
        logger.info(f"📊 Total de tracks de referencia válidos: {len(reference_tracks)}")

        if not reference_tracks:
            # No hay tracks de referencia
            recognition.recognition_status = 'error'
            recognition.recognition_error = 'No hay tracks de referencia disponibles'
            recognition.save()
            
            uploaded_file.processing_status = 'completed'
            uploaded_file.save()
            
            processing_time = time.time() - start_time
            recognition.processing_time = processing_time
            recognition.save()
            
            return {
                'success': False,
                'error': 'No hay tracks de referencia disponibles',
                'processing_time': processing_time
            }

        # Realizar reconocimiento
        result = audio_recognition_service.recognize_audio(
            uploaded_file.file.path, 
            reference_tracks
        )
        
        processing_time = time.time() - start_time
        recognition.processing_time = processing_time

        if result['success'] and result.get('recognized'):
            # Buscar el track correspondiente
            try:
                recognized_track = Track.objects.get(id=result['track_id'])
                
                # Actualizar reconocimiento con resultado exitoso
                recognition.recognized_track = recognized_track
                recognition.confidence = result.get('confidence', 0)
                recognition.offset_seconds = 0  # No calculamos offset en esta implementación
                recognition.fingerprinted_confidence = int(result.get('similarity', 0) * 100)
                recognition.recognition_status = 'found'
                recognition.dejavu_result = result
                recognition.save()
                
                # Actualizar archivo subido
                uploaded_file.processing_status = 'completed'
                uploaded_file.save()
                
                logger.info(f"Audio reconocido: {recognized_track.title} por {recognized_track.artist.name}")
                
                return {
                    'success': True,
                    'recognition_id': recognition.id,
                    'track': {
                        'id': recognized_track.id,
                        'title': recognized_track.title,
                        'artist': recognized_track.artist.name,
                        'genre': recognized_track.genre.name if recognized_track.genre else None,
                        'mood': recognized_track.mood.name if recognized_track.mood else None,
                    },
                    'confidence': recognition.confidence,
                    'similarity': result.get('similarity', 0),
                    'processing_time': processing_time
                }
                
            except Track.DoesNotExist:
                # Error de inconsistencia
                recognition.recognition_status = 'error'
                recognition.recognition_error = f"Track con ID {result['track_id']} no encontrado en la base de datos"
                recognition.dejavu_result = result
                recognition.save()
                
                uploaded_file.processing_status = 'error'
                uploaded_file.save()
                
                logger.warning(f"Track {result['track_id']} no encontrado en BD")
                
                return {
                    'success': False,
                    'error': 'Inconsistencia en base de datos',
                    'result': result
                }
        else:
            # No se encontró coincidencia
            recognition.recognition_status = 'not_found'
            recognition.recognition_error = result.get('message', 'No se encontró coincidencia')
            recognition.dejavu_result = result
            recognition.save()
            
            uploaded_file.processing_status = 'completed'
            uploaded_file.save()
            
            logger.info(f"No se encontró coincidencia para archivo {uploaded_file.name}")
            
            return {
                'success': False,
                'message': 'No se encontró coincidencia',
                'best_similarity': result.get('best_similarity', 0),
                'threshold': result.get('threshold', 0.7),
                'processing_time': processing_time,
                'recognition_id': recognition.id
            }

    except UploadedFile.DoesNotExist:
        logger.error(f"UploadedFile {uploaded_file_id} no encontrado")
        return {'success': False, 'error': 'Archivo no encontrado'}
    except Exception as e:
        logger.error(f"Error reconociendo archivo {uploaded_file_id}: {str(e)}")
        
        # Actualizar estados de error
        try:
            if 'recognition' in locals():
                recognition.recognition_status = 'error'
                recognition.recognition_error = str(e)
                recognition.save()
            
            uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
            uploaded_file.processing_status = 'error'
            uploaded_file.save()
        except:
            pass
            
        return {'success': False, 'error': str(e)}


@shared_task 
def batch_fingerprint_tracks(track_ids):
    """
    Procesa múltiples tracks en batch
    
    Args:
        track_ids (list): Lista de IDs de tracks
    
    Returns:
        dict: Resultado del procesamiento en batch
    """
    results = {
        'success': [],
        'errors': [],
        'total': len(track_ids)
    }
    
    for track_id in track_ids:
        try:
            result = fingerprint_track(track_id)
            if result['success']:
                results['success'].append(track_id)
            else:
                results['errors'].append({'track_id': track_id, 'error': result['error']})
        except Exception as e:
            results['errors'].append({'track_id': track_id, 'error': str(e)})
    
    logger.info(f"Batch fingerprinting completado: {len(results['success'])}/{results['total']} exitosos")
    return results


@shared_task
def cleanup_orphaned_fingerprints():
    """
    Limpia fingerprints huérfanos (versión simplificada)
    """
    try:
        # Limpiar cache de fingerprints
        audio_recognition_service.clear_cache()
        
        # Limpiar análisis sin track correspondiente
        orphaned_analyses = Analysis.objects.filter(track__isnull=True)
        count = orphaned_analyses.count()
        orphaned_analyses.delete()
        
        logger.info(f"Limpieza completada: {count} análisis huérfanos eliminados")
        return {'success': True, 'cleaned': count}
        
    except Exception as e:
        logger.error(f"Error en limpieza de fingerprints: {str(e)}")
        return {'success': False, 'error': str(e)}


def analyze_audio_file(file_path):
    """
    Analiza un archivo de audio usando pydub
    
    Args:
        file_path (str): Ruta al archivo de audio
    
    Returns:
        dict: Información del archivo
    """
    try:
        # Cargar archivo con pydub
        audio = AudioSegment.from_file(file_path)
        
        # Obtener información básica
        info = mediainfo(file_path)
        
        # Calcular métricas básicas
        max_amplitude = audio.max
        rms = audio.rms
        
        # Detectar clipping (simplificado)
        clipping_detected = max_amplitude >= 32767 * 0.99  # Para 16-bit
        
        # Calcular porcentaje de silencio (simplificado)
        silence_threshold = -50  # dB
        silence_segments = audio.split_on_silence(min_silence_len=100, silence_thresh=silence_threshold)
        total_silence = len(audio) - sum(len(segment) for segment in silence_segments)
        silence_percentage = (total_silence / len(audio)) * 100 if len(audio) > 0 else 0
        
        return {
            'duration_ms': len(audio),
            'duration_seconds': len(audio) / 1000.0,
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'frame_width': audio.frame_width,
            'max_amplitude': float(max_amplitude),
            'rms_amplitude': float(rms),
            'format': info.get('format_name', '').upper(),
            'bitrate': int(info.get('bit_rate', 0)) if info.get('bit_rate') else None,
            'file_size': os.path.getsize(file_path),
            'clipping_detected': clipping_detected,
            'silence_percentage': silence_percentage
        }
        
    except Exception as e:
        logger.error(f"Error analizando archivo {file_path}: {str(e)}")
        return None


def predict_genre_from_filename(filename):
    """
    Predicción simple de género basada en el nombre del archivo
    """
    filename_lower = filename.lower()
    
    if any(word in filename_lower for word in ['electronic', 'techno', 'house', 'edm']):
        return Genre.objects.get_or_create(name='Electronic')[0]
    elif any(word in filename_lower for word in ['rock', 'metal', 'punk']):
        return Genre.objects.get_or_create(name='Rock')[0]
    elif any(word in filename_lower for word in ['pop', 'mainstream']):
        return Genre.objects.get_or_create(name='Pop')[0]
    elif any(word in filename_lower for word in ['jazz', 'blues']):
        return Genre.objects.get_or_create(name='Jazz')[0]
    elif any(word in filename_lower for word in ['classical', 'orchestra']):
        return Genre.objects.get_or_create(name='Classical')[0]
    else:
        return Genre.objects.get_or_create(name='Unknown')[0]


def predict_mood_from_filename(filename):
    """
    Predicción simple de mood basada en el nombre del archivo
    """
    filename_lower = filename.lower()
    
    if any(word in filename_lower for word in ['happy', 'energetic', 'upbeat', 'dance']):
        return Mood.objects.get_or_create(name='Happy', defaults={'valence_score': 0.8})[0]
    elif any(word in filename_lower for word in ['sad', 'melancholy', 'depressing']):
        return Mood.objects.get_or_create(name='Sad', defaults={'valence_score': -0.6})[0]
    elif any(word in filename_lower for word in ['calm', 'relaxing', 'peaceful', 'ambient']):
        return Mood.objects.get_or_create(name='Calm', defaults={'valence_score': 0.2})[0]
    elif any(word in filename_lower for word in ['aggressive', 'angry', 'intense']):
        return Mood.objects.get_or_create(name='Aggressive', defaults={'valence_score': -0.2})[0]
    else:
        return Mood.objects.get_or_create(name='Neutral', defaults={'valence_score': 0.0})[0] 