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
            # fingerprint_track.delay(track.id)  # Comentado temporalmente - requiere Celery/Redis
            
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
        
        # Si el track tiene análisis, devolverlo
        if hasattr(track, 'analysis'):
            return Response(AnalysisSerializer(track.analysis).data)
        
        # Si no hay análisis, devolver información básica del track
        return Response({
            'track_id': track.id,
            'track_title': track.title,
            'artist_name': track.artist.name if track.artist else 'Unknown Artist',
            'fingerprint_status': track.fingerprint_status,
            'fingerprint_error': track.fingerprint_error,
            'fingerprints_count': track.fingerprints_count,
            'message': 'No detailed analysis available yet'
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
    Vista para subir archivos de audio para reconocimiento (tipo Shazam)
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
                    processing_status='pending'
                )
                
                # Para debugging: no usar Celery por ahora
                # recognize_audio_file.delay(uploaded_file.id)
                
                # En su lugar, cambiar el estado a procesando sin ejecutar la tarea
                uploaded_file.processing_status = 'processing'
                uploaded_file.save()
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        
        response_data = {
            'status': recognition.recognition_status,
            'processing_time': recognition.processing_time,
            'confidence': recognition.confidence,
            'recognition_id': recognition.id
        }
        
        if recognition.recognized_track:
            response_data['track'] = {
                'id': recognition.recognized_track.id,
                'title': recognition.recognized_track.title,
                'artist': recognition.recognized_track.artist.name,
                'genre': recognition.recognized_track.genre.name if recognition.recognized_track.genre else None,
                'mood': recognition.recognized_track.mood.name if recognition.recognized_track.mood else None,
            }
        
        if recognition.recognition_error:
            response_data['error'] = recognition.recognition_error
        
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