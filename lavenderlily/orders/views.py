from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import requests
import hmac
import hashlib
from .models import Order, OrderItem
from store.models import Product
from core.models import UserAddress
from cart.models import CartItem
from decimal import Decimal
import uuid
from .utils import send_order_email
from django.utils import timezone
from django.conf import settings

@login_required(login_url='signin')
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    buy_now = request.session.get("buy_now", False)

    products = []
    subtotal = 0

    for cart_item in cart_items:
        item_subtotal = cart_item.subtotal
        subtotal += item_subtotal
        products.append({
            "product": cart_item.product,
            "qty": cart_item.quantity,
            "subtotal": item_subtotal
        })

    # Calculate shipping and tax
    shipping = Decimal('0') if subtotal >= Decimal('500') else Decimal('50')  # Free shipping over AED 500
    tax = subtotal * Decimal('0.05')  # 5% VAT (UAE standard)
    total = subtotal + shipping + tax

    # Get user's default address or first address
    default_address = UserAddress.objects.filter(user=request.user, is_default=True).first()
    if not default_address:
        default_address = UserAddress.objects.filter(user=request.user).first()

    if request.method == "POST":
        # Check if address already exists
        existing_address = UserAddress.objects.filter(
            user=request.user,
            full_name=request.POST.get("full_name"),
            phone=request.POST.get("phone"),
            address_line=request.POST.get("address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            postal_code=request.POST.get("postal_code"),
            country=request.POST.get("country"),
        ).first()

        if existing_address:
            address = existing_address
        else:
            address = UserAddress.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                address_line=request.POST.get("address"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                postal_code=request.POST.get("postal_code"),
                country=request.POST.get("country"),
            )

        order = Order.objects.create(
            user=request.user,
            order_number=f"LL-{uuid.uuid4().hex[:8].upper()}",
            total_amount=total,
            payment_method=request.POST.get("payment_method", "COD"),
            is_paid=False,  # Will be updated after payment
            shipping_address=address
        )

        for item in products:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["qty"],
                price=item["product"].price
            )

        payment_method = request.POST.get("payment_method", "Fake Payment")

        # For fake payment, redirect to payment processing page
        return render(request, 'orders/payment.html', {
            'order': order,
            'payment_method': 'Fake Payment',
            'amount': int(total * 100),
            'currency': 'AED',
            'user': request.user,
            'customer_name': address.full_name,
            'customer_email': request.user.email,
            'customer_phone': address.phone,
            'callback_url': f"{request.scheme}://{request.get_host()}/orders/payment-callback/",
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
        })

    return render(request, "orders/checkout.html", {
        "cart_items": products,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
        "buy_now": buy_now,
        "default_address": default_address
    })


@login_required(login_url='signin')
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == "POST" and order.status == 'processing':
        order.cancel_requested = True
        order.cancel_reason = request.POST.get('reason', '')
        order.cancel_date = timezone.now()
        order.status = 'cancelled'
        order.save()
        messages.success(request, "Order cancellation requested successfully.")

        # Send order cancellation email
        send_order_email(order, 'cancelled')

    return redirect('order_detail', pk=pk)

@login_required
def return_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == "POST" and order.status == 'delivered':
        order.return_requested = True
        order.return_reason = request.POST.get('reason', '')
        order.return_date = timezone.now()
        order.status = 'returned'
        order.save()
        messages.success(request, "Return request submitted successfully.")
    return redirect('order_detail', pk=pk)


@login_required(login_url='signin')
def order_detail(request, pk):
    if request.user.is_staff:
        order = get_object_or_404(Order, pk=pk)
    else:
        order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


def payment_status(request, status):
    """Handle payment status display"""
    return render(request, "orders/payment_status.html", {"status": status})


@csrf_exempt
def payment_callback(request):
    """Handle fake payment completion"""
    if request.method == 'POST':
        # Get order number from POST data
        order_number = request.POST.get('order_number')
        
        if order_number:
            try:
                order = Order.objects.get(order_number=order_number)
                
                # Mark as paid
                order.is_paid = True
                order.status = 'processing'
                order.save()

                # Clear cart from database
                CartItem.objects.filter(user=order.user).delete()
                if "buy_now" in request.session:
                    del request.session["buy_now"]

                # Send order confirmation email
                send_order_email(order, 'confirmation')

                return redirect("payment_status", status="success")

            except Order.DoesNotExist:
                messages.error(request, "Order not found")
                return redirect("payment_status", status="failed")
        else:
            messages.error(request, "Invalid payment callback data")
            return redirect("payment_status", status="failed")

    else:
        # Handle GET request (payment cancelled or failed)
        return redirect("payment_status", status="failed")
