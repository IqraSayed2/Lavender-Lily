from django.contrib import admin
from .models import Product, Review, Category, Color, Size

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "hex_code", "created_at")
    search_fields = ("name",)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order")
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id","name","category","color","price","sku")
    search_fields = ("name","category__name","sku")
    list_filter = ("category","color")
    fields = ("name","category","color","sizes","price","description","sku","material","care","image_main","image1","image2","image3","image4")
    readonly_fields = ("slug",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id","product","name","rating","created_at","approved")
    list_filter = ("approved","rating")
    search_fields = ("name","comment","product__name")
