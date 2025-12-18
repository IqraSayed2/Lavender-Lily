from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from .models import CartItem

@login_required(login_url='signin')
def cart_page(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    products = []
    subtotal = 0

    for cart_item in cart_items:
        subtotal += cart_item.subtotal
        products.append({
            "product": cart_item.product,
            "qty": cart_item.quantity,
            "subtotal": cart_item.subtotal,
            "cart_item_id": cart_item.id
        })

    shipping = Decimal('0') if subtotal >= Decimal('200') else Decimal('20')  # Free shipping over AED 200
    tax = subtotal * Decimal('0.05')  # 5% VAT (UAE standard)
    total = subtotal + shipping + tax

    return render(request, "cart/cart.html", {
        "cart_items": products,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total
    })


@login_required(login_url='signin')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    qty = int(request.POST.get("quantity", 1))

    if request.POST.get("buy_now"):
        # For Buy Now, clear cart and add only this item
        CartItem.objects.filter(user=request.user).delete()  # Clear existing cart
        CartItem.objects.create(user=request.user, product=product, quantity=qty)
        request.session["buy_now"] = True  # Flag to indicate buy now purchase
        return redirect("checkout")
    else:
        # Normal add to cart - update or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 0}
        )
        cart_item.quantity += qty
        cart_item.save()
        messages.success(request, f"Added {product.name} (x{qty}) to cart.")
        return redirect(request.POST.get("next", product.get_absolute_url()))


@login_required(login_url='signin')
def update_cart(request):
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("qty_"):
                cart_item_id = key.split("_", 1)[1]
                try:
                    qty = int(value)
                    if qty <= 0:
                        CartItem.objects.filter(id=cart_item_id, user=request.user).delete()
                    else:
                        CartItem.objects.filter(id=cart_item_id, user=request.user).update(quantity=qty)
                except (ValueError, CartItem.DoesNotExist):
                    pass
        messages.success(request, "Cart updated successfully.")
        return redirect("cart")


@login_required(login_url='signin')
def remove_from_cart(request, cart_item_id):
    CartItem.objects.filter(id=cart_item_id, user=request.user).delete()
    messages.info(request, "Item removed from cart.")
    return redirect("cart")
