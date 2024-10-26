from django.urls import path
from . import views

# Укажите путь к вашей функции custom_404
handler404 = 'business_app.views.custom_404'

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('authorization/', views.AuthorizationView.as_view(), name='authorization'),
    path('purchase/', views.purchase, name='purchase'),
    path('sale/', views.sale, name='sale'),
    path('profile/', views.profile, name='profile'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('logout/', views.logout_view, name='logout'),
    path('404/', views.custom_404, name='custom_404'),
    path("update_product/", views.update_product, name="update_product"),
    # path('accounts/', include('allauth.urls'),
    # Добавьте другие URL-маршруты, необходимые для вашего приложения
]
