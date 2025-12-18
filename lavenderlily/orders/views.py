from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Order, OrderItem
from store.models import Product
from core.models import UserAddress
from cart.models import CartItem
from decimal import Decimal
import uuid
from .utils import send_order_email
from django.utils import timezone
from django.conf import settings
import razorpay

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

        payment_method = request.POST.get("payment_method", "COD")

        if payment_method == "Razorpay":
            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Create Razorpay order
            try:
                razorpay_order = client.order.create({
                    'amount': int(total * 100),  # Amount in paisa (multiply by 100)
                    'currency': settings.RAZORPAY_CURRENCY,
                    'payment_capture': '1',  # Auto capture
                    'notes': {
                        'order_number': order.order_number,
                        'customer_name': address.full_name,
                        'customer_email': request.user.email,
                        'customer_phone': address.phone,
                    }
                })

                # Store Razorpay order ID in the order
                order.razorpay_order_id = razorpay_order['id']
                order.save()

                # Prepare context for payment
                context = {
                    'order': order,
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'amount': int(total * 100),
                    'currency': 'AED',  # Display currency
                    'user': request.user,
                    'customer_name': address.full_name,
                    'customer_email': request.user.email,
                    'customer_phone': address.phone,
                    'callback_url': f"{request.scheme}://{request.get_host()}/orders/payment-callback/",
                    'subtotal': subtotal,
                    'shipping': shipping,
                    'tax': tax,
                }

                return render(request, 'orders/payment.html', context)
            except Exception as e:
                messages.error(request, f"Payment setup failed: {str(e)}")
                return redirect('checkout')
        else:
            # COD - mark as paid immediately
            order.is_paid = True
            order.save()
            request.session["cart"] = {}
            if "buy_now" in request.session:
                del request.session["buy_now"]
            messages.success(request, "Order placed successfully!")

            # Send order confirmation email
            send_order_email(order, 'confirmation')

            return redirect("profile")

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
    """Handle Razorpay payment completion"""
    if request.method == 'POST':
        # Get payment details from Razorpay
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # Verify the payment signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Payment successful
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.is_paid = True
            order.razorpay_payment_id = razorpay_payment_id
            order.status = 'processing'  # Move to processing after payment
            order.save()

            # Clear cart from database
            CartItem.objects.filter(user=order.user).delete()
            if "buy_now" in request.session:
                del request.session["buy_now"]

            # Send order confirmation email
            send_order_email(order, 'confirmation')

            return redirect("payment_status", status="success")

        except razorpay.errors.SignatureVerificationError:
            # Payment verification failed
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.status = 'cancelled'
                order.save()
            except Order.DoesNotExist:
                pass
            return redirect("payment_status", status="failed")

        except Exception as e:
            messages.error(request, f"Payment processing failed: {str(e)}")
            return redirect("payment_status", status="failed")
    else:
        # Handle GET request (payment cancelled or failed)
        razorpay_order_id = request.GET.get('razorpay_order_id')
        if razorpay_order_id:
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.status = 'cancelled'
                order.save()
            except Order.DoesNotExist:
                pass

        return redirect("payment_status", status="failed")
