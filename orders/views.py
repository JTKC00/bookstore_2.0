from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from carts.models import ShopCart, CartItem
from django.contrib import messages
from datetime import datetime


@login_required
def shipping(request):

    shopcart_id = request.GET.get("shopcart_id")
    total_amount = request.GET.get("total_amount")
    total_quantity = request.GET.get("total_quantity")

    shopcart = get_object_or_404(ShopCart, id=shopcart_id, userId=request.user)
    cart_items = shopcart.cartitem_set.filter(is_ordered=False)

    return render(
        request,    
        "orders/shipping.html",
        {
            "shopcart": shopcart,
            "cart_items": cart_items,
            "total_quantity": total_quantity,
            "total_amount": total_amount,
        },
    )


@login_required
def orderconfirm(request):
    if request.method == "POST":
        shopcart_id = request.POST.get("shopcart_id")
        total_amount = request.POST.get("total_amount")
        total_quantity = request.POST.get("total_quantity")
        receipient = request.POST.get("receipient")
        receipient_phone = request.POST.get("receipient_phone")
        shipping_address = request.POST.get("shipping_address")

        shopcart = get_object_or_404(ShopCart, id=shopcart_id, userId=request.user)
        cart_items = shopcart.cartitem_set.filter(is_ordered=False)

        # 檢查是否已經有未付款的訂單（避免重複創建）
        pending_order = Order.objects.filter(
            shopCartId=shopcart, 
            userId=request.user, 
            payment_status="PENDI"
        ).first()
        
        if pending_order:
            # 當存在未付款訂單時，需要檢查購物車是否有變更
            order_items = OrderItem.objects.filter(orderid=pending_order)
            cart_items_current = shopcart.cartitem_set.filter(is_ordered=False)
            
            # 檢查購物車是否有變更（數量或商品）
            needs_update = False
            
            # 重新計算當前購物車的總計
            current_total_quantity = sum(item.quantity for item in cart_items_current)
            current_total_amount = sum(item.sub_total for item in cart_items_current)
            
            # 檢查商品數量是否不同
            if cart_items_current.count() != order_items.count():
                needs_update = True
            else:
                # 檢查每個商品的數量是否變更
                for cart_item in cart_items_current:
                    corresponding_order_item = order_items.filter(CartID=cart_item).first()
                    if not corresponding_order_item or corresponding_order_item.quantity != cart_item.quantity:
                        needs_update = True
                        break
            
            if needs_update:
                print(f"[DEBUG] 購物車已變更，更新訂單 {pending_order.id}")
                
                # 刪除舊的訂單項目
                order_items.delete()
                
                # 更新訂單總計
                pending_order.total_amount = current_total_amount
                pending_order.save()
                
                # 重新創建訂單項目
                for item in cart_items_current:
                    OrderItem.objects.create(
                        bookid=item.bookId,
                        CartID=item,
                        orderid=pending_order,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        subTotal=item.quantity * item.unit_price,
                    )
                
                print(f"[DEBUG] 訂單 {pending_order.id} 已更新，新總額: {current_total_amount}")
            
            # 重新獲取更新後的訂單項目
            updated_order_items = OrderItem.objects.filter(orderid=pending_order)
            
            return render(
                request,
                "orders/orderconfirm.html",
                {
                    "order": pending_order,
                    "cart_items": cart_items_current,  # 使用最新的購物車數據
                    "total_quantity": current_total_quantity,
                    "total_amount": current_total_amount,
                    "shopcart": shopcart,
                },
            )

        # 在創建訂單前檢查所有商品庫存
        stock_errors = []
        for item in cart_items:
            if item.quantity > item.bookId.stock:
                stock_errors.append(
                    f"{item.bookId.title}：需要 {item.quantity} 本，但庫存只有 {item.bookId.stock} 本"
                )
        
        if stock_errors:
            for error in stock_errors:
                messages.error(request, error)
            messages.error(request, "請調整購物車中的商品數量後再試。")
            return redirect("carts:cart")

        # Otherwise, create a new order and order items
        order = Order.objects.create(
            userId=request.user,
            shopCartId=shopcart,
            invoice_no=shopcart_id,
            order_date=datetime.now(),
            receipient=receipient,
            receipient_phone=receipient_phone,
            shipping_address=shipping_address,
            payment_status="PENDI",
            shipping_status="STOCK",
            total_amount=total_amount,
        )

        for item in cart_items:
            OrderItem.objects.create(
                bookid=item.bookId,
                CartID=item,
                orderid=order,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subTotal=item.quantity * item.unit_price,
            )

        return render(
            request,
            "orders/orderconfirm.html",
            {
                "order": order,
                "cart_items": cart_items,
                "total_quantity": total_quantity,
                "total_amount": total_amount,
                "shopcart": shopcart,
            },
        )
    else:
        return redirect("orders:shipping")


@login_required
def create_order(request):
    if not request.user.is_authenticated:
        messages.error(request, "請先登入")
        return redirect('accounts:login')

    shopcart = get_object_or_404(ShopCart, userId=request.user)
    cart_items = shopcart.cartitem_set.filter(is_ordered=False)

    # 防止重覆：檢查這個購物車是否已建立訂單且未取消
    existing_order = Order.objects.filter(shopcart=shopcart, status__in=['pending', 'paid']).first()
    if existing_order:
        messages.warning(request, "此購物車已建立訂單，請勿重覆下單。")
        return redirect('orders:orderconfirm', order_id=existing_order.id)

    # 建立訂單
    order = Order.objects.create(
        user=request.user,
        shopcart=shopcart,
        total_amount=sum(item.sub_total for item in cart_items),
        status='pending'
    )
    # 建立訂單明細
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            book=item.bookId,
            quantity=item.quantity,
            unit_price=item.unit_price,
            sub_total=item.sub_total
        )
    # 建立訂單成功後，標記購物車商品為已下單
    shopcart.cartitem_set.filter(is_ordered=False).update(is_ordered=True)
    # 或者：shopcart.delete()  # 如果你想連購物車本身都刪除
    messages.success(request, "訂單已建立，購物車已清空。")
    return redirect('orders:orderconfirm', order_id=order.id)


@login_required
def order_detail(request, order_id):
    """訂單詳情頁面"""
    order = get_object_or_404(Order, id=order_id, userId=request.user)
    order_items = OrderItem.objects.filter(orderid=order)
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_items': order_items,
    })


@login_required
def order_list(request):
    """用戶訂單列表頁面"""
    from django.core.paginator import Paginator
    
    orders = Order.objects.filter(userId=request.user).order_by('-order_date')
    
    # 分頁處理
    paginator = Paginator(orders, 10)  # 每頁顯示 10 個訂單
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'orders/order_list.html', {
        'orders': page_obj,
    })


@login_required
def cancel_order(request):
    """取消訂單處理
    
    用於用戶在訂單確認頁面取消訂單。不刪除購物車，
    但會清除 OrderItem 記錄，並將訂單狀態標記為已取消。
    """
    shopcart_id = request.GET.get("shopcart_id")
    
    if not shopcart_id:
        messages.error(request, "無效的請求，缺少購物車ID。")
        return redirect("carts:cart")
    
    try:
        # 獲取購物車
        shopcart = get_object_or_404(ShopCart, id=shopcart_id, userId=request.user)
        
        # 檢查是否有處於 PENDI 狀態的相關訂單
        pending_order = Order.objects.filter(
            shopCartId=shopcart, 
            userId=request.user,
            payment_status="PENDI"
        ).first()
        
        if pending_order:
            # 有未完成的訂單，先記錄訂單號
            order_id = pending_order.id
            
            # 刪除相關的 OrderItem 記錄
            OrderItem.objects.filter(orderid=pending_order).delete()
            
            # 可選：刪除訂單本身或標記為已取消
            pending_order.delete()
            # 或者標記為已取消:
            # pending_order.payment_status = "CANC"
            # pending_order.save()
            
            messages.success(request, f"訂單 #{order_id} 已成功取消，您可以繼續購物或調整購物車。")
        else:
            messages.info(request, "未找到待處理的訂單。")
    
    except Exception as e:
        messages.error(request, f"取消訂單時發生錯誤: {str(e)}")
    
    # 重定向到購物車頁面
    return redirect("carts:cart")


@login_required
def cancel_order_by_id(request, order_id):
    """透過訂單ID取消訂單
    
    用於用戶在訂單列表或訂單詳情頁面取消訂單。
    只有處於待付款(PENDI)狀態的訂單可以被取消。
    """
    try:
        # 獲取訂單並確認是該用戶的訂單
        order = get_object_or_404(Order, id=order_id, userId=request.user)
        
        # 檢查訂單狀態是否為待付款
        if order.payment_status != "待付款":
            messages.error(request, "只能取消待付款的訂單。")
            return redirect("orders:order_detail", order_id=order_id)
        
        # 記錄該訂單的購物車ID，以便返回時可以使用
        shopcart_id = order.shopCartId.id if order.shopCartId else None
        
        # 刪除相關的OrderItem記錄
        OrderItem.objects.filter(orderid=order).delete()
        
        # 可選：保留訂單但標記為已取消
        # order.payment_status = "CANC"
        # order.save()
        
        # 或完全刪除訂單
        order.delete()
        
        messages.success(request, f"訂單 #{order_id} 已成功取消。")
        
        # 確認從哪裡返回
        referer = request.META.get('HTTP_REFERER', '')
        if 'detail' in referer:
            # 如果是從訂單詳情頁面來的，則返回訂單列表
            return redirect("orders:order_list")
        else:
            # 否則返回原頁面（大多是訂單列表）
            return redirect("orders:order_list")
            
    except Exception as e:
        messages.error(request, f"取消訂單時發生錯誤: {str(e)}")
        return redirect("orders:order_list")
