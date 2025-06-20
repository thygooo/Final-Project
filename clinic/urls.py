from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('inventory/', views.inventory, name='inventory'),
    path('category/<int:category_id>/', views.category_medicines, name='category_medicines'),
    path('medicine/add/', views.add_medicine, name='add_medicine'),
    path('medicine/edit/<int:medicine_id>/', views.edit_medicine, name='edit_medicine'),
    path('medicine/delete/<int:medicine_id>/', views.delete_medicine, name='delete_medicine'),
    path('request/', views.request_medicine, name='request_medicine'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('manage-requests/', views.manage_requests, name='manage_requests'),
    path('process-request/<int:request_id>/', views.process_request, name='process_request'),
    path('category/add/', views.add_category, name='add_category'),
    path('alerts/', views.alerts, name='alerts'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
]