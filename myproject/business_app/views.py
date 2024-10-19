from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required


def main_page(request):
    return render(request, 'business_app/main_page.html')


def authorization(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect_user_based_on_group(user)
        else:
            # Обработка ошибки аутентификации (например, неверный логин или пароль)
            context = {'error': 'Invalid email or password'}
            return render(request, 'business_app/authorization.html', context)
    return render(request, 'business_app/authorization.html')


@login_required
def purchase(request):
    if request.user.groups.filter(name='customer').exists():
        context = {'is_customer': True}
        return render(request, 'business_app/purchase.html', context)
    elif request.user.groups.filter(name='salesman').exists():
        return redirect('sale')
    else:
        return redirect('main_page')


@login_required
def sale(request):
    if request.user.groups.filter(name='salesman').exists():
        context = {'is_salesman': True}
        return render(request, 'business_app/sale.html', context)
    elif request.user.groups.filter(name='customer').exists():
        return redirect('purchase')
    else:
        return redirect('main_page')


@login_required
def profile(request):
    return render(request, 'business_app/profile.html')


def registration(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer_group = Group.objects.get(name='customer')
            user.groups.add(customer_group)
            login(request, user)
            return redirect('purchase')
    else:
        form = UserCreationForm()
    return render(request, 'business_app/registration.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('main_page')

def redirect_user_based_on_group(user):
    """Redirect user based on their group."""
    if user.groups.filter(name='customer').exists():
        return redirect('purchase')
    elif user.groups.filter(name='salesman').exists():
        return redirect('sale')
    else:
        return redirect('profile')
