from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from core.models import UserAddress

class Order(models.Model):
    STATUS_CHOICES = (
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    payment_method = models.CharField(max_length=50, default="COD")
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    ziina_payment_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=True)
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True, blank=True)
    cancel_requested = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True)
    return_requested = models.BooleanField(default=False)
    return_reason = models.TextField(blank=True)
    cancel_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        # Check if status has changed
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                # Status has changed, send appropriate email
                from .utils import send_order_email
                if self.status == 'delivered':
                    send_order_email(self, 'delivered')
                elif self.status == 'cancelled' and not old_order.cancel_requested:
                    # Only send if not already sent during cancellation request
                    send_order_email(self, 'cancelled')

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity