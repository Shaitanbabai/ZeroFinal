"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
# from django.conf.urls import handler404
# from django.conf.urls import handler500
from django.shortcuts import render
from business_app.views import handle_permission_denied_or_not_found


# Регистрация обработчиков ошибок
handler403 = handle_permission_denied_or_not_found
handler404 = handle_permission_denied_or_not_found

urlpatterns = ([
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('business_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# # Обработчик ошибки 404
# def custom_page_not_found_view(request, exception):
#     return render(request, 'page_errors.html', status=404)
#
# # Связываем обработчик с кодом ошибки 404
# handler404 = custom_page_not_found_view
#
# # Обработчик ошибки 500
# def custom_page_restricted_view(request):
#     return render(request, 'page_errors.html', status=500)
#
# # Связываем обработчик с кодом ошибки 500
# handler500 = custom_page_restricted_view