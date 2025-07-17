import requests
from django.shortcuts import render, get_object_or_404
from .models import Book
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
# Create your views here.

def categories(request):
    categories = {
        '文學': ['中國文學', '西方文學', '亞洲文學', '其他文學'],
        '社會科學': ['心理學', '社會學', '政治學', '法律', '其他社會科學'],
        '商業財經': ['投資理財', '商業管理', '市場營銷', '會計財務', '經濟學', '其他商業財經'],
        '飲食文化': ['烹飪', '飲品', '飲食歷史', '其他飲食文化'],
        '心理勵志': ['自我提升', '成功學', '心靈雞湯', '其他心理勵志'],
        '其他':['其他']
    }
    category = request.GET.get('category', '')
    subcategory = request.GET.get('subcategory', '')
    
    books = Book.objects.all()
    if category:
        try:
            books = books.filter(category__iexact=category.strip())
        except ValueError:
            messages.error(request, '無效的類別。')
    if subcategory:
        try:
            books = books.filter(subcategory__iexact=subcategory.strip())
        except ValueError:
            messages.error(request, '無效的子類別。')

    # 分頁處理
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'books/categories.html', {
        'categories': categories,
        'books': page_obj,
        'category': category,  
        'subcategory': subcategory,  
    })

def book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    
    # 獲取最近的評論（只顯示前3條）
    recent_reviews = book.reviews.select_related('user').order_by('-created_at')[:3]
    
    # 檢查當前用戶是否已經評論過
    user_review = None
    if request.user.is_authenticated:
        user_review = book.reviews.filter(user=request.user).first()
    
    context = {
        'book': book,
        'recent_reviews': recent_reviews,
        'user_review': user_review,
    }
    return render(request, 'books/book.html', context)

def search(request):
    query = request.GET.get('q', '')           # 取得搜尋關鍵字，q 參數（通常係搜尋字），如果冇，就用預設值 ''(emtpy)
    category = request.GET.get('category', '') # 取得分類（如有）
    price = request.GET.get('price', '')       # 取得價格範圍（如有）
    books = Book.objects.all()                 # 先取出所有書
    #左邊嘅variables （自定義名稱）係從 GET 請求中取得的參數，右邊係預設值
    # 如果冇輸入關鍵字，就用所有書籍 
    # get 後面嘅tuple('xxx', '') 左邊係key名（key），右邊係預設值

    # 如果有輸入關鍵字，就用 title 或 author 做模糊搜尋
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))

    # 如果有選分類，就 filter category
    if category:
        books = books.filter(category=category)

    # 如果有選價格範圍，就 filter price
    if price:
        if price == '0-100':
            books = books.filter(price__gte=0, price__lte=100)
        elif price == '101-200':
            books = books.filter(price__gte=101, price__lte=200)
        elif price == '201-500':
            books = books.filter(price__gte=201, price__lte=500)
        elif price == '501-':
            books = books.filter(price__gte=501)

    # 分頁處理
    paginator = Paginator(books, 8)  # 每頁顯示 8 本書
    page_number = request.GET.get('page', 1)
    try:
        page_number = int(page_number)  # 確保 page_number 是整數
    except ValueError:
        page_number = 1
    # 如果 page_number 不是有效的整數，則默認為 1
    page_obj = paginator.get_page(page_number) 
    # 將搜尋結果傳去 template
    return render(request, 'books/search.html', {'books': page_obj, 'query': query, 'category': category, 'price': price})

def hots(request):
    category = request.GET.get('category', 'hots')
    books = Book.objects.all()
    if category == 'hots':
        books = books.filter(is_hots=True)
        category_name = '熱買推薦'
    elif category == 'newbook':
        books = books.filter(is_new=True)
        category_name = '新書上架'
    elif category == 'recommend':
        books = books.filter(is_recommended=True)
        category_name = '精選推薦'

    categories = [
        ('hots', '熱買推薦'),
        ('newbook', '新書上架'),
        ('recommend', '精選推薦'),
    ]

    # 分頁處理
    paginator = Paginator(books, 12)  # 每頁顯示 12 本書
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'books/hots.html', {
        'categories': categories,
        'books': page_obj,
        'selected_category': category,
        'category_name': category_name,
    })

def fastapi_search(request):
    results = []
    query = request.GET.get('q', '')
    error_message = None
    
    if query:
        try:
            # 確保正確的 API endpoint 和參數
            resp = requests.get(
                'http://localhost:8001/search', 
                params={'title': query},
                timeout=15,  # 增加超時時間
                headers={'Content-Type': 'application/json'}  # 添加標頭
            )
            print(f"請求 URL: {resp.url}")  # 顯示完整請求 URL
            print(f"FastAPI 回應狀態: {resp.status_code}")
            print(f"FastAPI 回應內容: {resp.text}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"解析後的 JSON: {data}")
                    
                    # 根據實際回應格式處理資料
                    raw_books = []
                    if 'google_books' in data:
                        raw_books = data['google_books']
                    elif 'books' in data:
                        raw_books = data['books']
                    elif isinstance(data, list):
                        raw_books = data
                    else:
                        raw_books = [data]
                    
                    # 格式化書籍資料以統一格式
                    results = []
                    for book in raw_books:
                        formatted_book = {
                            'title': book.get('title', '無標題'),
                            'author': ', '.join(book.get('authors', ['未知作者'])),  # 將 authors 陣列轉為字串
                            'publishedDate': book.get('publishedDate', ''),
                            'publisher': book.get('publisher', ''),
                            'description': book.get('description', ''),
                        }
                        results.append(formatted_book)
                        
                    if not results:
                        error_message = "沒有找到相關書籍"
                except ValueError as e:
                    error_message = f"無法解析 JSON 回應: {e}"
            else:
                error_message = f"API 回應錯誤: {resp.status_code} - {resp.text}"
                
        except requests.exceptions.ConnectionError as e:
            error_message = f"無法連接到 FastAPI 服務 (http://localhost:8001)，請確認服務是否已啟動。錯誤: {e}"
        except requests.exceptions.Timeout:
            error_message = "請求超時（15秒），請稍後再試"
        except Exception as e:
            error_message = f"查詢失敗: {type(e).__name__}: {str(e)}"
            
    return render(request, 'books/fastapi_search.html', {
        'results': results, 
        'query': query,
        'error_message': error_message
    })