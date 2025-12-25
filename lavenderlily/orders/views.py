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

        if payment_method in ["Razorpay", "ApplePay", "GooglePay"]:
            # Initialize Razorpay client for card payments, Apple Pay, and Google Pay
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

        elif payment_method == "Ziina":
            # Ziina payment processing
            try:
                # Store Ziina order details (you'll need to implement Ziina API integration)
                order.payment_method = 'Ziina'
                order.save()

                # Prepare context for Ziina payment
                context = {
                    'order': order,
                    'payment_method': 'Ziina',
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
                }

                return render(request, 'orders/payment.html', context)
            except Exception as e:
                messages.error(request, f"Ziina payment setup failed: {str(e)}")
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
def create_ziina_payment(request):
    """Create Ziina payment session (Test Mode Implementation)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_number = data.get('order_number')
            amount = data.get('amount')
            currency = data.get('currency', 'AED')

            # Get the order
            order = Order.objects.get(order_number=order_number, payment_method='Ziina')

            # Production Ziina API integration
            try:
                # Prepare Ziina payment request
                ziina_payload = {
                    'merchant_id': settings.ZIINA_MERCHANT_ID,
                    'amount': str(amount),  # Amount in cents (e.g., 1000 = 10.00 AED)
                    'currency': currency,
                    'order_id': order_number,
                    'customer_email': order.user.email,
                    'customer_name': f"{order.user.first_name} {order.user.last_name}".strip(),
                    'customer_phone': order.shipping_address.phone if order.shipping_address else '',
                    'description': f'Order {order_number}',
                    'success_url': f"{request.scheme}://{request.get_host()}/orders/payment-callback/",
                    'cancel_url': f"{request.scheme}://{request.get_host()}/orders/payment-callback/?ziina_order_id={order_number}&ziina_status=cancelled",
                    'webhook_url': f"{request.scheme}://{request.get_host()}/orders/ziina-webhook/",
                }

                # Generate signature for Ziina API request
                signature_string = '&'.join([f"{k}={v}" for k, v in sorted(ziina_payload.items())])
                signature = hmac.new(
                    settings.ZIINA_API_SECRET.encode(),
                    signature_string.encode(),
                    hashlib.sha256
                ).hexdigest()

                # Add signature to payload
                ziina_payload['signature'] = signature

                # Make API call to Ziina
                headers = {
                    'Authorization': f'Bearer {settings.ZIINA_API_KEY}',
                    'Content-Type': 'application/json'
                }

                response = requests.post(
                    f"{settings.ZIINA_BASE_URL}/v1/payments/create",
                    json=ziina_payload,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    ziina_response = response.json()

                    # Store Ziina payment ID in order
                    order.ziina_payment_id = ziina_response.get('payment_id')
                    order.save()

                    return JsonResponse({
                        'success': True,
                        'payment_url': ziina_response.get('payment_url'),
                        'payment_id': ziina_response.get('payment_id')
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Ziina API error: {response.text}'
                    })

            except requests.RequestException as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Network error: {str(e)}'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Payment creation failed: {str(e)}'
                })

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def payment_callback(request):
    """Handle payment completion for both Razorpay and Ziina"""
    if request.method == 'POST':
        # Check if this is a Razorpay payment
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        if razorpay_payment_id and razorpay_order_id and razorpay_signature:
            # Handle Razorpay payment
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
            # Check if this is a Ziina payment callback
            ziina_payment_id = request.POST.get('ziina_payment_id')
            ziina_order_id = request.POST.get('ziina_order_id')
            ziina_status = request.POST.get('ziina_status')

            if ziina_payment_id and ziina_order_id:
                # Handle Ziina payment
                try:
                    # Get the order by order number (since Ziina might use different ID format)
                    order = Order.objects.get(order_number=ziina_order_id, payment_method='Ziina')

                    # Verify Ziina payment with API
                    headers = {
                        'Authorization': f'Bearer {settings.ZIINA_API_KEY}',
                        'Content-Type': 'application/json'
                    }

                    verify_response = requests.get(
                        f"{settings.ZIINA_BASE_URL}/v1/payments/{ziina_payment_id}",
                        headers=headers,
                        timeout=30
                    )

                    if verify_response.status_code == 200:
                        payment_data = verify_response.json()

                        # Verify payment signature
                        signature_string = '&'.join([f"{k}={v}" for k, v in sorted(payment_data.items()) if k != 'signature'])
                        expected_signature = hmac.new(
                            settings.ZIINA_API_SECRET.encode(),
                            signature_string.encode(),
                            hashlib.sha256
                        ).hexdigest()

                        if payment_data.get('signature') == expected_signature:
                            if payment_data.get('status') == 'completed':
                                # Payment successful
                                order.is_paid = True
                                order.ziina_payment_id = ziina_payment_id
                                order.status = 'processing'
                                order.save()

                                # Clear cart from database
                                CartItem.objects.filter(user=order.user).delete()
                                if "buy_now" in request.session:
                                    del request.session["buy_now"]

                                # Send order confirmation email
                                send_order_email(order, 'confirmation')

                                return redirect("payment_status", status="success")
                            else:
                                # Payment failed or pending
                                order.status = 'cancelled'
                                order.save()
                                return redirect("payment_status", status="failed")
                        else:
                            # Invalid signature
                            return redirect("payment_status", status="failed")
                    else:
                        # API verification failed
                        return redirect("payment_status", status="failed")

                except Order.DoesNotExist:
                    messages.error(request, "Order not found")
                    return redirect("payment_status", status="failed")
                except Exception as e:
                    messages.error(request, f"Ziina payment processing failed: {str(e)}")
                    return redirect("payment_status", status="failed")
            else:
                messages.error(request, "Invalid payment callback data")
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

        # Handle Ziina cancellation (you might need to adjust based on Ziina's callback format)
        ziina_order_id = request.GET.get('ziina_order_id')
        if ziina_order_id:
            try:
                order = Order.objects.get(order_number=ziina_order_id, payment_method='Ziina')
                order.status = 'cancelled'
                order.save()
            except Order.DoesNotExist:
                pass

        return redirect("payment_status", status="failed")


@csrf_exempt
def ziina_webhook(request):
    """Handle Ziina webhook notifications for payment status updates"""
    if request.method == 'POST':
        try:
            # Get webhook data
            webhook_data = json.loads(request.body)

            # Verify webhook signature
            signature = request.headers.get('X-Ziina-Signature')
            if not signature:
                return JsonResponse({'status': 'error', 'message': 'Missing signature'}, status=400)

            # Create signature string from webhook data
            signature_string = json.dumps(webhook_data, sort_keys=True)
            expected_signature = hmac.new(
                settings.ZIINA_API_SECRET.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).hexdigest()

            if signature != expected_signature:
                return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

            # Process webhook data
            payment_id = webhook_data.get('payment_id')
            order_number = webhook_data.get('order_id')
            payment_status = webhook_data.get('status')

            if payment_id and order_number:
                try:
                    order = Order.objects.get(order_number=order_number, payment_method='Ziina')

                    if payment_status == 'completed' and not order.is_paid:
                        # Payment completed
                        order.is_paid = True
                        order.ziina_payment_id = payment_id
                        order.status = 'processing'
                        order.save()

                        # Clear cart from database
                        CartItem.objects.filter(user=order.user).delete()
                        if "buy_now" in request.session:
                            del request.session["buy_now"]

                        # Send order confirmation email
                        send_order_email(order, 'confirmation')

                    elif payment_status in ['failed', 'cancelled']:
                        # Payment failed
                        order.status = 'cancelled'
                        order.save()

                    return JsonResponse({'status': 'success'})

                except Order.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

            return JsonResponse({'status': 'error', 'message': 'Invalid webhook data'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
