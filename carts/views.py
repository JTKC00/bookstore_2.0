from django.shortcuts import get_object_or_404, render, redirect
from books.models import Book
from .models import ShopCart, CartItem
from django.contrib import messages
from django.http import JsonResponse


def cart(request):
    if request.user.is_authenticated:
        # 獲取用戶最新的購物車，如果沒有則創建新的
        try:
            # 優先獲取有未下單商品的購物車
            shopcart = ShopCart.objects.filter(
                userId=request.user,
                cartitem__is_ordered=False
            ).distinct().first()
            
            if not shopcart:
                # 如果沒有包含未下單商品的購物車，獲取最新的購物車
                shopcart = ShopCart.objects.filter(userId=request.user).order_by('-id').first()
            
            if not shopcart:
                # 如果完全沒有購物車，創建新的
                shopcart = ShopCart.objects.create(userId=request.user)
                print(f"[DEBUG] 為用戶 {request.user} 創建了新的購物車 {shopcart.id}")
        except Exception as e:
            # 發生任何錯誤時創建新購物車
            shopcart = ShopCart.objects.create(userId=request.user)
            print(f"[DEBUG] 發生錯誤後為用戶 {request.user} 創建了新的購物車 {shopcart.id}: {str(e)}")

        # 只顯示未下單的商品
        cart_items = shopcart.cartitem_set.filter(is_ordered=False)

        # 計算總數量和總價格
        total_quantity = sum(item.quantity for item in cart_items)
        total_price = sum(item.sub_total for item in cart_items)

        # 檢查購物車是否為空
        if not cart_items.exists():
            messages.info(
                request, "您的購物車目前是空的，歡迎瀏覽商品並加入購物車。"
            )

        return render(
            request,
            "carts/cart.html",
            {
                "shopcart": shopcart,
                "cart_items": cart_items,
                "total_quantity": total_quantity,
                "total_price": total_price,
            },
        )
    else:
        messages.error(request, "您尚未登入，請先登入以使用購物車功能。")
        return redirect("accounts:login")


def add_to_cart(request, book_id):
    if not request.user.is_authenticated:
        messages.error(request, "您尚未登入，請先登入以使用購物車功能。")
        return redirect("accounts:login")

    book = get_object_or_404(Book, pk=book_id)
    
    # 檢查庫存
    if book.stock <= 0:
        messages.error(request, f"抱歉，{book.title} 目前缺貨。")
        return redirect("books:book", book_id=book_id)

    # 獲取用戶輸入的數量，預設為1
    try:
        quantity = int(request.GET.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1
    
    print(f"[DEBUG] 用戶想要加入 {quantity} 本 {book.title}")

    # 獲取或創建用戶購物車（使用最新的有效購物車）
    try:
        # 優先獲取有未下單商品的購物車
        shop_cart = ShopCart.objects.filter(
            userId=request.user,
            cartitem__is_ordered=False
        ).distinct().first()
        
        if not shop_cart:
            # 如果沒有包含未下單商品的購物車，獲取最新的購物車
            shop_cart = ShopCart.objects.filter(userId=request.user).order_by('-id').first()
        
        if not shop_cart:
            # 如果完全沒有購物車，創建新的
            shop_cart = ShopCart.objects.create(userId=request.user)
            print(f"[DEBUG] 為用戶 {request.user} 創建了新的購物車 {shop_cart.id}")
    except Exception as e:
        # 發生任何錯誤時創建新購物車
        shop_cart = ShopCart.objects.create(userId=request.user)
        print(f"[DEBUG] 發生錯誤後為用戶 {request.user} 創建了新的購物車 {shop_cart.id}: {str(e)}")

    unit_price = book.price
    sub_total = unit_price * quantity

    # 檢查是否已在購物車中
    try:
        cart_item = CartItem.objects.get(
            bookId=book,
            shopCartId=shop_cart,
            is_ordered=False  # 只檢查未下單的商品
        )
        # 檢查加入後是否超過庫存
        new_quantity = cart_item.quantity + quantity
        if new_quantity > book.stock:
            messages.error(
                request, 
                f"抱歉，{book.title} 庫存不足。目前庫存：{book.stock}，購物車中已有：{cart_item.quantity}"
            )
            return redirect("carts:cart")
        
        # 更新數量和小計
        cart_item.quantity = new_quantity
        cart_item.sub_total = cart_item.unit_price * cart_item.quantity
        cart_item.save()
        print(f"[DEBUG] 更新購物車項目：{book.title} 數量從 {cart_item.quantity - quantity} 增加到 {cart_item.quantity}")
        messages.success(
            request, f"已將 {book.title} 的數量增加至 {cart_item.quantity}。"
        )
    except CartItem.DoesNotExist:
        # 創建新的購物車項目
        if quantity > book.stock:
            messages.error(
                request, 
                f"抱歉，{book.title} 庫存不足。目前庫存：{book.stock}"
            )
            return redirect("books:book", book_id=book_id)
            
        cart_item = CartItem.objects.create(
            bookId=book,
            shopCartId=shop_cart,
            quantity=quantity,
            unit_price=unit_price,
            sub_total=sub_total,
            is_ordered=False
        )
        print(f"[DEBUG] 創建新的購物車項目：{book.title} 數量 {quantity}, 小計 {sub_total}")
        messages.success(request, f"{book.title} 已成功添加到購物車，數量：{quantity}。")

    # 重定向到購物車頁面
    return redirect("carts:cart")


def update_quantity(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "請先登入"}, status=401)

    cart_item = get_object_or_404(CartItem, pk=item_id)

    # 確保用戶只能修改自己的購物車
    if cart_item.shopCartId.userId != request.user:
        return JsonResponse({"error": "無權限修改此項目"}, status=403)

    action = request.GET.get("action")
    book = cart_item.bookId

    if action == "increase":
        # 檢查庫存限制
        if cart_item.quantity >= book.stock:
            return JsonResponse({
                "error": f"庫存不足！{book.title} 目前庫存：{book.stock}"
            }, status=400)
        cart_item.quantity += 1
    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            return JsonResponse({"error": "數量不能少於1"}, status=400)

    cart_item.sub_total = cart_item.unit_price * cart_item.quantity
    cart_item.save()
    
    print(f"[DEBUG] 購物車項目更新：{book.title} 數量 {cart_item.quantity}, 小計 {cart_item.sub_total}")

    # 重新計算購物車總計
    shopcart = cart_item.shopCartId
    cart_items = shopcart.cartitem_set.filter(is_ordered=False)
    total_price = sum(item.sub_total for item in cart_items)
    total_quantity = sum(item.quantity for item in cart_items)
    
    # 檢查是否有相關的未付款訂單需要更新
    from orders.models import Order, OrderItem
    pending_orders = Order.objects.filter(
        shopCartId=shopcart,
        userId=request.user,
        payment_status="待付款"
    )
    
    for order in pending_orders:
        # 更新訂單總計
        order.total_amount = total_price
        order.save()
        
        # 更新對應的訂單項目
        order_item = OrderItem.objects.filter(
            orderid=order,
            CartID=cart_item
        ).first()
        
        if order_item:
            order_item.quantity = cart_item.quantity
            order_item.subTotal = cart_item.sub_total
            order_item.save()
            print(f"[DEBUG] 同步更新訂單項目：{order_item.bookid.title} 數量 {order_item.quantity}")

    return JsonResponse(
        {
            "quantity": cart_item.quantity,
            "sub_total": float(cart_item.sub_total),
            "total_price": float(total_price),
            "total_quantity": total_quantity,
            "stock": book.stock,  # 返回當前庫存
        }
    )


def remove_item(request, item_id):
    if not request.user.is_authenticated:
        messages.error(request, "請先登入")
        return redirect("accounts:login")

    cart_item = get_object_or_404(CartItem, pk=item_id)

    # 確保用戶只能刪除自己的購物車項目
    if cart_item.shopCartId.userId != request.user:
        messages.error(request, "您沒有權限刪除此項目")
        return redirect("carts:cart")

    item_name = cart_item.bookId.title
    shopcart = cart_item.shopCartId
    
    # 在刪除購物車項目前，先處理相關的訂單項目
    from orders.models import Order, OrderItem
    pending_orders = Order.objects.filter(
        shopCartId=shopcart,
        userId=request.user,
        payment_status="PENDI"
    )
    
    for order in pending_orders:
        # 刪除對應的訂單項目
        order_items_to_delete = OrderItem.objects.filter(
            orderid=order,
            CartID=cart_item
        )
        deleted_count = order_items_to_delete.count()
        order_items_to_delete.delete()
        
        if deleted_count > 0:
            print(f"[DEBUG] 從訂單 {order.id} 中刪除了 {deleted_count} 個項目")
            
            # 重新計算訂單總計
            remaining_items = shopcart.cartitem_set.filter(is_ordered=False).exclude(id=cart_item.id)
            new_total = sum(item.sub_total for item in remaining_items)
            order.total_amount = new_total
            order.save()
            print(f"[DEBUG] 更新訂單 {order.id} 總金額為 {new_total}")
    
    # 刪除購物車項目
    cart_item.delete()
    messages.success(request, f"{item_name} 已從購物車中移除")

    return redirect("carts:cart")


# 在這裡添加 JavaScript 代碼
def extra_js(request):
    return render(request, "carts/extra_js.html")
