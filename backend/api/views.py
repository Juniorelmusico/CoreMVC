from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import api_view, parser_classes, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .serializers import UserSerializer, NoteSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import Note, Artist, Genre, Mood, Track, Analysis, UploadedFile, MusicFile, Recognition
from .serializers import ArtistSerializer, GenreSerializer, MoodSerializer, TrackSerializer, AnalysisSerializer, UploadedFileSerializer, TrackUploadSerializer, MusicFileSerializer
from .tasks import fingerprint_track, recognize_audio_file, batch_fingerprint_tracks
from django.core.files.storage import default_storage
import os
from rest_framework.generics import RetrieveAPIView
import time
from django.urls import reverse
from rest_framework.routers import DefaultRouter
from django.core.files.base import ContentFile
import numpy as np
from scipy.io.wavfile import write
import tempfile


class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)


class NoteDelete(generics.DestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Si es superuser, puede ver todos los tracks
        if self.request.user.is_superuser:
            return Track.objects.all()
        # Si es usuario normal, solo sus tracks
        return Track.objects.filter(artist__user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Subir track y generar fingerprint con Dejavu
        """
        serializer = TrackUploadSerializer(data=request.data)
        if serializer.is_valid():
            # Get or create artist
            artist, _ = Artist.objects.get_or_create(
                name=serializer.validated_data['artist_name'],
                user=request.user
            )
            
            # Create track
            track = Track.objects.create(
                title=serializer.validated_data['title'],
                file=serializer.validated_data['file'],
                artist=artist,
                fingerprint_status='pending',
                is_reference_track=True,  # Tracks subidos por usuarios son de referencia
                reference_source='user_upload'
            )
            
            # Start fingerprinting task
            try:
                # Ejecutar fingerprinting directamente (sin Celery para desarrollo)
                from .tasks import fingerprint_track
                fingerprint_track(track.id)  # Llamada directa sin .delay()
            except Exception as e:
                # Si falla el fingerprinting, el track se queda en pending
                track.fingerprint_error = str(e)
                track.save()
            
            return Response(
                TrackSerializer(track).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        """
        Obtener análisis de un track
        """
        track = self.get_object()
        
        # Si el track tiene análisis completo, devolverlo con todas las características
        if hasattr(track, 'analysis') and track.analysis.fingerprint_result:
            analysis_data = AnalysisSerializer(track.analysis).data
            
            # Extraer características del fingerprint para mostrar información detallada
            fingerprint_features = track.analysis.fingerprint_result.get('features', {})
            
            # Crear un resumen de análisis musical
            music_analysis = {
                'track_id': track.id,
                'track_title': track.title,
                'artist_name': track.artist.name,
                'fingerprint_status': track.fingerprint_status,
                'fingerprints_count': track.fingerprints_count,
                
                # Características musicales extraídas
                'musical_features': {
                    'tempo_bpm': fingerprint_features.get('tempo', track.bpm),
                    'duration_seconds': track.duration,
                    'spectral_centroid_mean': fingerprint_features.get('spectral_centroid_mean'),
                    'spectral_centroid_std': fingerprint_features.get('spectral_centroid_std'),
                    'zero_crossing_rate_mean': fingerprint_features.get('zero_crossing_rate_mean'),
                    'mfcc_coefficients': fingerprint_features.get('mfcc_mean', [])[:5] if fingerprint_features.get('mfcc_mean') else [],
                    'chroma_features': fingerprint_features.get('chroma_mean', [])[:5] if fingerprint_features.get('chroma_mean') else [],
                    'spectral_contrast': fingerprint_features.get('contrast_mean', [])[:3] if fingerprint_features.get('contrast_mean') else [],
                },
                
                # Metadata del archivo
                'file_info': {
                    'format': track.analysis.file_format,
                    'sample_rate': track.sample_rate,
                    'channels': track.channels,
                    'bitrate': track.bitrate,
                    'file_size_mb': round(track.analysis.file_size_bytes / (1024*1024), 2) if track.analysis.file_size_bytes else None,
                },
                
                # Análisis de calidad
                'quality_analysis': {
                    'clipping_detected': track.analysis.clipping_detected,
                    'silence_percentage': track.analysis.silence_percentage,
                    'rms_amplitude': track.analysis.rms_amplitude,
                    'max_amplitude': track.analysis.max_amplitude,
                },
                
                'genre': track.genre.name if track.genre else 'Sin clasificar',
                'mood': track.mood.name if track.mood else 'Sin clasificar',
                'message': 'Análisis completo disponible con características musicales',
                'analysis_complete': True
            }
            
            return Response(music_analysis, status=status.HTTP_200_OK)
        
        # Si no hay análisis completo, devolver información básica del track
        return Response({
            'track_id': track.id,
            'track_title': track.title,
            'artist_name': track.artist.name if track.artist else 'Unknown Artist',
            'fingerprint_status': track.fingerprint_status,
            'fingerprint_error': track.fingerprint_error,
            'fingerprints_count': track.fingerprints_count,
            'message': 'Análisis en proceso o no disponible',
            'analysis_complete': False
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def test_endpoint(self, request, pk=None):
        """
        Endpoint de prueba para verificar que los actions funcionen
        """
        track = self.get_object()
        return Response({
            'message': 'Test endpoint working',
            'track_id': track.id,
            'track_title': track.title
        })

    @action(detail=True, methods=['get'])
    def simple_test(self, request, pk=None):
        """
        Test aún más simple
        """
        return Response({
            'message': 'Simple test working',
            'track_pk': pk
        })

    @action(detail=True, methods=['post'])
    def regenerate_fingerprint(self, request, pk=None):
        """
        Regenerar fingerprint de un track
        """
        track = self.get_object()
        track.fingerprint_status = 'pending'
        track.fingerprint_error = None
        track.save()
        
        fingerprint_track.delay(track.id)
        
        return Response({'message': 'Regeneración de fingerprint iniciada'})

    @action(detail=False, methods=['post'])
    def batch_fingerprint(self, request):
        """
        Generar fingerprints en batch para múltiples tracks
        """
        track_ids = request.data.get('track_ids', [])
        if not track_ids:
            return Response({'error': 'No track IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que todos los tracks pertenecen al usuario
        user_tracks = Track.objects.filter(
            id__in=track_ids, 
            artist__user=request.user
        ).values_list('id', flat=True)
        
        if len(user_tracks) != len(track_ids):
            return Response({'error': 'Some tracks do not belong to user'}, status=status.HTTP_403_FORBIDDEN)
        
        batch_fingerprint_tracks.delay(list(user_tracks))
        
        return Response({'message': f'Batch fingerprinting started for {len(user_tracks)} tracks'})


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticated]


class MoodViewSet(viewsets.ModelViewSet):
    queryset = Mood.objects.all()
    serializer_class = MoodSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnalysisViewSet(viewsets.ModelViewSet):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer


class FileUploadView(generics.CreateAPIView):
    """
    Vista para subir archivos de audio para reconocimiento USANDO AUDD
    REEMPLAZA el sistema anterior por reconocimiento real con AudD
    """
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({"error": "No file was provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validación de formato de archivo
        filename, extension = os.path.splitext(file_obj.name)
        extension = extension.lower()
        
        if extension not in ['.mp3', '.wav']:
            return Response(
                {"error": "Formato de archivo no válido. Solo se aceptan archivos MP3 y WAV."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create file data
        file_data = {
            'file': file_obj,
            'name': file_obj.name,
            'content_type': file_obj.content_type,
            'size': file_obj.size
        }
        
        serializer = self.get_serializer(data=file_data)
        if serializer.is_valid():
            try:
                uploaded_file = serializer.save(
                    uploaded_by=request.user,
                    file_purpose='recognition',
                    processing_status='processing'  # Cambiado de 'pending' a 'processing'
                )
                
                # *** AQUÍ ESTÁ EL CAMBIO PRINCIPAL ***
                # En lugar de usar el sistema anterior, usar AudD directamente
                try:
                    from .audd_service import get_audd_service
                    from django.core.files.storage import default_storage
                    import time
                    
                    start_time = time.time()
                    
                    # Obtener ruta completa del archivo
                    file_path = default_storage.path(uploaded_file.file.name)
                    
                    # Reconocer con AudD
                    service = get_audd_service()
                    audd_result = service.recognize_file(file_path)
                    
                    processing_time = time.time() - start_time
                    
                    # Crear registro de reconocimiento
                    recognition = Recognition.objects.create(
                        uploaded_file=uploaded_file,
                        processing_time=processing_time,
                        recognition_status='processing'
                    )
                    
                    if audd_result['success'] and audd_result.get('recognized'):
                        # *** CANCIÓN RECONOCIDA POR AUDD ***
                        external_info = audd_result['track_info']
                        
                        # Buscar si ya existe en tu BD (matching inteligente)
                        external_info = audd_result['track_info']
                        
                        # *** DEBUG: Información de AudD ***
                        print(f"🔍 AudD identificó:")
                        print(f"   Título: {external_info['title']}")
                        print(f"   Artista: {external_info['artist']}")
                        print(f"   Spotify ID: {external_info.get('spotify', {}).get('id')}")
                        
                        possible_tracks = find_matching_tracks(
                            title=external_info['title'],
                            artist=external_info['artist'],
                            user=request.user,
                            spotify_id=external_info.get('spotify', {}).get('id')
                        )
                        
                        print(f"🔍 Búsqueda resultado: {len(possible_tracks)} tracks encontrados")
                        if possible_tracks:
                            track = possible_tracks[0]
                            print(f"   ✅ ENCONTRADO: {track.title} - {track.artist.name} (Spotify: {track.spotify_id})")
                        else:
                            print(f"   ❌ NO ENCONTRADO en BD del usuario {request.user.username}")
                        
                        if possible_tracks:
                            # Existe en tu BD - usar el track existente
                            existing_track = possible_tracks[0]
                            recognition.recognized_track = existing_track
                            recognition.confidence = 0.95  # Alta confianza con AudD
                            recognition.recognition_status = 'found'
                            recognition.dejavu_result = {
                                'audd_result': audd_result,
                                'matched_with_existing': True,
                                'existing_track_id': existing_track.id
                            }
                            recognition.save()
                            
                            # Actualizar archivo
                            uploaded_file.processing_status = 'completed'
                            uploaded_file.save()
                            
                            # *** RESPUESTA INMEDIATA CON INFO REAL ***
                            return Response({
                                **serializer.data,
                                'recognition_preview': {
                                    'status': 'found',
                                    'track': {
                                        'id': existing_track.id,
                                        'title': existing_track.title,
                                        'artist': existing_track.artist.name,
                                        'genre': existing_track.genre.name if existing_track.genre else 'Sin clasificar',
                                        'mood': existing_track.mood.name if existing_track.mood else 'Sin clasificar'
                                    },
                                    'audd_identified': {
                                        'title': external_info['title'],
                                        'artist': external_info['artist'],
                                        'album': external_info.get('album'),
                                        'spotify_id': external_info.get('spotify', {}).get('id'),
                                        'apple_music_url': external_info.get('apple_music', {}).get('url')
                                    },
                                    'confidence': 0.95,
                                    'processing_time': processing_time,
                                    'recognition_id': recognition.id,
                                    'message': f'✅ Reconocida: "{external_info["title"]}" por {external_info["artist"]} (Existe en tu BD)'
                                }
                            }, status=status.HTTP_201_CREATED)
                        
                        else:
                            # No existe en tu BD - mostrar info de AudD sin crear track
                            recognition.recognized_track = None  # No track asociado
                            recognition.confidence = 0.95
                            recognition.recognition_status = 'found'
                            recognition.dejavu_result = {
                                'audd_result': audd_result,
                                'track_not_in_db': True,
                                'external_only': True
                            }
                            recognition.save()
                            
                            uploaded_file.processing_status = 'completed'
                            uploaded_file.save()
                            
                            return Response({
                                **serializer.data,
                                'recognition_preview': {
                                    'status': 'found',
                                    'track': None,  # No track en BD
                                    'audd_identified': {
                                        'title': external_info['title'],
                                        'artist': external_info['artist'],
                                        'album': external_info.get('album'),
                                        'spotify_id': external_info.get('spotify', {}).get('id'),
                                        'apple_music_url': external_info.get('apple_music', {}).get('url'),
                                        'release_date': external_info.get('release_date'),
                                        'genres': external_info.get('apple_music', {}).get('genres', [])
                                    },
                                    'confidence': 0.95,
                                    'processing_time': processing_time,
                                    'recognition_id': recognition.id,
                                    'message': f'✅ Reconocida: "{external_info["title"]}" por {external_info["artist"]} (No existe en tu BD - Info solo de AudD)'
                                }
                            }, status=status.HTTP_201_CREATED)
                    
                    else:
                        # AudD no reconoció la canción
                        recognition.recognition_status = 'not_found'
                        
                        # Verificar si es error de cuota
                        if audd_result.get('quota_exceeded'):
                            recognition.recognition_error = f"Límite de API: {audd_result.get('message', 'Cuota diaria agotada')}"
                            recognition.recognition_status = 'error'
                            message = audd_result.get('message', 'Has alcanzado el límite diario de AudD')
                        else:
                            recognition.recognition_error = audd_result.get('message', 'Canción no encontrada en AudD')
                            message = 'Canción no encontrada en la base de datos de AudD'
                        
                        recognition.dejavu_result = {'audd_result': audd_result}
                        recognition.save()
                        
                        uploaded_file.processing_status = 'completed'
                        uploaded_file.save()
                        
                        return Response({
                            **serializer.data,
                            'recognition_preview': {
                                'status': recognition.recognition_status,
                                'confidence': 0.0,
                                'processing_time': processing_time,
                                'recognition_id': recognition.id,
                                'message': message,
                                'quota_exceeded': audd_result.get('quota_exceeded', False),
                                'error': audd_result.get('error') if audd_result.get('quota_exceeded') else None
                            }
                        }, status=status.HTTP_201_CREATED)
                
                except Exception as audd_error:
                    # Error con AudD - crear reconocimiento con error
                    recognition = Recognition.objects.create(
                        uploaded_file=uploaded_file,
                        recognition_status='error',
                        recognition_error=f'Error AudD: {str(audd_error)}',
                        processing_time=time.time() - start_time if 'start_time' in locals() else 0
                    )
                    
                    uploaded_file.processing_status = 'error'
                    uploaded_file.save()
                    
                    return Response({
                        **serializer.data,
                        'recognition_preview': {
                            'status': 'error',
                            'error': f'Error en reconocimiento: {str(audd_error)}',
                            'recognition_id': recognition.id
                        }
                    }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {"error": f"Error saving file: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FileListView(generics.ListAPIView):
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Obtener solo los archivos subidos por el usuario actual
        return UploadedFile.objects.filter(uploaded_by=self.request.user).order_by('-uploaded_at')


class RecognitionListView(generics.ListAPIView):
    """
    Vista para listar reconocimientos de audio del usuario
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Recognition.objects.filter(
            uploaded_file__uploaded_by=self.request.user
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        recognitions = self.get_queryset()
        
        data = []
        for recognition in recognitions:
            recognition_data = {
                'id': recognition.id,
                'uploaded_file': {
                    'id': recognition.uploaded_file.id,
                    'name': recognition.uploaded_file.name,
                    'uploaded_at': recognition.uploaded_file.uploaded_at
                },
                'recognition_status': recognition.recognition_status,
                'confidence': recognition.confidence,
                'offset_seconds': recognition.offset_seconds,
                'processing_time': recognition.processing_time,
                'created_at': recognition.created_at,
                'recognized_track': None
            }
            
            if recognition.recognized_track:
                recognition_data['recognized_track'] = {
                    'id': recognition.recognized_track.id,
                    'title': recognition.recognized_track.title,
                    'artist': recognition.recognized_track.artist.name,
                    'genre': recognition.recognized_track.genre.name if recognition.recognized_track.genre else None,
                    'mood': recognition.recognized_track.mood.name if recognition.recognized_track.mood else None,
                    'duration': recognition.recognized_track.duration,
                    'bpm': recognition.recognized_track.bpm
                }
            
            data.append(recognition_data)
        
        return Response(data)


class RecognitionDetailView(generics.RetrieveAPIView):
    """
    Vista para obtener detalles de un reconocimiento específico
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        recognition_id = self.kwargs['pk']
        return get_object_or_404(
            Recognition,
            id=recognition_id,
            uploaded_file__uploaded_by=self.request.user
        )
    
    def retrieve(self, request, *args, **kwargs):
        recognition = self.get_object()
        
        data = {
            'id': recognition.id,
            'recognition_status': recognition.recognition_status,
            'confidence': recognition.confidence,
            'offset_seconds': recognition.offset_seconds,
            'fingerprinted_confidence': recognition.fingerprinted_confidence,
            'processing_time': recognition.processing_time,
            'recognition_error': recognition.recognition_error,
            'created_at': recognition.created_at,
            'dejavu_result': recognition.dejavu_result,
            'uploaded_file': {
                'id': recognition.uploaded_file.id,
                'name': recognition.uploaded_file.name,
                'size': recognition.uploaded_file.size,
                'uploaded_at': recognition.uploaded_file.uploaded_at
            },
            'recognized_track': None
        }
        
        if recognition.recognized_track:
            track = recognition.recognized_track
            data['recognized_track'] = {
                'id': track.id,
                'title': track.title,
                'artist': {
                    'id': track.artist.id,
                    'name': track.artist.name,
                    'description': track.artist.description,
                    'country': track.artist.country
                },
                'genre': {
                    'id': track.genre.id,
                    'name': track.genre.name,
                    'description': track.genre.description
                } if track.genre else None,
                'mood': {
                    'id': track.mood.id,
                    'name': track.mood.name,
                    'description': track.mood.description,
                    'valence_score': track.mood.valence_score
                } if track.mood else None,
                'duration': track.duration,
                'bpm': track.bpm,
                'uploaded_at': track.uploaded_at,
                'fingerprints_count': track.fingerprints_count
            }
        
        return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recognition_status(request, file_id):
    """
    Endpoint para polling del estado de reconocimiento
    ACTUALIZADO para mostrar información real de AudD
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            id=file_id,
            uploaded_by=request.user
        )
        
        # Buscar el reconocimiento más reciente para este archivo
        recognition = Recognition.objects.filter(
            uploaded_file=uploaded_file
        ).order_by('-created_at').first()
        
        if not recognition:
            return Response({
                'status': 'processing',
                'message': 'Recognition not started yet'
            })
        
        # *** INFORMACIÓN REAL DE AUDD ***
        response_data = {
            'status': recognition.recognition_status,
            'processing_time': recognition.processing_time,
            'confidence': recognition.confidence,
            'recognition_id': recognition.id
        }
        
        # Extraer información de AudD del resultado
        audd_info = None
        if recognition.dejavu_result and 'audd_result' in recognition.dejavu_result:
            audd_result = recognition.dejavu_result['audd_result']
            if audd_result.get('track_info'):
                audd_info = audd_result['track_info']
        
        if recognition.recognized_track:
            # CASO 1: Track existe en tu BD
            response_data['track'] = {
                'id': recognition.recognized_track.id,
                'title': recognition.recognized_track.title,
                'artist': recognition.recognized_track.artist.name,
                'genre': recognition.recognized_track.genre.name if recognition.recognized_track.genre else 'Sin clasificar',
                'mood': recognition.recognized_track.mood.name if recognition.recognized_track.mood else 'Sin clasificar',
            }
            
            # *** AGREGAR INFORMACIÓN REAL DE AUDD ***
            if audd_info:
                response_data['audd_identified'] = {
                    'real_title': audd_info['title'],
                    'real_artist': audd_info['artist'],
                    'album': audd_info.get('album'),
                    'spotify_id': audd_info.get('spotify', {}).get('id'),
                    'spotify_preview': audd_info.get('spotify', {}).get('preview_url'),
                    'apple_music_url': audd_info.get('apple_music', {}).get('url'),
                    'apple_music_artwork': audd_info.get('apple_music', {}).get('artwork'),
                    'release_date': audd_info.get('release_date'),
                    'genres': audd_info.get('apple_music', {}).get('genres', [])
                }
                
                # Comparar información de BD vs AudD
                response_data['comparison'] = {
                    'bd_vs_audd': {
                        'title_match': recognition.recognized_track.title.lower() == audd_info['title'].lower(),
                        'artist_match': recognition.recognized_track.artist.name.lower() == audd_info['artist'].lower(),
                        'bd_title': recognition.recognized_track.title,
                        'audd_title': audd_info['title'],
                        'bd_artist': recognition.recognized_track.artist.name,
                        'audd_artist': audd_info['artist']
                    }
                }
                
                response_data['message'] = f'✅ Identificada: "{audd_info["title"]}" por {audd_info["artist"]} (Existe en tu BD)'
            else:
                response_data['message'] = f'✅ Canción reconocida (ID: {recognition.recognized_track.id})'
        
        elif audd_info:
            # CASO 2: No hay track en BD pero sí información de AudD
            response_data['track'] = None
            response_data['audd_identified'] = {
                'real_title': audd_info['title'],
                'real_artist': audd_info['artist'],
                'album': audd_info.get('album'),
                'spotify_id': audd_info.get('spotify', {}).get('id'),
                'spotify_preview': audd_info.get('spotify', {}).get('preview_url'),
                'apple_music_url': audd_info.get('apple_music', {}).get('url'),
                'apple_music_artwork': audd_info.get('apple_music', {}).get('artwork'),
                'release_date': audd_info.get('release_date'),
                'genres': audd_info.get('apple_music', {}).get('genres', [])
            }
            
            response_data['comparison'] = {
                'track_in_db': False,
                'message': 'Track no existe en tu BD, pero identificado por AudD'
            }
            
            response_data['message'] = f'✅ Identificada: "{audd_info["title"]}" por {audd_info["artist"]} (Solo información de AudD)'
        
        if recognition.recognition_error:
            response_data['error'] = recognition.recognition_error
            
            # Si es error de AudD, dar más contexto
            if 'AudD' in recognition.recognition_error:
                response_data['message'] = 'Error conectando con el servicio de identificación de música'
        
        return Response(response_data)
        
    except UploadedFile.DoesNotExist:
        return Response(
            {'error': 'File not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# Vistas para administradores
class AdminUserListView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().order_by('-date_joined')


class AdminFileListView(generics.ListAPIView):
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAdminUser]
    queryset = UploadedFile.objects.all().order_by('-uploaded_at')


class AdminUserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()


class AdminFileDeleteView(generics.DestroyAPIView):
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAdminUser]
    queryset = UploadedFile.objects.all()


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    """
    Vista para obtener estadísticas básicas del dashboard de administrador
    """
    users_count = User.objects.count()
    files_count = UploadedFile.objects.count()
    tracks_count = Track.objects.count()
    recognitions_count = Recognition.objects.count()
    
    # Estadísticas de fingerprinting
    fingerprinted_tracks = Track.objects.filter(fingerprint_status='completed').count()
    pending_fingerprints = Track.objects.filter(fingerprint_status='pending').count()
    
    # Estadísticas de reconocimiento
    successful_recognitions = Recognition.objects.filter(recognition_status='found').count()
    failed_recognitions = Recognition.objects.filter(recognition_status='not_found').count()
    
    total_file_size = UploadedFile.objects.all().values_list('size', flat=True)
    total_size_mb = sum(total_file_size) / (1024 * 1024) if total_file_size else 0
    
    # Últimos usuarios registrados
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    recent_users_data = UserSerializer(recent_users, many=True).data
    
    # Últimos archivos subidos
    recent_files = UploadedFile.objects.all().order_by('-uploaded_at')[:5]
    recent_files_data = UploadedFileSerializer(recent_files, many=True).data
    
    return Response({
        'users_count': users_count,
        'files_count': files_count,
        'tracks_count': tracks_count,
        'recognitions_count': recognitions_count,
        'fingerprinted_tracks': fingerprinted_tracks,
        'pending_fingerprints': pending_fingerprints,
        'successful_recognitions': successful_recognitions,
        'failed_recognitions': failed_recognitions,
        'storage_used_mb': round(total_size_mb, 2),
        'recent_users': recent_users_data,
        'recent_files': recent_files_data
    })


# Vistas CRUD para administradores
class AdminArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AdminGenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminUser]


class AdminMoodViewSet(viewsets.ModelViewSet):
    queryset = Mood.objects.all()
    serializer_class = MoodSerializer
    permission_classes = [IsAdminUser]


class AdminTrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create':
            from .serializers import TrackCreateSerializer
            return TrackCreateSerializer
        from .serializers import TrackSerializer
        return TrackSerializer

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if file_obj:
            filename, extension = os.path.splitext(file_obj.name)
            extension = extension.lower()
            if extension not in ['.mp3', '.wav']:
                return Response(
                    {"error": "Formato de archivo no válido. Solo se aceptan archivos MP3 y WAV."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        response = super().create(request, *args, **kwargs)
        
        # Si se creó exitosamente, iniciar fingerprinting
        if response.status_code == status.HTTP_201_CREATED:
            track_id = response.data.get('id')
            if track_id:
                fingerprint_track.delay(track_id)
        
        return response

    @action(detail=False, methods=['post'])
    def batch_fingerprint(self, request):
        """
        Generar fingerprints en batch para tracks seleccionados
        """
        track_ids = request.data.get('track_ids', [])
        if not track_ids:
            return Response({'error': 'No track IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        batch_fingerprint_tracks.delay(track_ids)
        
        return Response({'message': f'Batch fingerprinting started for {len(track_ids)} tracks'})


class AdminAnalysisViewSet(viewsets.ModelViewSet):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAdminUser]


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_model_stats(request):
    """
    Vista para obtener estadísticas de los modelos
    """
    artists_count = Artist.objects.count()
    genres_count = Genre.objects.count()
    moods_count = Mood.objects.count()
    tracks_count = Track.objects.count()
    analyses_count = Analysis.objects.count()
    
    # Datos recientes
    recent_artists = ArtistSerializer(Artist.objects.all().order_by('-created_at')[:5], many=True).data
    recent_tracks = TrackSerializer(Track.objects.all().order_by('-uploaded_at')[:5], many=True).data
    
    return Response({
        'artists_count': artists_count,
        'genres_count': genres_count,
        'moods_count': moods_count,
        'tracks_count': tracks_count,
        'analyses_count': analyses_count,
        'recent_artists': recent_artists,
        'recent_tracks': recent_tracks
    })


class MusicFileViewSet(viewsets.ModelViewSet):
    """
    ViewSet simplificado para compatibilidad
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MusicFileSerializer
    
    def get_queryset(self):
        return MusicFile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        music_file = serializer.save(user=self.request.user)
        return music_file


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_auth(request):
    """
    Endpoint de prueba para verificar autenticación
    """
    return Response({
        'authenticated': True,
        'user': request.user.username,
        'user_id': request.user.id,
        'is_superuser': request.user.is_superuser,
        'message': 'Authentication working correctly',
        'auth_header': request.META.get('HTTP_AUTHORIZATION', 'No Authorization header')
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def test_no_auth(request):
    """
    Endpoint de prueba sin autenticación requerida
    """
    return Response({
        'message': 'Server working correctly',
        'has_auth_header': 'HTTP_AUTHORIZATION' in request.META,
        'auth_header': request.META.get('HTTP_AUTHORIZATION', 'No Authorization header')[:50] + '...' if request.META.get('HTTP_AUTHORIZATION') else 'None'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_routes(request):
    """
    Endpoint de diagnóstico para mostrar rutas registradas
    """
    # Crear router temporal para mostrar rutas
    router = DefaultRouter()
    router.register(r'tracks', TrackViewSet, basename='track')
    
    # Obtener todas las rutas del TrackViewSet
    track_routes = []
    for pattern in router.urls:
        track_routes.append({
            'pattern': str(pattern.pattern),
            'name': pattern.name,
            'callback': str(pattern.callback)
        })
    
    # Información adicional sobre los métodos del TrackViewSet
    viewset_methods = []
    for attr_name in dir(TrackViewSet):
        if not attr_name.startswith('_'):
            attr = getattr(TrackViewSet, attr_name)
            if hasattr(attr, 'mapping'):
                viewset_methods.append({
                    'method': attr_name,
                    'mapping': attr.mapping
                })
    
    return Response({
        'message': 'Diagnóstico de rutas del TrackViewSet',
        'registered_routes': track_routes,
        'viewset_methods_with_actions': viewset_methods,
        'total_routes': len(track_routes),
        'analysis_method_exists': hasattr(TrackViewSet, 'analysis'),
        'analysis_has_action_decorator': hasattr(getattr(TrackViewSet, 'analysis', None), 'mapping')
    })

# ENDPOINT DE DEBUGGING PARA VERIFICAR TRACKS DE REFERENCIA
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_reference_tracks(request):
    """
    Endpoint de debugging para verificar tracks de referencia
    """
    try:
        completed_tracks = Track.objects.filter(
            fingerprint_status='completed',
            is_reference_track=True
        ).select_related('artist', 'genre', 'mood', 'analysis')
        
        tracks_info = []
        for track in completed_tracks:
            track_data = {
                'id': track.id,
                'title': track.title,
                'artist': track.artist.name,
                'fingerprint_status': track.fingerprint_status,
                'fingerprints_count': track.fingerprints_count,
                'dejavu_song_id': track.dejavu_song_id,
                'has_analysis': hasattr(track, 'analysis'),
                'has_fingerprint_result': False,
                'fingerprint_features': None
            }
            
            if hasattr(track, 'analysis') and track.analysis.fingerprint_result:
                track_data['has_fingerprint_result'] = True
                features = track.analysis.fingerprint_result.get('features', {})
                
                # Verificar características principales
                required_keys = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
                missing_keys = [key for key in required_keys if key not in features]
                
                track_data['fingerprint_features'] = {
                    'has_all_required_keys': len(missing_keys) == 0,
                    'missing_keys': missing_keys,
                    'tempo': features.get('tempo'),
                    'spectral_centroid_mean': features.get('spectral_centroid_mean'),
                    'duration': features.get('duration'),
                    'mfcc_length': len(features.get('mfcc_mean', [])),
                    'chroma_length': len(features.get('chroma_mean', [])),
                    'contrast_length': len(features.get('contrast_mean', []))
                }
            
            tracks_info.append(track_data)
        
        return Response({
            'total_completed_tracks': completed_tracks.count(),
            'tracks_with_valid_fingerprints': len([t for t in tracks_info if t['has_fingerprint_result']]),
            'tracks': tracks_info
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error en debug: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_recognition_debug(request):
    """
    Endpoint para probar reconocimiento con debugging detallado
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = request.FILES['file']
    
    try:
        # Crear archivo temporal para testing
        from django.core.files.storage import default_storage
        import tempfile
        import os
        
        # Guardar archivo temporalmente
        temp_filename = f"test_recognition_{file_obj.name}"
        file_path = default_storage.save(temp_filename, file_obj)
        full_path = default_storage.path(file_path)
        
        # Obtener tracks de referencia
        from .models import Track
        reference_tracks = []
        completed_tracks = Track.objects.filter(
            fingerprint_status='completed',
            is_reference_track=True
        ).select_related('artist', 'analysis')
        
        for track in completed_tracks:
            if hasattr(track, 'analysis') and track.analysis.fingerprint_result:
                reference_tracks.append({
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist.name,
                    'fingerprint_features': track.analysis.fingerprint_result.get('features', {})
                })
        
        # Ejecutar reconocimiento
        from .dejavu_service import audio_recognition_service
        result = audio_recognition_service.recognize_audio(full_path, reference_tracks)
        
        # Limpiar archivo temporal
        try:
            default_storage.delete(file_path)
        except:
            pass
        
        return Response({
            'debug_info': {
                'file_name': file_obj.name,
                'file_size': file_obj.size,
                'reference_tracks_count': len(reference_tracks),
                'reference_tracks': [
                    {
                        'id': t['id'],
                        'title': t['title'],
                        'artist': t['artist']
                    } for t in reference_tracks
                ]
            },
            'recognition_result': result
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error en test de reconocimiento: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debug_recognition_step_by_step(request):
    """
    Endpoint para debugging paso a paso del reconocimiento
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = request.FILES['file']
    debug_info = {
        'steps': [],
        'file_info': {
            'name': file_obj.name,
            'size': file_obj.size,
            'content_type': file_obj.content_type
        }
    }
    
    try:
        from django.core.files.storage import default_storage
        from .models import Track
        from .dejavu_service import audio_recognition_service
        
        # PASO 1: Guardar archivo temporalmente
        debug_info['steps'].append("PASO 1: Guardando archivo temporal")
        temp_filename = f"debug_recognition_{file_obj.name}"
        file_path = default_storage.save(temp_filename, file_obj)
        full_path = default_storage.path(file_path)
        debug_info['temp_file_path'] = full_path
        
        # PASO 2: Obtener tracks de referencia
        debug_info['steps'].append("PASO 2: Cargando tracks de referencia")
        completed_tracks = Track.objects.filter(
            fingerprint_status='completed',
            is_reference_track=True
        ).select_related('artist', 'analysis')
        
        debug_info['total_tracks_in_db'] = completed_tracks.count()
        
        reference_tracks = []
        track_details = []
        
        for track in completed_tracks:
            track_info = {
                'id': track.id,
                'title': track.title,
                'artist': track.artist.name,
                'has_analysis': hasattr(track, 'analysis'),
                'has_fingerprint_result': False
            }
            
            if hasattr(track, 'analysis') and track.analysis and track.analysis.fingerprint_result:
                fingerprint_features = track.analysis.fingerprint_result.get('features', {})
                
                # Verificar que tenga todas las características requeridas
                required_keys = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
                missing_keys = [key for key in required_keys if key not in fingerprint_features]
                
                if not missing_keys:
                    reference_tracks.append({
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist.name,
                        'fingerprint_features': fingerprint_features
                    })
                    track_info['has_fingerprint_result'] = True
                    track_info['tempo'] = fingerprint_features.get('tempo')
                    track_info['spectral_centroid'] = fingerprint_features.get('spectral_centroid_mean')
                else:
                    track_info['missing_keys'] = missing_keys
            
            track_details.append(track_info)
        
        debug_info['reference_tracks_count'] = len(reference_tracks)
        debug_info['track_details'] = track_details
        
        if not reference_tracks:
            debug_info['steps'].append("❌ ERROR: No hay tracks de referencia válidos")
            return Response(debug_info)
        
        # PASO 3: Extraer características del archivo subido
        debug_info['steps'].append("PASO 3: Extrayendo características del audio")
        fingerprint_service = audio_recognition_service.fingerprint
        query_result = fingerprint_service.extract_features(full_path)
        
        if not query_result['success']:
            debug_info['steps'].append(f"❌ ERROR extrayendo características: {query_result.get('error')}")
            return Response(debug_info)
        
        query_features = query_result['features']
        debug_info['query_features'] = {
            'tempo': query_features.get('tempo'),
            'spectral_centroid_mean': query_features.get('spectral_centroid_mean'),
            'duration': query_features.get('duration'),
            'mfcc_length': len(query_features.get('mfcc_mean', [])),
            'chroma_length': len(query_features.get('chroma_mean', [])),
            'contrast_length': len(query_features.get('contrast_mean', []))
        }
        
        # PASO 4: Comparar con cada track
        debug_info['steps'].append("PASO 4: Comparando con tracks de referencia")
        comparisons = []
        best_similarity = 0.0
        best_match = None
        
        for i, track in enumerate(reference_tracks):
            comparison_info = {
                'track_id': track['id'],
                'title': track['title'],
                'artist': track['artist'],
                'comparison_step': i + 1
            }
            
            # Realizar comparación manual paso a paso
            ref_features = track['fingerprint_features']
            
            try:
                # Verificar que ambos tengan las características necesarias
                required_keys = ['mfcc_mean', 'chroma_mean', 'contrast_mean', 'tempo', 'spectral_centroid_mean']
                query_missing = [key for key in required_keys if key not in query_features]
                ref_missing = [key for key in required_keys if key not in ref_features]
                
                if query_missing or ref_missing:
                    comparison_info['error'] = f"Faltan claves - Query: {query_missing}, Ref: {ref_missing}"
                    comparison_info['similarity'] = 0.0
                else:
                    # Calcular similitud usando la función del servicio
                    similarity = fingerprint_service.compare_fingerprints(query_features, ref_features)
                    comparison_info['similarity'] = similarity
                    
                    # Información detallada de la comparación
                    comparison_info['details'] = {
                        'query_tempo': query_features.get('tempo'),
                        'ref_tempo': ref_features.get('tempo'),
                        'tempo_diff': abs(query_features.get('tempo', 0) - ref_features.get('tempo', 0)),
                        'query_centroid': query_features.get('spectral_centroid_mean'),
                        'ref_centroid': ref_features.get('spectral_centroid_mean'),
                        'centroid_diff': abs(query_features.get('spectral_centroid_mean', 0) - ref_features.get('spectral_centroid_mean', 0))
                    }
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = track
                
            except Exception as e:
                comparison_info['error'] = str(e)
                comparison_info['similarity'] = 0.0
            
            comparisons.append(comparison_info)
        
        # Ordenar por similitud
        comparisons.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        debug_info['comparisons'] = comparisons
        debug_info['best_similarity'] = best_similarity
        debug_info['similarity_threshold'] = 0.85
        
        # PASO 5: Resultado final
        if best_match and best_similarity >= 0.85:
            debug_info['steps'].append(f"✅ ÉXITO: Canción reconocida con {best_similarity:.4f} similitud")
            debug_info['final_result'] = {
                'recognized': True,
                'track': best_match,
                'confidence': best_similarity
            }
        else:
            debug_info['steps'].append(f"❌ NO RECONOCIDO: Mejor similitud {best_similarity:.4f} < 0.85")
            debug_info['final_result'] = {
                'recognized': False,
                'best_similarity': best_similarity,
                'message': 'No se encontró coincidencia suficiente'
            }
        
        # Limpiar archivo temporal
        try:
            default_storage.delete(file_path)
            debug_info['steps'].append("PASO 6: Archivo temporal eliminado")
        except:
            pass
        
        return Response(debug_info)
        
    except Exception as e:
        debug_info['steps'].append(f"❌ ERROR GENERAL: {str(e)}")
        debug_info['error'] = str(e)
        return Response(debug_info, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NUEVOS ENDPOINTS SIMPLIFICADOS PARA RECONOCIMIENTO PRECISO

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_recognition(request):
    """
    Reconocimiento inteligente que integra AudD con tu base de datos
    Permite enriquecer tracks existentes y tener control total sobre la información
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = request.FILES['file']
    
    # Opciones de configuración
    auto_create = request.data.get('auto_create', 'true').lower() == 'true'
    update_existing = request.data.get('update_existing', 'true').lower() == 'true'
    use_service = request.data.get('service', 'audd')
    
    try:
        from django.core.files.storage import default_storage
        from .audd_service import get_audd_service
        
        # Guardar archivo temporalmente
        temp_filename = f"smart_recognition_{file_obj.name}"
        file_path = default_storage.save(temp_filename, file_obj)
        full_path = default_storage.path(file_path)
        
        # Reconocer con AudD
        service = get_audd_service()
        recognition_result = service.recognize_file(full_path)
        
        # Limpiar archivo temporal
        try:
            default_storage.delete(file_path)
        except:
            pass
        
        if not recognition_result['success'] or not recognition_result.get('recognized'):
            return Response({
                'recognized': False,
                'service_used': use_service,
                'message': recognition_result.get('message', 'No se pudo reconocer la música'),
                'error': recognition_result.get('error')
            })
        
        # Información reconocida por AudD
        external_info = recognition_result['track_info']
        
        # PASO 1: Buscar tracks existentes (más inteligente)
        possible_tracks = find_matching_tracks(
            title=external_info['title'],
            artist=external_info['artist'],
            user=request.user,
            spotify_id=external_info.get('spotify', {}).get('id')
        )
        
        response_data = {
            'recognized': True,
            'service_used': use_service,
            'external_info': external_info,
            'possible_matches': len(possible_tracks),
        }
        
        if possible_tracks:
            # CASO 1: Track ya existe en tu BD
            existing_track = possible_tracks[0]  # El mejor match
            
            # Enriquecer track existente con nueva información
            if update_existing:
                updated_track = enrich_existing_track(existing_track, external_info)
                response_data.update({
                    'track_exists_in_db': True,
                    'track_updated': update_existing,
                    'track': serialize_track_with_enrichment(updated_track, external_info),
                    'enrichment_applied': get_enrichment_summary(existing_track, external_info)
                })
            else:
                response_data.update({
                    'track_exists_in_db': True,
                    'track_updated': False,
                    'track': serialize_track_with_enrichment(existing_track, external_info)
                })
        
        else:
            # CASO 2: Track no existe, mostrar información de AudD sin crear
            if auto_create:
                response_data.update({
                    'track_exists_in_db': False,
                    'track_created': False,
                    'audd_info_only': True,
                    'external_track_info': serialize_external_info_only(external_info),
                    'message': 'Track no existe en BD. Información solo de AudD (no se creó track automáticamente)'
                })
            else:
                response_data.update({
                    'track_exists_in_db': False,
                    'track_created': False,
                    'message': 'Track no existe. Usar auto_create=true para más opciones'
                })
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': f'Error en reconocimiento inteligente: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def find_matching_tracks(title, artist, user, spotify_id=None):
    """
    Buscar tracks que coincidan de manera inteligente
    PRIORIDAD: 1. spotify_id, 2. título/artista exacto, 3. similitud
    """
    from django.db.models import Q
    import difflib
    
    print(f"🔍 find_matching_tracks llamado:")
    print(f"   Usuario: {user.username} (ID: {user.id})")
    print(f"   Título: {title}")
    print(f"   Artista: {artist}")
    print(f"   Spotify ID: {spotify_id}")
    
    # PRIORIDAD 1: Buscar por spotify_id (más preciso)
    if spotify_id:
        print(f"🎯 Buscando por Spotify ID: {spotify_id}")
        
        # Primero buscar SIN filtro de usuario para debug
        all_spotify_tracks = Track.objects.filter(spotify_id=spotify_id)
        print(f"   Tracks totales con este Spotify ID: {all_spotify_tracks.count()}")
        for track in all_spotify_tracks:
            print(f"     - {track.title} por {track.artist.name} (User: {track.artist.user.username})")
        
        # Ahora buscar CON filtro de usuario
        spotify_matches = Track.objects.filter(
            spotify_id=spotify_id,
            artist__user=user
        ).select_related('artist', 'genre', 'mood')
        
        print(f"   Tracks del usuario {user.username}: {spotify_matches.count()}")
        
        if spotify_matches.exists():
            print(f"🎯 MATCH por Spotify ID: {spotify_id}")
            return list(spotify_matches)
        else:
            print(f"❌ NO MATCH por Spotify ID para usuario {user.username}")
    
    # Normalizar strings para comparación
    title_clean = title.lower().strip()
    artist_clean = artist.lower().strip()
    
    # PRIORIDAD 2: Buscar coincidencias exactas por título/artista
    exact_matches = Track.objects.filter(
        Q(title__iexact=title) & Q(artist__name__iexact=artist),
        artist__user=user
    ).select_related('artist', 'genre', 'mood')
    
    if exact_matches.exists():
        print(f"🎯 MATCH exacto: {title} - {artist}")
        return list(exact_matches)
    
    # PRIORIDAD 3: Buscar coincidencias similares
    similar_tracks = Track.objects.filter(
        artist__user=user
    ).select_related('artist', 'genre', 'mood')
    
    matches = []
    for track in similar_tracks:
        title_similarity = difflib.SequenceMatcher(
            None, title_clean, track.title.lower()
        ).ratio()
        artist_similarity = difflib.SequenceMatcher(
            None, artist_clean, track.artist.name.lower()
        ).ratio()
        
        # Si ambos tienen alta similitud, es probable que sea el mismo track
        if title_similarity > 0.8 and artist_similarity > 0.8:
            matches.append((track, title_similarity + artist_similarity))
    
    # Ordenar por similitud y devolver los mejores matches
    matches.sort(key=lambda x: x[1], reverse=True)
    if matches:
        print(f"🎯 MATCH por similitud: {matches[0][0].title} - {matches[0][0].artist.name}")
    return [match[0] for match in matches[:3]]


def enrich_existing_track(track, external_info):
    """
    Enriquecer track existente con información externa
    """
    updated = False
    
    # Actualizar información faltante o mejorar existente
    if not track.bpm and external_info.get('tempo'):
        track.bpm = external_info['tempo']
        updated = True
    
    if not track.duration and external_info.get('duration'):
        track.duration = external_info['duration']
        updated = True
    
    # Agregar spotify_id si no lo tiene
    if not track.spotify_id and external_info.get('spotify', {}).get('id'):
        track.spotify_id = external_info['spotify']['id']
        updated = True
        print(f"✅ Spotify ID agregado: {track.spotify_id}")
    
    # Asignar género automáticamente si no tiene
    if not track.genre and external_info.get('apple_music', {}).get('genres'):
        genre_name = external_info['apple_music']['genres'][0]
        genre, _ = Genre.objects.get_or_create(name=genre_name)
        track.genre = genre
        updated = True
    
    # NOTA: Track no tiene campo release_date, solo guardamos en external_info
    # La fecha se mantiene en la información externa para mostrar en frontend
    
    if updated:
        track.save()
        print(f"🔄 Track actualizado: {track.title}")
    
    return track


def serialize_track_with_enrichment(track, external_info):
    """
    Serializar track combinando información de BD con información externa
    """
    track_data = {
        'id': track.id,
        'title': track.title,
        'artist': track.artist.name,
        'album': external_info.get('album'),  # Preferir info externa para álbum
        'duration': track.duration or external_info.get('duration'),
        'bpm': track.bpm,
        'genre': track.genre.name if track.genre else None,
        'mood': track.mood.name if track.mood else None,
        'release_date': external_info.get('release_date'),  # Solo de info externa
        
        # Información externa enriquecida
        'spotify_id': external_info.get('spotify', {}).get('id'),
        'spotify_preview': external_info.get('spotify', {}).get('preview_url'),
        'apple_music_url': external_info.get('apple_music', {}).get('url'),
        'apple_music_artwork': external_info.get('apple_music', {}).get('artwork'),
        'external_genres': external_info.get('apple_music', {}).get('genres', []),
        
        # Metadatos de tu BD
        'fingerprint_status': track.fingerprint_status,
        'fingerprints_count': track.fingerprints_count,
        'uploaded_at': track.uploaded_at.isoformat() if track.uploaded_at else None,
    }
    
    return track_data


def get_enrichment_summary(track, external_info):
    """
    Resumen de qué información se agregó/actualizó
    """
    enrichments = []
    
    if external_info.get('album'):
        enrichments.append('Álbum identificado')
    
    if external_info.get('spotify', {}).get('id'):
        enrichments.append('Spotify ID agregado')
    
    if external_info.get('apple_music', {}).get('url'):
        enrichments.append('Apple Music URL agregada')
    
    if external_info.get('release_date'):
        enrichments.append('Fecha de lanzamiento identificada')
    
    if external_info.get('apple_music', {}).get('genres'):
        enrichments.append(f"Géneros detectados: {', '.join(external_info['apple_music']['genres'])}")
    
    return enrichments


def get_auto_assignments(track, external_info):
    """
    Resumen de asignaciones automáticas hechas al crear el track
    """
    assignments = []
    
    if track and track.genre:
        assignments.append(f'Género asignado: {track.genre.name}')
    
    if track and track.duration:
        assignments.append(f'Duración: {track.duration}s')
    
    # La fecha de lanzamiento viene de external_info, no del modelo Track
    if external_info.get('release_date'):
        assignments.append(f'Fecha de lanzamiento: {external_info["release_date"]}')
    
    return assignments

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def easy_recognition(request):
    """
    Endpoint simple para reconocimiento de música (compatibilidad)
    Redirige al smart_recognition con configuración por defecto
    """
    # Configurar parámetros por defecto para mantener simplicidad
    request.data['auto_create'] = 'true'
    request.data['update_existing'] = 'true'
    
    # Usar smart_recognition internamente
    return smart_recognition(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_audd_recognition(request):
    """
    Endpoint para probar AudD (GRATUITO)
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = request.FILES['file']
    
    try:
        from django.core.files.storage import default_storage
        from .audd_service import get_audd_service
        
        # Guardar archivo temporalmente
        temp_filename = f"audd_test_{file_obj.name}"
        file_path = default_storage.save(temp_filename, file_obj)
        full_path = default_storage.path(file_path)
        
        # Reconocer con AudD
        service = get_audd_service()
        result = service.recognize_file(full_path)
        
        # Limpiar archivo temporal
        try:
            default_storage.delete(file_path)
        except:
            pass
        
        return Response({
            'service': 'AudD (Gratuito)',
            'file_name': file_obj.name,
            'result': result
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error testing AudD: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_acrcloud_recognition(request):
    """
    Endpoint para probar ACRCloud (COMERCIAL - Muy preciso)
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = request.FILES['file']
    
    try:
        from django.core.files.storage import default_storage
        from .acrcloud_service import get_acrcloud_service
        
        # Guardar archivo temporalmente
        temp_filename = f"acrcloud_test_{file_obj.name}"
        file_path = default_storage.save(temp_filename, file_obj)
        full_path = default_storage.path(file_path)
        
        # Reconocer con ACRCloud
        service = get_acrcloud_service()
        result = service.recognize_file(full_path)
        
        # Limpiar archivo temporal
        try:
            default_storage.delete(file_path)
        except:
            pass
        
        return Response({
            'service': 'ACRCloud (Comercial)',
            'file_name': file_obj.name,
            'result': result
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error testing ACRCloud: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recognition_services_status(request):
    """
    Verificar el estado de los servicios de reconocimiento
    """
    services_status = {}
    
    # Verificar AudD
    try:
        from .audd_service import get_audd_service
        audd_service = get_audd_service()
        services_status['audd'] = {
            'available': True,
            'name': 'AudD API',
            'type': 'Gratuito',
            'description': '25 reconocimientos/día gratis',
            'configured': True
        }
    except Exception as e:
        services_status['audd'] = {
            'available': False,
            'error': str(e)
        }
    
    # Verificar ACRCloud
    try:
        from .acrcloud_service import get_acrcloud_service
        acrcloud_service = get_acrcloud_service()
        services_status['acrcloud'] = {
            'available': True,
            'name': 'ACRCloud API',
            'type': 'Comercial',
            'description': 'Muy preciso, usado por Shazam',
            'configured': True
        }
    except Exception as e:
        services_status['acrcloud'] = {
            'available': False,
            'error': str(e),
            'setup_required': 'Necesitas configurar ACRCLOUD_ACCESS_KEY y ACRCLOUD_ACCESS_SECRET'
        }
    
    return Response({
        'services': services_status,
        'recommendation': 'AudD para empezar (gratuito), ACRCloud para máxima precisión'
    })

@api_view(['GET'])
@permission_classes([AllowAny])  # Sin autenticación para prueba rápida
def demo_recognition_flow(request):
    """
    Demostración del flujo completo de reconocimiento
    Simula como funciona el sistema con ejemplos reales
    """
    try:
        from .audd_service import get_audd_service
        
        # Verificar que AudD esté disponible
        service = get_audd_service()
        
        demo_response = {
            'status': 'Sistema funcionando correctamente',
            'flow_description': 'Así funciona cuando subes un archivo:',
            'steps': [
                '1. Usuario sube archivo MP3/WAV',
                '2. AudD identifica la canción en ~2-3 segundos',
                '3. Sistema busca en tu BD si ya existe',
                '4. Si existe: enriquece con nueva info',
                '5. Si no existe: crea nuevo track completo',
                '6. Retorna toda la información combinada'
            ],
            'example_scenarios': {
                'scenario_1_existing_track': {
                    'description': 'Track ya existe en tu BD',
                    'user_action': 'Sube "Bohemian Rhapsody.mp3"',
                    'audd_identifies': {
                        'title': 'Bohemian Rhapsody',
                        'artist': 'Queen',
                        'album': 'A Night at the Opera',
                        'spotify_id': '4u7EnebtmKWzUH433cf5Qv',
                        'release_date': '1975-10-31'
                    },
                    'your_db_has': {
                        'id': 123,
                        'title': 'Bohemian Rhapsody',
                        'artist': 'Queen',
                        'genre': 'Rock',
                        'mood': 'Epic',
                        'fingerprint_status': 'completed'
                    },
                    'final_result': {
                        'recognized': True,
                        'track_exists_in_db': True,
                        'track_updated': True,
                        'track': {
                            'id': 123,
                            'title': 'Bohemian Rhapsody',
                            'artist': 'Queen',
                            'genre': 'Rock',  # ← TU info se mantiene
                            'mood': 'Epic',   # ← TU info se mantiene
                            'album': 'A Night at the Opera',  # ← NUEVO de AudD
                            'spotify_id': '4u7EnebtmKWzUH433cf5Qv',  # ← NUEVO
                            'release_date': '1975-10-31'  # ← NUEVO
                        },
                        'enrichment_applied': [
                            'Álbum agregado',
                            'Spotify ID agregado',
                            'Fecha de lanzamiento agregada'
                        ]
                    }
                },
                'scenario_2_new_track': {
                    'description': 'Track no existe en tu BD',
                    'user_action': 'Sube "Imagine.mp3"',
                    'audd_identifies': {
                        'title': 'Imagine',
                        'artist': 'John Lennon',
                        'album': 'Imagine',
                        'spotify_id': '7pKfPomDEeI4TPT6EOYjn9',
                        'genre': 'Rock'
                    },
                    'your_db_has': 'Nada - track no existe',
                    'final_result': {
                        'recognized': True,
                        'track_exists_in_db': False,
                        'track_created': True,
                        'track': {
                            'id': 456,  # ← NUEVO track creado
                            'title': 'Imagine',
                            'artist': 'John Lennon',
                            'album': 'Imagine',
                            'spotify_id': '7pKfPomDEeI4TPT6EOYjn9',
                            'genre': 'Rock',  # ← Auto-asignado
                            'is_reference_track': False,
                            'reference_source': 'audd_recognition'
                        },
                        'auto_assigned': [
                            'Artista creado: John Lennon',
                            'Género asignado: Rock',
                            'Track creado con toda la info externa'
                        ]
                    }
                }
            },
            'endpoints_to_test': [
                {
                    'endpoint': 'POST /api/easy-recognition/',
                    'description': 'Automático - sube archivo y listo',
                    'body': 'form-data: file (MP3/WAV)'
                },
                {
                    'endpoint': 'POST /api/smart-recognition/',
                    'description': 'Control total con opciones',
                    'body': 'form-data: file + auto_create=true + update_existing=true'
                }
            ],
            'audd_service_status': 'Disponible y configurado correctamente'
        }
        
        return Response(demo_response)
        
    except Exception as e:
        return Response({
            'error': f'Error en servicio: {str(e)}',
            'message': 'Revisa la configuración de AudD'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_real_recognition(request):
    """
    Prueba REAL del sistema de reconocimiento
    Sube un archivo y ve exactamente cómo funciona
    """
    if 'file' not in request.FILES:
        return Response({
            'error': 'No file provided',
            'instructions': 'Sube un archivo MP3 o WAV para probar',
            'example_curl': '''
curl -X POST http://localhost:8000/api/test-real-recognition/ \\
  -H "Authorization: Bearer tu_token" \\
  -F "file=@ruta/a/tu/cancion.mp3"
            '''
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = request.FILES['file']
    
    try:
        from django.core.files.storage import default_storage
        from .audd_service import get_audd_service
        import time
        
        start_time = time.time()
        
        response_data = {
            'test_info': {
                'file_name': file_obj.name,
                'file_size_mb': round(file_obj.size / (1024*1024), 2),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'steps_executed': []
        }
        
        # PASO 1: Guardar archivo
        response_data['steps_executed'].append('✅ Archivo recibido y guardado temporalmente')
        temp_filename = f"test_real_{file_obj.name}"
        file_path = default_storage.save(temp_filename, file_obj)
        full_path = default_storage.path(file_path)
        
        # PASO 2: Reconocer con AudD
        response_data['steps_executed'].append('🔍 Enviando a AudD para reconocimiento...')
        service = get_audd_service()
        recognition_result = service.recognize_file(full_path)
        
        recognition_time = time.time() - start_time
        response_data['recognition_time_seconds'] = round(recognition_time, 2)
        
        # Limpiar archivo temporal
        try:
            default_storage.delete(file_path)
            response_data['steps_executed'].append('🧹 Archivo temporal eliminado')
        except:
            pass
        
        if not recognition_result['success']:
            response_data['steps_executed'].append('❌ AudD no pudo procesar el archivo')
            response_data['audd_response'] = recognition_result
            return Response(response_data)
        
        if not recognition_result.get('recognized'):
            response_data['steps_executed'].append('❌ AudD no reconoció la canción')
            response_data['audd_response'] = recognition_result
            response_data['message'] = 'Canción no encontrada en la base de datos de AudD'
            return Response(response_data)
        
        # PASO 3: Información reconocida
        external_info = recognition_result['track_info']
        response_data['steps_executed'].append('✅ ¡Canción reconocida por AudD!')
        response_data['audd_identified'] = {
            'title': external_info['title'],
            'artist': external_info['artist'],
            'album': external_info.get('album'),
            'has_spotify': bool(external_info.get('spotify', {}).get('id')),
            'has_apple_music': bool(external_info.get('apple_music', {}).get('url')),
            'has_genres': bool(external_info.get('apple_music', {}).get('genres'))
        }
        
        # PASO 4: Buscar en tu BD
        response_data['steps_executed'].append('🔎 Buscando en tu base de datos...')
        possible_tracks = find_matching_tracks(
            title=external_info['title'],
            artist=external_info['artist'],
            user=request.user,
            spotify_id=external_info.get('spotify', {}).get('id')
        )
        
        response_data['database_search'] = {
            'matches_found': len(possible_tracks),
            'tracks_in_your_db': Track.objects.filter(artist__user=request.user).count()
        }
        
        if possible_tracks:
            # CASO 1: Track existe
            existing_track = possible_tracks[0]
            response_data['steps_executed'].append(f'✅ Track encontrado en tu BD (ID: {existing_track.id})')
            
            # Información antes del enriquecimiento
            before_enrichment = {
                'id': existing_track.id,
                'title': existing_track.title,
                'artist': existing_track.artist.name,
                'genre': existing_track.genre.name if existing_track.genre else None,
                'mood': existing_track.mood.name if existing_track.mood else None,
                'duration': existing_track.duration,
                'fingerprint_status': existing_track.fingerprint_status
            }
            
            # Enriquecer track
            updated_track = enrich_existing_track(existing_track, external_info)
            response_data['steps_executed'].append('✨ Track enriquecido con información externa')
            
            # Información después del enriquecimiento
            after_enrichment = serialize_track_with_enrichment(updated_track, external_info)
            
            response_data['final_result'] = {
                'action': 'track_enriched',
                'track_existed': True,
                'before_enrichment': before_enrichment,
                'after_enrichment': after_enrichment,
                'new_information_added': get_enrichment_summary(updated_track, external_info)
            }
            
        else:
            # CASO 2: Track no existe
            response_data['steps_executed'].append('ℹ️ Track no existe en tu BD, creando nuevo...')
            
            new_track = create_enriched_track(external_info, request.user)
            response_data['steps_executed'].append(f'✅ Nuevo track creado (ID: {new_track.id})')
            
            track_data = serialize_track_with_enrichment(new_track, external_info)
            
            response_data['final_result'] = {
                'action': 'track_created',
                'track_existed': False,
                'new_track': track_data,
                'auto_assignments': get_auto_assignments(new_track, external_info)
            }
        
        response_data['steps_executed'].append('🎉 ¡Proceso completado exitosamente!')
        response_data['total_time_seconds'] = round(time.time() - start_time, 2)
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'error': f'Error en prueba real: {str(e)}',
            'steps_executed': response_data.get('steps_executed', []),
            'debug_info': {
                'file_name': file_obj.name,
                'error_type': type(e).__name__
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def serialize_external_info_only(external_info):
    """
    Serializar solo la información externa de AudD sin track en BD
    """
    return {
        'title': external_info['title'],
        'artist': external_info['artist'],
        'album': external_info.get('album'),
        'duration': external_info.get('duration'),
        'release_date': external_info.get('release_date'),
        
        # Información externa enriquecida
        'spotify_id': external_info.get('spotify', {}).get('id'),
        'spotify_preview': external_info.get('spotify', {}).get('preview_url'),
        'apple_music_url': external_info.get('apple_music', {}).get('url'),
        'apple_music_artwork': external_info.get('apple_music', {}).get('artwork'),
        'external_genres': external_info.get('apple_music', {}).get('genres', []),
        
        # Indicar que no está en BD
        'in_database': False,
        'source': 'audd_only'
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_audd_quota(request):
    """
    Verificar el estado de la cuota de AudD
    """
    try:
        from .audd_service import get_audd_service
        import tempfile
        import os
        
        # Crear un archivo de audio muy pequeño para testing (silencio de 1 segundo)
        import numpy as np
        from scipy.io.wavfile import write
        
        # Generar 1 segundo de silencio
        sample_rate = 22050
        duration = 1  # segundo
        samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            write(tmp_file.name, sample_rate, samples)
            temp_path = tmp_file.name
        
        try:
            # Probar AudD con el archivo de silencio
            service = get_audd_service()
            result = service.recognize_file(temp_path)
            
            # Limpiar archivo temporal
            os.unlink(temp_path)
            
            if result.get('quota_exceeded'):
                return Response({
                    'quota_status': 'exceeded',
                    'message': 'Cuota diaria de AudD agotada (25 reconocimientos)',
                    'recommendation': 'Espera hasta mañana o considera AudD premium',
                    'error': result.get('error'),
                    'raw_response': result.get('raw_response')
                })
            elif result.get('success') == False and 'error' in result:
                return Response({
                    'quota_status': 'error',
                    'message': 'Error conectando con AudD',
                    'error': result.get('error'),
                    'raw_response': result.get('raw_response')
                })
            else:
                return Response({
                    'quota_status': 'active',
                    'message': 'AudD funcionando correctamente',
                    'recognized': result.get('recognized', False),
                    'remaining_quota': 'Cuota disponible (no se puede determinar el número exacto)'
                })
                
        except Exception as e:
            # Limpiar archivo temporal en caso de error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e
            
    except Exception as e:
        return Response({
            'quota_status': 'unknown',
            'error': f'Error verificando estado: {str(e)}',
            'message': 'No se pudo verificar el estado de AudD'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)