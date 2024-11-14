myproject/
├── business_app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └──migrations
│   │     └── __init__.py
│   │          
│   └── static
│   │   └── business_app
│   │       ├── css
│   │       │    └──style.css      
│   │       ├── images
│   │       │   └──logo_green.png       
│   │       └──js
│   └─ templates
│       ├── account  
│       │   ├── login.html
│       │   └── signup.html
│       │
│       └──business_app
│       │   ├── main_page.html
│       │   ├── page_errors.html
│       │   ├── profile.html
│       │   ├── update_profile.html
│       │   │
│       │   ├── sale.html
│       │   ├── order_form.html
│       │   │
│       │   ├── purchase.html
│       │   ├── product_detail.html
│       │   ├── product_list.html
│       │   ├── update_product.html
│       │   │
│       │   └── review.html
│       └── base.html 
│
├── myproject
│     ├── __init__.py   
│     ├── asgi.py
│     ├── settings.py
│     ├── urls.py
│     └── wsgi.py
├── media/
├── db.sqlite3
├── manage.py       
└── structure.txt 

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