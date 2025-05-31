from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import api_view, parser_classes, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .serializers import UserSerializer, NoteSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import Note, Artist, Genre, Mood, Track, Analysis, UploadedFile, MusicFile
from .serializers import ArtistSerializer, GenreSerializer, MoodSerializer, TrackSerializer, AnalysisSerializer, UploadedFileSerializer, TrackUploadSerializer, MusicFileSerializer
from .tasks import analyze_track
from django.core.files.storage import default_storage
from .services import analyze_music_file
import os
from rest_framework.generics import RetrieveAPIView


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
        return Track.objects.filter(artist__user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
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
                analysis_status='pending'
            )
            
            # Start analysis task
            analyze_track.delay(track.id)
            
            return Response(
                TrackSerializer(track).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        track = self.get_object()
        if track.analysis:
            return Response(AnalysisSerializer(track.analysis).data)
        return Response(
            {'status': track.analysis_status, 'error': track.analysis_error},
            status=status.HTTP_200_OK
        )


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
            serializer.save(uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FileListView(generics.ListAPIView):
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Obtener solo los archivos subidos por el usuario actual
        return UploadedFile.objects.filter(uploaded_by=self.request.user).order_by('-uploaded_at')


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
        return super().create(request, *args, **kwargs)


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


class TrackAnalysisView(RetrieveAPIView):
    serializer_class = AnalysisSerializer

    def get_object(self):
        track_id = self.kwargs['pk']
        return Analysis.objects.get(track__id=track_id)


class MusicFileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MusicFileSerializer
    
    def get_queryset(self):
        return MusicFile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Save the file first
        music_file = serializer.save(user=self.request.user)
        
        try:
            # Get the file path
            file_path = music_file.file.path
            
            # Analyze the music file
            metadata = analyze_music_file(file_path)
            
            # Update the model with the metadata
            music_file.duration = metadata['duration']
            music_file.tempo = metadata['tempo']
            music_file.key = metadata['key']
            music_file.loudness = metadata['loudness']
            music_file.save()
            
        except Exception as e:
            # If analysis fails, delete the file and raise the error
            music_file.delete()
            raise Exception(f"Error processing music file: {str(e)}")
    
    @action(detail=True, methods=['get'])
    def analyze(self, request, pk=None):
        music_file = self.get_object()
        
        try:
            metadata = analyze_music_file(music_file.file.path)
            
            # Update the model with new analysis
            music_file.duration = metadata['duration']
            music_file.tempo = metadata['tempo']
            music_file.key = metadata['key']
            music_file.loudness = metadata['loudness']
            music_file.save()
            
            return Response(self.get_serializer(music_file).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )