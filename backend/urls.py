from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from api.tokens import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', lambda request: HttpResponse("Bienvenido a la API!")),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="get_token"),
]