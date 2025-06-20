from django.contrib import admin

from django.contrib import admin
from .models import MedicineCategory, Medicine

@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_per_page = 20

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'shelf_location', 'quantity', 'expiry_date')
    list_filter = ('shelf_location', 'category')
    search_fields = ('name',)