# Generated by Django 5.2.1 on 2025-07-26 09:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_coupon_min_order_amount'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='per_user_limit',
            field=models.PositiveIntegerField(default=1, help_text='每個用戶最多可使用次數'),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='usage_limit',
            field=models.PositiveIntegerField(default=1, help_text='全站總使用次數限制'),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='used_count',
            field=models.PositiveIntegerField(default=0, help_text='全站已使用次數'),
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('used_count', models.PositiveIntegerField(default=0, help_text='該用戶使用此優惠碼的次數')),
                ('first_used', models.DateTimeField(auto_now_add=True, help_text='首次使用時間')),
                ('last_used', models.DateTimeField(auto_now=True, help_text='最近使用時間')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '優惠碼使用記錄',
                'verbose_name_plural': '優惠碼使用記錄',
                'unique_together': {('user', 'coupon')},
            },
        ),
    ]
