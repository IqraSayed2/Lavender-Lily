from django.db import models
from cart.models import CartItem, WishlistItem
from .models import SocialMedia

def cart_wishlist_counts(request):
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).aggregate(
            total=models.Sum('quantity'))['total'] or 0
        wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    else:
        cart_count = 0
        wishlist_count = 0

    # Get active social media links for footer
    social_media_links = SocialMedia.objects.filter(is_active=True).order_by('display_order')

    return {
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
        "social_media_links": social_media_links
    }
