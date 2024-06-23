from django.urls import path
from . import views

urlpatterns = [
    path('', views.examples, name='examples'),
    path('add/', views.add_example, name='add_example'),
    path('edit/<int:pk>/', views.edit_example, name='edit_example'),
    path('delete/<int:pk>/', views.delete_example, name='delete_example'),
]
