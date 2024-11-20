def user_group_context(request):
    if request.user.is_authenticated:
        group_names = request.user.groups.values_list('name', flat=True)
        return {
            'is_customer': 'customer' in group_names or request.user.is_superuser,
            'is_salesman': 'salesman' in group_names or request.user.is_superuser,
        }
    return {
        'is_customer': False,
        'is_salesman': False,
    }