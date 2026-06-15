"""
URL configuration for config project.

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
from django.urls import path
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from view.auth import AuthView, home_view
from view.crud import get_crud_urls
from view.api_views import validate_document_view, empresa_details_view, empresa_allowed_documents_view, empresa_painel_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', AuthView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('api/validate/', validate_document_view, name='api_validate'),
    path('api/empresa/<int:pk>/detalhes/', empresa_details_view, name='api_empresa_detalhes'),
    path('api/empresa/<int:pk>/documentos-permitidos/', empresa_allowed_documents_view, name='api_empresa_documentos_permitidos'),
    path('empresa/<int:pk>/painel/', empresa_painel_view, name='empresa_painel'),
    path('', home_view, name='home'),
] + get_crud_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
