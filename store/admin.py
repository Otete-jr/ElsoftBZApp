from django.contrib import admin
from .models import Store, Product, Sale, Expense, User

# Sajili hapa ili uzione kwenye Admin Panel
admin.site.register(Store)
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(Expense)
admin.site.register(User)
