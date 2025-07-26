from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from books.models import Book


class ShopCart(models.Model):
    datetime = models.DateTimeField(default=datetime.now, blank=True)
    userId = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True)
    
    def clear_cart(self):
        """清空購物車中所有商品"""
        self.cartitem_set.all().delete()
        
    def clear_ordered_items(self):
        """清空已下單的商品"""
        self.cartitem_set.filter(is_ordered=True).delete()


class CartItem(models.Model):
    bookId = models.ForeignKey(Book, on_delete=models.DO_NOTHING)
    shopCartId = models.ForeignKey(ShopCart, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField()
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_ordered = models.BooleanField(default=False)  # 標記是否已下單
