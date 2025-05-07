from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuración del router para las vistas basadas en ViewSets
router = DefaultRouter()
router.register(r'artists', views.ArtistViewSet, basename='artist')
router.register(r'genres', views.GenreViewSet, basename='genre')
router.register(r'moods', views.MoodViewSet, basename='mood')
router.register(r'tracks', views.TrackViewSet, basename='track')
router.register(r'analyses', views.AnalysisViewSet, basename='analysis')

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
    path("upload/", views.FileUploadView.as_view(), name="file-upload"),
    path("files/", views.FileListView.as_view(), name="file-list"),
    
    # URLs para administradores
    path("admin/dashboard/", views.admin_dashboard, name="admin-dashboard"),
    path("admin/model-stats/", views.admin_model_stats, name="admin-model-stats"),
    path("admin/users/", views.AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/files/", views.AdminFileListView.as_view(), name="admin-files"),
    path("admin/files/<int:pk>/", views.AdminFileDeleteView.as_view(), name="admin-file-delete"),
    
    # Incluir router de administración
    path("admin/crud/", include(admin_router.urls)),
    
    path("api/", include(router.urls)),  # Incluye las rutas generadas por el router
]