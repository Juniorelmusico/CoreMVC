from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import MusicFileViewSet, RecognitionListView, RecognitionDetailView, recognition_status, test_auth, test_no_auth

# Configuración del router para las vistas basadas en ViewSets
router = DefaultRouter()
router.register(r'artists', views.ArtistViewSet, basename='artist')
router.register(r'genres', views.GenreViewSet, basename='genre')
router.register(r'moods', views.MoodViewSet, basename='mood')
router.register(r'tracks', views.TrackViewSet, basename='track')
router.register(r'analyses', views.AnalysisViewSet, basename='analysis')
router.register(r'music', MusicFileViewSet, basename='music')

# Router para endpoints de administración
admin_router = DefaultRouter()
admin_router.register(r'artists', views.AdminArtistViewSet, basename='admin-artist')
admin_router.register(r'genres', views.AdminGenreViewSet, basename='admin-genre')
admin_router.register(r'moods', views.AdminMoodViewSet, basename='admin-mood')
admin_router.register(r'tracks', views.AdminTrackViewSet, basename='admin-track')
admin_router.register(r'analyses', views.AdminAnalysisViewSet, basename='admin-analysis')

urlpatterns = [
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="delete-note"),
    
    # Endpoints de archivos y reconocimiento
    path("upload/", views.FileUploadView.as_view(), name="file-upload"),
    path("files/", views.FileListView.as_view(), name="file-list"),
    path("recognitions/", RecognitionListView.as_view(), name="recognition-list"),
    path("recognitions/<int:pk>/", RecognitionDetailView.as_view(), name="recognition-detail"),
    path("recognition-status/<int:file_id>/", recognition_status, name="recognition-status"),
    
    # Endpoints de prueba
    path("test-auth/", test_auth, name="test-auth"),
    path("test-no-auth/", test_no_auth, name="test-no-auth"),
    
    # URLs para administradores
    path("admin/dashboard/", views.admin_dashboard, name="admin-dashboard"),
    path("admin/model-stats/", views.admin_model_stats, name="admin-model-stats"),
    path("admin/users/", views.AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/files/", views.AdminFileListView.as_view(), name="admin-files"),
    path("admin/files/<int:pk>/", views.AdminFileDeleteView.as_view(), name="admin-file-delete"),
    
    # Incluir router de administración
    path("admin/crud/", include(admin_router.urls)),
    
    # API principal
    path("", include(router.urls)),  # Incluye las rutas generadas por el router
]