#!/usr/bin/env python
"""
創建測試優惠碼腳本
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# 設置 Django 環境
sys.path.append('/Users/jamestong/Documents/GitHub/bookstore_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from orders.models import Coupon

def create_test_coupons():
    """創建一些測試優惠碼"""
    
    # 刪除現有的測試優惠碼
    Coupon.objects.filter(code__startswith='TEST').delete()
    
    now = timezone.now()
    
    coupons_data = [
        {
            'code': 'WELCOME10',
            'discount': 10.00,
            'is_percent': True,
            'min_order_amount': 50.00,
            'valid_from': now,
            'valid_to': now + timedelta(days=30),
            'active': True,
            'usage_limit': 100,
            'per_user_limit': 1
        },
        {
            'code': 'SAVE20',
            'discount': 20.00,
            'is_percent': False,
            'min_order_amount': 100.00,
            'valid_from': now,
            'valid_to': now + timedelta(days=30),
            'active': True,
            'usage_limit': 50,
            'per_user_limit': 2
        },
        {
            'code': 'TEST50',
            'discount': 50.00,
            'is_percent': False,
            'min_order_amount': 0.00,
            'valid_from': now,
            'valid_to': now + timedelta(days=30),
            'active': True,
            'usage_limit': None,  # 無限制
            'per_user_limit': 5
        },
    ]
    
    created_coupons = []
    for coupon_data in coupons_data:
        coupon, created = Coupon.objects.get_or_create(
            code=coupon_data['code'],
            defaults=coupon_data
        )
        if created:
            created_coupons.append(coupon)
            print(f"✅ 創建優惠碼: {coupon.code}")
        else:
            print(f"⚠️ 優惠碼已存在: {coupon.code}")
    
    print(f"\n🎉 成功創建 {len(created_coupons)} 個測試優惠碼！")
    print("\n可用的測試優惠碼:")
    for coupon in Coupon.objects.filter(active=True):
        discount_text = f"{coupon.discount}%" if coupon.is_percent else f"${coupon.discount}"
        print(f"  • {coupon.code}: {discount_text} 折扣 (最低消費: ${coupon.min_order_amount})")

if __name__ == '__main__':
    create_test_coupons()
