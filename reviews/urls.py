from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<int:book_id>/', views.add_review, name='add_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('book/<int:book_id>/', views.book_reviews, name='book_reviews'),
    path('helpful/<int:review_id>/', views.toggle_helpful, name='toggle_helpful'),
    path('user/<str:username>/', views.user_reviews, name='user_reviews'),
    path('my-reviews/', views.user_reviews, name='my_reviews'),
]
