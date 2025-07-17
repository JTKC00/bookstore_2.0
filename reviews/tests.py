from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from books.models import Book
from .models import Review, ReviewHelpful

User = get_user_model()


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            publisher='Test Publisher',
            isbn='1234567890123',
            price=29.99,
            category='Fiction',
            subcategory='Romance',
            language='Chinese'
        )
    
    def test_review_creation(self):
        review = Review.objects.create(
            user=self.user,
            book=self.book,
            rating=5,
            title='Great Book!',
            content='This is an excellent book.'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.rating_stars, '⭐⭐⭐⭐⭐')
        self.assertEqual(str(review), f"{self.user.username} - {self.book.title} (5星)")
    
    def test_unique_review_per_user_book(self):
        Review.objects.create(
            user=self.user,
            book=self.book,
            rating=5,
            title='First Review',
            content='First review content.'
        )
        # 嘗試創建第二個評論應該失敗
        with self.assertRaises(Exception):
            Review.objects.create(
                user=self.user,
                book=self.book,
                rating=4,
                title='Second Review',
                content='Second review content.'
            )


class ReviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            publisher='Test Publisher',
            isbn='1234567890123',
            price=29.99,
            category='Fiction',
            subcategory='Romance',
            language='Chinese'
        )
    
    def test_add_review_requires_login(self):
        url = reverse('reviews:add_review', kwargs={'book_id': self.book.id})
        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')
    
    def test_add_review_authenticated_user(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('reviews:add_review', kwargs={'book_id': self.book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')
    
    def test_book_reviews_public_access(self):
        url = reverse('reviews:book_reviews', kwargs={'book_id': self.book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
