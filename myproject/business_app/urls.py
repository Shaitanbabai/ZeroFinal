from django.urls import path
from . import views

# Регистрация обработчиков ошибок
handler403 = 'business_app.views.handle_permission_denied_or_not_found'
handler404 = 'business_app.views.handle_permission_denied_or_not_found'

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('authorization/', views.AuthorizationView.as_view(), name='authorization'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile, name='profile'),
    path("update_profile/", views.update_profile, name="update_profile"),

    path('purchase/', views.purchase, name='purchase'),
    path('sale/', views.sale, name='sale'),
    # path("product/", views.product, name="product"),

    path("update_product/", views.update_product, name="update_product"),
    # path("delete_product/", views.delete_product, name="delete_product"),

    path("page_errors/", views.handle_permission_denied_or_not_found, name="page_errors"),

    # Добавьте другие URL-маршруты, необходимые для вашего приложения
]


# path('accounts/', include('allauth.urls'), name='accounts'),