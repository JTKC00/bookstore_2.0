from django.urls import path
from . import views

app_name = "orders"
urlpatterns = [
    path("shipping/", views.shipping, name="shipping"),
    path("orderconfirm/", views.orderconfirm, name="orderconfirm"),
    path("detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("list/", views.order_list, name="order_list"),
]
