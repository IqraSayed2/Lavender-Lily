from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Upload a cover image for this category (recommended size: 300x350px for best display on homepage)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Color(models.Model):
    name = models.CharField(max_length=30, unique=True)
    hex_code = models.CharField(max_length=7, blank=True, help_text="Hex color code (e.g., #FF0000)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.hex_code and self.name:
            # Set default hex codes for common colors
            color_hex_map = {
                'Lavender': '#E6E6FA',
                'Purple': '#800080',
                'Dark': '#000000',
                'Beige': '#F5F5DC',
                'White': '#FFFFFF',
                'Black': '#000000',
                'Red': '#FF0000',
                'Blue': '#0000FF',
                'Green': '#008000',
                'Yellow': '#FFFF00',
                'Pink': '#FFC0CB',
                'Gray': '#808080',
                'Brown': '#A52A2A',
                'Orange': '#FFA500',
                'Navy': '#000080',
            }
            self.hex_code = color_hex_map.get(self.name, '')
        elif self.hex_code and not self.hex_code.startswith('#'):
            self.hex_code = '#' + self.hex_code.upper()
        super().save(*args, **kwargs)

class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Order for display")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    variant_group = models.CharField(max_length=255, blank=True, help_text="Group products with same design but different colors/sizes")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    sizes = models.ManyToManyField(Size, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, blank=True)
    material = models.CharField(max_length=255, blank=True)
    care = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # images
    image_main = models.ImageField(upload_to="products/")
    image1 = models.ImageField(upload_to="products/", blank=True, null=True)
    image2 = models.ImageField(upload_to="products/", blank=True, null=True)
    image3 = models.ImageField(upload_to="products/", blank=True, null=True)
    image4 = models.ImageField(upload_to="products/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.variant_group:
            self.variant_group = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.pk])


class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=120)  # author name (for anonymous)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True)  # set False if you want moderation

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review {self.rating} by {self.name} for {self.product.name}"
