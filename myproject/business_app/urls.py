from django.urls import path
from . import views


urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('authorization/', views.authorization, name='authorization'),
    path('purchase/', views.purchase, name='purchase'),
    path('sale/', views.sale, name='sale'),
    path('profile/', views.profile, name='profile'),
    path('registration/', views.registration, name='registration'),
    path('logout/', views.logout_view, name='logout'),
    # Добавьте другие URL-маршруты, необходимые для вашего приложения
]
