"""
URL configuration for bookstore_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static 
from django.conf import settings

urlpatterns = [
    path('', include('pages.urls', namespace='pages')),
    path('books/', include('books.urls')),
    path('accounts/', include('accounts.urls')),
    path('carts/', include('carts.urls',namespace='carts')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('inquiries/', include('inquiries.urls')),
    path('reviews/', include('reviews.urls')),
    path('admin/', admin.site.urls),
] + debug_toolbar_urls()
# 多人用要先放  

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # DEBUG 模式下，提供靜態檔案服務