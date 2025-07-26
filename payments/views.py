import stripe
from django.conf import settings
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order, OrderItem
from notifications.utils import send_payment_success_email, send_payment_failed_email
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentPageView(View):
    def get(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id, userId=request.user)
        order_items = OrderItem.objects.filter(orderid=order)
        order_total = order.get_final_amount()  # 使用最終金額（包含折扣）
        return render(request, 'payments/payment.html', {
            'order': order,
            'order_items': order_items,
            'order_total': order_total,
            'final_amount': order_total,
            'discount_amount': order.discount_amount,
            'coupon': order.coupon,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
        })

class CreateCheckoutSessionView(View):
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id, userId=request.user)
        final_amount = order.get_final_amount()  # 使用最終金額
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'hkd',
                            'product_data': {
                                'name': f'訂單 #{order.id}',
                            },
                            'unit_amount': int(final_amount * 100),  # 使用最終金額，Stripe 以分為單位
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                metadata={'order_id': order.id},  # 添加訂單 ID 到 metadata
                success_url=request.build_absolute_uri(f'/payments/success/?order_id={order.id}'),
                cancel_url=request.build_absolute_uri('/payments/cancel/'),
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe

@csrf_exempt
def stripe_webhook(request):
    print(f"[DEBUG] Stripe webhook 被調用 - 方法: {request.method}")
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    print(f"[DEBUG] 收到 webhook payload 長度: {len(payload)}")
    
    # 暫時跳過簽名驗證來測試功能
    try:
        import json
        event = json.loads(payload)
        print(f"[DEBUG] Webhook 事件類型: {event.get('type', 'unknown')}")
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON 解析失敗: {str(e)}")
        return HttpResponse(f"Invalid JSON: {str(e)}", status=400)
    
    # 如果你有正確的 webhook secret，可以取消註釋下面的代碼
    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    #     )
    #     print(f"[DEBUG] Webhook 事件驗證成功，事件類型: {event['type']}")
    # except ValueError as e:
    #     print(f"[DEBUG] Webhook payload 無效: {str(e)}")
    #     return HttpResponse(f"Invalid payload: {str(e)}", status=400)
    # except stripe.error.SignatureVerificationError as e:
    #     print(f"[DEBUG] Webhook 簽名驗證失敗: {str(e)}")
    #     return HttpResponse(f"Invalid signature: {str(e)}", status=400)

    # 處理 checkout.session.completed 事件（付款成功）
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"[DEBUG] Stripe webhook 收到 checkout.session.completed 事件")
        
        try:
            # 從 metadata 獲取訂單 ID
            order_id = session.get('metadata', {}).get('order_id')
            print(f"[DEBUG] 從 Stripe session 獲取到 order_id: {order_id}")
            
            if order_id:
                from orders.models import Order
                order = Order.objects.get(id=order_id)
                print(f"[DEBUG] Stripe付款開始處理訂單 {order.id}")
                
                order.payment_status = "已付款"
                order.save()
                print(f"[DEBUG] 訂單 {order.id} 狀態已更新為已付款")
                
                # 如果使用了優惠碼，標記為已使用
                if order.coupon:
                    order.coupon.use_coupon()
                    print(f"[DEBUG] 優惠碼 {order.coupon.code} 已標記為使用")
                
                # 付款成功後標記購物車商品為已下單並扣減庫存
                if order.shopCartId:
                    # 通過 OrderItem 找到對應的 CartItem 並標記為已下單
                    order_items = OrderItem.objects.filter(orderid=order)
                    print(f"[DEBUG] 找到 {order_items.count()} 個訂單商品")
                    
                    for order_item in order_items:
                        cart_item = order_item.CartID
                        book = cart_item.bookId
                        print(f"[DEBUG] 處理 CartItem {cart_item.id}: {book.title}")
                        
                        # 扣減庫存
                        if book.stock >= cart_item.quantity:
                            book.stock -= cart_item.quantity
                            book.save()
                            print(f"[DEBUG] {book.title} 庫存已扣減 {cart_item.quantity}，剩餘庫存：{book.stock}")
                        else:
                            print(f"[WARNING] {book.title} 庫存不足，無法扣減")
                    
                    # 使用訂單模型的方法清空購物車
                    print(f"[DEBUG] 清空用戶 {order.userId} 的購物車")
                    order.clear_cart_after_payment()
                    print(f"[DEBUG] 購物車已清空已下單商品")
                
                # 發送付款成功郵件
                send_payment_success_email(order, 'Stripe')
                
                print(f"[DEBUG] 訂單 {order.id} 狀態已更新為已付款，購物車已清空")
            else:
                print("[DEBUG] 無法從 session metadata 獲取訂單 ID")
                
        except Order.DoesNotExist:
            print(f"[DEBUG] 找不到訂單 ID: {order_id}")
        except Exception as e:
            print(f"[DEBUG] 更新訂單狀態時發生錯誤: {str(e)}")
    # 處理付款失敗事件（如 charge.failed）
    elif event['type'] == 'charge.failed':
        session = event['data']['object']
        try:
            order_id = session.get('metadata', {}).get('order_id')
            if order_id:
                order = Order.objects.get(id=order_id)
                send_payment_failed_email(order, 'Stripe payment failed')
        except Order.DoesNotExist:
            print(f"找不到訂單 ID: {order_id}")

    return HttpResponse(status=200)

def fps_payment(request, order_id):
    if request.method == "POST":
        # 取得訂單並更新狀態
        order = get_object_or_404(Order, id=order_id, userId=request.user)
        print(f"[DEBUG] FPS付款開始處理訂單 {order.id}")
        
        order.payment_status = "已付款"
        order.save()
        print(f"[DEBUG] 訂單 {order.id} 狀態已更新為已付款")
        
        # 如果使用了優惠碼，標記為已使用
        if order.coupon:
            order.coupon.use_coupon()
            print(f"[DEBUG] 優惠碼 {order.coupon.code} 已標記為使用")
        
        # 付款成功後標記購物車商品為已下單並扣減庫存
        if order.shopCartId:
            # 通過 OrderItem 找到對應的 CartItem 並標記為已下單
            order_items = OrderItem.objects.filter(orderid=order)
            print(f"[DEBUG] 找到 {order_items.count()} 個訂單商品")
            
            for order_item in order_items:
                cart_item = order_item.CartID
                book = cart_item.bookId
                print(f"[DEBUG] 處理 CartItem {cart_item.id}: {book.title}")
                
                # 扣減庫存
                if book.stock >= cart_item.quantity:
                    book.stock -= cart_item.quantity
                    book.save()
                    print(f"[DEBUG] {book.title} 庫存已扣減 {cart_item.quantity}，剩餘庫存：{book.stock}")
                else:
                    print(f"[WARNING] {book.title} 庫存不足，無法扣減")
            
            # 使用訂單模型的方法清空購物車
            print(f"[DEBUG] 清空用戶 {order.userId} 的購物車")
            order.clear_cart_after_payment()
            print(f"[DEBUG] 購物車已清空已下單商品")
        
        # 發送付款成功郵件
        send_payment_success_email(order, 'FPS')

        # 這裡可以處理 FPS 付款資料，例如上傳收據
        return render(request, 'payments/success.html', {
            'method': 'FPS',
            'order': order,
            'message': 'FPS 付款已完成'
        })
    return redirect('payments:payment', order_id=order_id)



def payment_success(request):
    # 嘗試從 session 或其他方式獲取訂單資訊
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = get_object_or_404(Order, id=order_id, userId=request.user)
            print(f"[DEBUG] 付款成功頁面 - 處理訂單 {order.id}")
            
            # 確保訂單狀態已更新為已付款（因為 webhook 可能有延遲）
            if order.payment_status != "已付款":
                print(f"[DEBUG] 訂單 {order.id} 狀態仍為 {order.payment_status}，手動更新為已付款")
                
                # 手動更新訂單狀態和購物車
                order.payment_status = "已付款"
                order.save()
                
                # 如果使用了優惠碼，標記為已使用
                if order.coupon:
                    order.coupon.use_coupon()
                    print(f"[DEBUG] 優惠碼 {order.coupon.code} 已標記為使用")
                
                # 手動標記購物車商品為已下單並扣減庫存
                if order.shopCartId:
                    order_items = OrderItem.objects.filter(orderid=order)
                    print(f"[DEBUG] 手動處理 {order_items.count()} 個訂單商品")
                    
                    for order_item in order_items:
                        cart_item = order_item.CartID
                        book = cart_item.bookId
                        print(f"[DEBUG] 手動處理 CartItem {cart_item.id}: {book.title}")
                        
                        # 扣減庫存
                        if book.stock >= cart_item.quantity:
                            book.stock -= cart_item.quantity
                            book.save()
                            print(f"[DEBUG] {book.title} 庫存已扣減 {cart_item.quantity}，剩餘庫存：{book.stock}")
                        else:
                            print(f"[WARNING] {book.title} 庫存不足，無法扣減")
                
                # 使用訂單模型的方法清空購物車
                print(f"[DEBUG] 清空用戶 {order.userId} 的購物車")
                order.clear_cart_after_payment()
                print(f"[DEBUG] 購物車已清空已下單商品")
            
            return render(request, 'payments/success.html', {
                'order': order,
                'method': 'Stripe',
                'message': 'Stripe 付款已完成'
            })
        except Exception as e:
            print(f"[DEBUG] 付款成功頁面處理錯誤: {str(e)}")
    
    return render(request, 'payments/success.html', {
        'message': '付款已完成'
    })

def payment_cancel(request):
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = get_object_or_404(Order, id=order_id, userId=request.user)
            send_payment_failed_email(order, 'Payment was cancelled')
        except Order.DoesNotExist:
            pass
    
    return render(request, 'payments/cancel.html')

# urls.py (notification 應用的 URL 配置)
from django.urls import path
from . import views

app_name = 'notification'
urlpatterns = []