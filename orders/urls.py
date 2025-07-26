from django.urls import path
from . import views

app_name = "orders"
urlpatterns = [
    path("shipping/", views.shipping, name="shipping"),
    path("orderconfirm/", views.orderconfirm, name="orderconfirm"),
    path("cancel/", views.cancel_order, name="cancel_order"),
    path("cancel/<int:order_id>/", views.cancel_order_by_id, name="cancel_order_by_id"),
    path("detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("list/", views.order_list, name="order_list"),
    path("apply-coupon/<int:order_id>/", views.apply_coupon, name="apply_coupon"),
    path("remove-coupon/<int:order_id>/", views.remove_coupon, name="remove_coupon"),
]
