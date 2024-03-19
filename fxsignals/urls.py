from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home),
    path('api/fetch-fx-data/', views.get_fx_data_view, name='get_fx_data'),
]
