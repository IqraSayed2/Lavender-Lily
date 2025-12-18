from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_amount', 'status', 'cancel_requested', 'return_requested', 'created_at')
    list_filter = ('status', 'cancel_requested', 'return_requested', 'payment_method')
    search_fields = ('order_number', 'user__username')
    readonly_fields = ('order_number', 'created_at', 'cancel_date', 'return_date')
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total_amount', 'payment_method', 'is_paid', 'created_at')
        }),
        ('Shipping', {
            'fields': ('shipping_address',)
        }),
        ('Cancellation', {
            'fields': ('cancel_requested', 'cancel_reason', 'cancel_date'),
            'classes': ('collapse',)
        }),
        ('Return', {
            'fields': ('return_requested', 'return_reason', 'return_date'),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderItemInline]
