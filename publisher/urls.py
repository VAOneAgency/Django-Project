from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/create/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),

    # Roles
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:pk>/delete/', views.role_delete, name='role_delete'),

    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),

    # Organizations
    path('organizations/', views.org_list, name='org_list'),
    path('organizations/create/', views.org_create, name='org_create'),
    path('organizations/<int:pk>/edit/', views.org_edit, name='org_edit'),
    path('organizations/<int:pk>/delete/', views.org_delete, name='org_delete'),

    # Social Accounts
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/connect/', views.account_connect_choose, name='account_connect_choose'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),

    # Posts
    path('posts/', views.post_list, name='post_list'),
    path('posts/create/', views.post_create, name='post_create'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('posts/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('posts/<int:pk>/delete/', views.post_delete, name='post_delete'),

    # Account test connection
    path('accounts/<int:pk>/test/', views.account_test, name='account_test'),

    # Publish now
    path('posts/<int:pk>/publish/', views.post_publish_now, name='post_publish_now'),

    # Post Platforms (edit/delete only — create handled inline from post form)
    path('post-platforms/<int:pk>/edit/', views.post_platform_edit, name='post_platform_edit'),
    path('post-platforms/<int:pk>/delete/', views.post_platform_delete, name='post_platform_delete'),

    # Post Images (edit/delete only — create handled inline from post form)
    path('post-images/<int:pk>/delete/', views.post_image_delete, name='post_image_delete'),

    # Post Analytics
    path('posts/<int:pk>/analytics/', views.post_analytics, name='post_analytics'),

    # Meta Webhooks (Instagram / Facebook)
    # GET  = verification handshake from Meta
    # POST = incoming event notifications
    path('webhooks/meta/', views.webhook_meta, name='webhook_meta'),
    path('webhooks/events/', views.webhook_events, name='webhook_events'),
]
# ← append to existing urlpatterns in urls.py
