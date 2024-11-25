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

    path('purchase/', views.purchase, name='purchase'),  # Страница "Мои покупки", отображает заказы пользователя,
    # разделяя их по статусам (ожидающие, подтверждённые, доставленные, отменённые и завершённые).
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Маршрут для добавления продукта в корзину
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),  # Маршрут для удаления продукта из корзины
    path('clear_cart/', views.clear_cart, name='clear_cart'),  # Маршрут для очистки корзины
    path('cart_detail/', views.cart_detail, name='cart_detail'),  # Маршрут к шаблону корзины
    path('create_order/', views.create_order, name='create_order'),  # Маршрут Создаёт новый заказ на основе содержимого корзины и очищает
    # корзину после подтверждения заказа.
    # path('order/create/', views.create_order, name='create_order'),
    path('edit_order/<int:order_id>/', views.edit_order, name='edit_order'),  # Маршрут для создания временного заказа
    # для редактирования существующего заказа пользователем
    path('edit_order_detail/<int:order_id>/', views.edit_order_detail, name='edit_order_detail'),  # Маршрут отображает страницу
    # редактирования временного заказа и предоставляет возможность подтвердить или отменить изменения.
    path('confirm_order_changes/<int:order_id>/', views.confirm_order_changes, name='confirm_order_changes'),  # Маршрут Подтверждает изменения
    # временного заказа, обновляет оригинальный заказ и удаляет временный заказ.
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),  # Маршрут отменяет заказ, если он был подтверждён

    path('sale/', views.sale, name='sale'),  # Страница "Мои продажи", интерфейс продавца
    path('manage_orders/<int:order_id>/<str:action>/', views.manage_orders, name='manage_orders'),  # Маршрут для управления заказами
    path('products/', views.product_list, name='product_list'),  # Маршрут к шаблону продукта
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # Маршрут для просмотра выбранного продукта
    path('create/', views.create_product, name='create_product'),  # Маршрут для создания продукта
    path('product/<int:product_id>/update/', views.update_product, name='update_product'),  # Маршрут для обновления продукта
    path('product/<int:product_id>/toggle_status/', views.toggle_product_status, name='toggle_product_status'),  # Маршрут для переключения статуса продукта

    path("page_errors/", views.handle_permission_denied_or_not_found, name="page_errors"),  # Маршрут для обработки ошибок

    path('review', views.review, name='review'),  # Маршрут для страницы отзывов
    path('review/<int:order_id>/', views.review, name='review'),  # Маршрут для отзыва
    path('reply/<int:order_id>/', views.reply_to_review, name='add_reply'),  # Маршрут для ответа на отзыв
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),  # Маршрут для удаления отзыва
    path('review/all/', views.all_reviews, name='all_reviews'),  # Маршрут для отображения всех отзывов

    # Добавьте другие URL-маршруты, необходимые для вашего приложения
]

