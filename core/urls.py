from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # File actions
    path('upload/', views.upload_file_view, name='upload_file'),
    path('download/<int:file_id>/', views.download_file_view, name='download_file'),
    path('share/<int:file_id>/', views.share_file_view, name='share_file'),
    path('delete/<int:file_id>/', views.delete_file_view, name='delete_file'),
]