from django.urls import path
from . import views

urlpatterns = [
    path("", views.shop, name="shop"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("wishlist/toggle/<int:pk>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("size-chart/", views.size_chart, name="size_chart"),
]
