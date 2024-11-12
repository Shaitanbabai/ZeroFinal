from django.urls import path
# from .views import handle_permission_denied_or_not_found
from . import views


urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('authorization/', views.AuthorizationView.as_view(), name='authorization'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile, name='profile'),
    path("update_profile/", views.update_profile, name="update_profile"),

    path('purchase/', views.purchase, name='purchase'),  # Страница "Мои покупки", интерфейс покупателя
    path('order_form/', views.order_form, name='order_form'),  # Форма заказа и корзина
    path('add_product_to_order/<int:product_id>/', views.add_product_to_order, name='add_product_to_order'),  # Маршрут для добавления продукта в заказ
    path('update_cart/', views.update_cart, name='update_cart'),  # Маршрут для обновления корзины

    path('sale/', views.sale, name='sale'),  # Страница "Мои продажи", интерфейс продавца
    path('products/', views.product_list, name='product_list'),  # Маршрут к шаблону продукта
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Маршрут для просмотра выбранного продукта
    path('create/', views.create_product, name='create_product'),  # Маршрут для создания продукта
    path('product/<int:product_id>/update/', views.update_product, name='update_product'),  # Маршрут для обновления продукта
    path('product/<int:product_id>/toggle_status/', views.toggle_product_status, name='toggle_product_status'),  # Маршрут для переключения статуса продукта

    path("page_errors/", views.handle_permission_denied_or_not_found, name="page_errors"),

    path('review/', views.sale, name='review'),

    # Добавьте другие URL-маршруты, необходимые для вашего приложения
]

