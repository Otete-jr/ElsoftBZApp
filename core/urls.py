"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import get_user_model # Tumia hii badala ya User ya kawaida
from django.http import HttpResponse

# Hii itapata User Model yako sahihi (store.User) automatically
User = get_user_model()

def create_admin(request):
    try:
        if not User.objects.filter(username="admin").exists():
            # Tunatengeneza admin hapa
            User.objects.create_superuser("admin", "admin@elsoft.com", "elsoft123")
            return HttpResponse("Admin ametengenezwa kikamilifu!")
        else:
            return HttpResponse("Admin tayari yupo kwenye mfumo.")
    except Exception as e:
        return HttpResponse(f"Kuna hitilafu: {str(e)}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/store/', include('store.urls')),
    path('setup-admin/', create_admin),
]