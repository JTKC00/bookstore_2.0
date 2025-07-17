from django.contrib import admin
from .models import Review, ReviewHelpful


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'title', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at', 'book__category')
    search_fields = ('user__username', 'book__title', 'title', 'content')
    readonly_fields = ('is_verified_purchase', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'book')
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user', 'book', 'rating', 'title', 'content')
        }),
        ('系統資訊', {
            'fields': ('is_verified_purchase', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book')


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'is_helpful', 'created_at')
    list_filter = ('is_helpful', 'created_at')
    search_fields = ('user__username', 'review__title')
    raw_id_fields = ('user', 'review')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'review')
