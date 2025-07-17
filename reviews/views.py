from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Review, ReviewHelpful
from .forms import ReviewForm
from books.models import Book
from orders.models import OrderItem


@login_required
def add_review(request, book_id):
    """添加評論"""
    book = get_object_or_404(Book, id=book_id)
    
    # 檢查用戶是否已經評論過這本書
    existing_review = Review.objects.filter(user=request.user, book=book).first()
    if existing_review:
        messages.warning(request, "您已經評論過這本書了，您可以編輯您的評論。")
        return redirect('reviews:edit_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book = book
            review.save()
            messages.success(request, "評論發布成功！")
            return redirect('books:book', book_id=book.id)
    else:
        form = ReviewForm()
    
    # 檢查用戶是否購買過這本書
    has_purchased = OrderItem.objects.filter(
        orderid__userId=request.user,
        bookid=book,
        orderid__payment_status='paid'
    ).exists()
    
    context = {
        'form': form,
        'book': book,
        'has_purchased': has_purchased,
    }
    return render(request, 'reviews/add_review.html', context)


@login_required
def edit_review(request, review_id):
    """編輯評論"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "評論更新成功！")
            return redirect('books:book', book_id=review.book.id)
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'book': review.book,
    }
    return render(request, 'reviews/edit_review.html', context)


@login_required
def delete_review(request, review_id):
    """刪除評論"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    book = review.book
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, "評論已刪除。")
        return redirect('books:book', book_id=book.id)
    
    context = {
        'review': review,
        'book': book,
    }
    return render(request, 'reviews/delete_review.html', context)


def book_reviews(request, book_id):
    """書籍評論列表"""
    book = get_object_or_404(Book, id=book_id)
    reviews_list = Review.objects.filter(book=book).select_related('user')
    
    # 排序選項
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        reviews_list = reviews_list.order_by('created_at')
    elif sort_by == 'rating_high':
        reviews_list = reviews_list.order_by('-rating', '-created_at')
    elif sort_by == 'rating_low':
        reviews_list = reviews_list.order_by('rating', '-created_at')
    elif sort_by == 'helpful':
        reviews_list = reviews_list.order_by('-helpful_votes__count', '-created_at')
    else:  # newest
        reviews_list = reviews_list.order_by('-created_at')
    
    # 分頁
    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    
    # 評分統計
    rating_stats = {}
    for i in range(1, 6):
        rating_stats[i] = reviews_list.filter(rating=i).count()
    
    context = {
        'book': book,
        'reviews': reviews,
        'rating_stats': rating_stats,
        'sort_by': sort_by,
    }
    return render(request, 'reviews/book_reviews.html', context)


@login_required
@require_POST
def toggle_helpful(request, review_id):
    """切換評論有用性投票"""
    review = get_object_or_404(Review, id=review_id)
    is_helpful = request.POST.get('is_helpful') == 'true'
    
    # 檢查用戶是否已經投票過
    helpful_vote, created = ReviewHelpful.objects.get_or_create(
        user=request.user,
        review=review,
        defaults={'is_helpful': is_helpful}
    )
    
    if not created:
        if helpful_vote.is_helpful == is_helpful:
            # 如果重複點擊同一個按鈕，刪除投票
            helpful_vote.delete()
            action = 'removed'
        else:
            # 如果點擊了不同的按鈕，更新投票
            helpful_vote.is_helpful = is_helpful
            helpful_vote.save()
            action = 'updated'
    else:
        action = 'added'
    
    # 計算新的投票數
    helpful_count = review.helpful_votes.filter(is_helpful=True).count()
    unhelpful_count = review.helpful_votes.filter(is_helpful=False).count()
    
    return JsonResponse({
        'action': action,
        'helpful_count': helpful_count,
        'unhelpful_count': unhelpful_count,
    })


def user_reviews(request, username=None):
    """用戶評論列表"""
    if username:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    reviews_list = Review.objects.filter(user=user).select_related('book')
    
    # 分頁
    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    
    context = {
        'profile_user': user,
        'reviews': reviews,
    }
    return render(request, 'reviews/user_reviews.html', context)
