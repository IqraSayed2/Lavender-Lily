from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from store import views as store_views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    path('signin/', views.signin_page, name='signin'),
    path('signup/', views.signup_page, name='signup'),
    path('logout/', views.logout_user, name='logout'),

    path('profile/', views.profile, name='profile'),
    path('profile/remove-address/<int:address_id>/', views.remove_address, name='remove_address'),

    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset_combined.html',
        extra_context={'step': 'email'}
    ), name='password_reset'),

    path('password-reset-sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_combined.html',
        extra_context={'step': 'sent'}
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_combined.html',
        extra_context={'step': 'new_password'}
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_combined.html',
        extra_context={'step': 'complete'}
    ), name='password_reset_complete'),

    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Management URLs under dashboard
    path('dashboard/manage/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/manage/orders/<int:pk>/status/', views.update_order_status, name='update_order_status'),
    path('dashboard/manage/users/', views.manage_users, name='manage_users'),
    path('dashboard/manage/users/<int:pk>/status/', views.update_user_status, name='update_user_status'),
    path('dashboard/manage/messages/', views.manage_messages, name='manage_messages'),
    path('dashboard/manage/messages/<int:pk>/view/', views.message_detail, name='message_detail'),
    path('dashboard/manage/messages/<int:pk>/reply/', views.reply_to_message, name='reply_to_message'),
    path('dashboard/manage/messages/<int:pk>/delete/', views.delete_message, name='delete_message'),
    path('dashboard/manage/homepage/', views.manage_homepage, name='manage_homepage'),
    path('dashboard/manage/contact-page/', views.manage_contact_page, name='manage_contact_page'),
    path('dashboard/manage/about-page/', views.manage_about_page, name='manage_about_page'),
    path('dashboard/manage/newsletters/', views.manage_newsletters, name='manage_newsletters'),
    path('dashboard/manage/newsletters/<int:pk>/content/', views.newsletter_content, name='newsletter_content'),
    path('dashboard/manage/subscribers/', views.manage_subscribers, name='manage_subscribers'),
    path('dashboard/manage/subscribers/<int:pk>/toggle/', views.toggle_subscriber_status, name='toggle_subscriber_status'),

    # Store management URLs under dashboard
    path('dashboard/manage/products/', store_views.manage_products, name='manage_products'),
    path('dashboard/manage/products/add/', store_views.add_product, name='add_product'),
    path('dashboard/manage/products/<int:pk>/edit/', store_views.edit_product, name='edit_product'),
    path('dashboard/manage/products/<int:pk>/delete/', store_views.delete_product, name='delete_product'),
    path('dashboard/manage/categories/', store_views.manage_categories, name='manage_categories'),
    path('dashboard/manage/colors/', store_views.manage_colors, name='manage_colors'),
]
