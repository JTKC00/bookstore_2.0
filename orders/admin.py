from django.contrib import admin
from orders.models import Order, OrderItem
from django.forms import NumberInput  
from django.db import models  


## define a class
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "userId",
        "shopCartId",
        "invoice_no",
        "order_date",
        "receipient",
        "receipient_phone",
        "shipping_address",
        "payment_status",
        "shipping_status",
        "total_amount",
    )  # Fields to display in the admin list view

    list_display_links = ("id",)  # Fields that are clickable links
    list_filter = ("userId",)  # Filters to apply in the admin interface
    list_editable = (
        "payment_status",
        "shipping_status",
    )  # Fields that can be edited directly in the list view
    search_fields = (
        "userId",
        "ShopCartId",
        "invoice_no",
    )  # Fields to search in the admin interface
    list_per_page = 25  # Number of listings to display per page in the admin interface
    ordering = ["-id"]  # Default ordering of listings by list date in descending order
    ##   title = 'Listings Admin'  # Title for the admin interface
    ##    Example of how to use the slug field
    ##    prepopulated_fields = {'title': ('title',)}  # Automatically populate the slug field based on the title
    ## do not use the slug to insert spaces amid the argument as an endpoint of the URL

    formfield_overrides = {
        models.IntegerField: {"widget": NumberInput(attrs={"size": "10"})}
    }  # Use a number input for DecimalFields
    show_facets = admin.ShowFacets.ALWAYS


# Register the Listing model with the admin site using the ListingAdmin class
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bookid",
        "bookid__title",
        "orderid",
        "unit_price",
        "quantity",
        "subTotal",
        "CartID",
    )  # Fields to display in the admin list view

    list_display_links = ("id",)  # Fields that are clickable links
    list_filter = ()  # Filters to apply in the admin interface
    list_editable = ()  # Fields that can be edited directly in the list view
    search_fields = (
        "orderid",
        "orderid__invoice_no",
    )  # Fields to search in the admin interface
    list_per_page = 25  # Number of listings to display per page in the admin interface
    ordering = ["-id"]  # Default ordering of listings by list date in descending order
    ##   title = 'Listings Admin'  # Title for the admin interface
    ##    Example of how to use the slug field
    ##    prepopulated_fields = {'title': ('title',)}  # Automatically populate the slug field based on the title
    ## do not use the slug to insert spaces amid the argument as an endpoint of the URL

    formfield_overrides = {
        models.IntegerField: {"widget": NumberInput(attrs={"size": "10"})}
    }  # Use a number input for DecimalFields
    show_facets = admin.ShowFacets.ALWAYS


# Register the Listing model with the admin site using the ListingAdmin class


admin.site.register(Order, OrderAdmin)  # Register the Order model with the admin site
admin.site.register(OrderItem, OrderItemAdmin)
