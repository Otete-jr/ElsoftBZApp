from django.urls import path
from . import views

urlpatterns = [
    path('register-store/', views.register_store, name='register-store'),
    path('login/', views.login_user, name='login'),
    path('expenses/', views.manage_expenses, name='manage-expenses'),
    path('make-sale/', views.make_sale, name='make-sale'),
    path('products/', views.manage_products, name='manage-products'),
    path('reports/detailed/', views.get_detailed_reports, name='detailed-reports'),
    path('products/<int:pk>/restock/', views.restock_product, name='restock-product'),
    
]