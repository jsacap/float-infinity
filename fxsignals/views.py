from django.shortcuts import render


def home(request):
    context = {
        'name': 'Jun'
    }

    return render(request, 'dashboard.html', context)
