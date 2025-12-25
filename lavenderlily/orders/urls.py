from django.urls import path
from . import views

urlpatterns = [
    path("payment-status/<str:status>/", views.payment_status, name="payment_status"),
    path("payment-callback/", views.payment_callback, name="payment_callback"),
    path("create-ziina-payment/", views.create_ziina_payment, name="create_ziina_payment"),
    path("ziina-webhook/", views.ziina_webhook, name="ziina_webhook"),
    path("order/<int:pk>/", views.order_detail, name="order_detail"),
    path("order/<int:pk>/cancel/", views.cancel_order, name="cancel_order"),
    path("order/<int:pk>/return/", views.return_order, name="return_order"),
]
