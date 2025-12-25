from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Review, Category, Color, Size

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "cover_image_thumbnail", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "slug", "description", "cover_image")
    readonly_fields = ("slug",)

    def cover_image_thumbnail(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.cover_image.url)
        return "No image"
    cover_image_thumbnail.short_description = "Cover Image"

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
