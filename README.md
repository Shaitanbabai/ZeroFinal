business_app/
    ├── migrations/
    ├── static/
    │   └── business_app/
    │       ├── css/
    │       ├── js/
    │       └── images/
    ├── templates/
    │   └── business_app/
    │       ├── base.html
    │       ├── product_list.html
    │       └── checkout.html
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    └── views.py

Добавлю контекст. Общая функциональность сайта будет такова:

1. Не авторизованный пользователь будет видеть главную страницу. Ему на ней будет доступна кнопка регистрации/авторизации с переходом на соответствующие страницы административной панели.

2. Авторизованный пользователь в роли user  переходит на соответствующий его роли шаблон страницы.
На соответствующей его роли странице он видит кнопки:
- Profile (переход в профиль пользователя в административной панели)
- Orders (переход на страницу заказа после выбора товара)
- Logout (принудительное окончание сессии и выход на главную страницу)

3. Авторизованный пользователь в роли manager переходит на соответствующий его роли шаблон страницы.
 Manager, видит те же кнопки, что и user, а кроме того видит кнопку:
- Sales (переход на страницу  с анализом продаж)

4. Пользователю с ролью superuser доступно только определение роли пользователей и управление сайтом. Он не имеет доступа к функциональности страниц Orders и Sales.