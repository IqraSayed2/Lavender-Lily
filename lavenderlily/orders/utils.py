from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order

def send_order_email(order, email_type):
    """
    Send email notification for order status changes
    email_type: 'confirmation', 'cancelled', 'delivered'
    """
    subject_templates = {
        'confirmation': f'Order Confirmation - {order.order_number}',
        'cancelled': f'Order Cancelled - {order.order_number}',
        'delivered': f'Order Delivered - {order.order_number}'
    }

    template_names = {
        'confirmation': 'emails/order_confirmation.html',
        'cancelled': 'emails/order_cancelled.html',
        'delivered': 'emails/order_delivered.html'
    }

    subject = subject_templates.get(email_type)
    template_name = template_names.get(email_type)

    if not subject or not template_name:
        return False

    # Render email content
    context = {'order': order}
    html_message = render_to_string(template_name, context)
    plain_message = f"""
    Order {email_type.title()} - {order.order_number}

    Order Details:
    Order Number: {order.order_number}
    Total Amount: AED {order.total_amount}
    Status: {order.get_status_display()}

    Thank you for shopping with Lavender Lily!
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log the error in production
        print(f"Failed to send {email_type} email for order {order.order_number}: {e}")
        return False