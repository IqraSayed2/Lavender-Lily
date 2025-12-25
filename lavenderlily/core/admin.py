from django.contrib import admin
from django.utils import timezone
from django.db import models
from .models import AboutPage, ContactPage, ContactService, ContactMessage, Homepage, NewsletterSubscriber, Newsletter, SocialMedia

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("hero_title", "updated_at")

class ContactServiceInline(admin.TabularInline):
    model = ContactService
    extra = 3  # shows 3 by default

@admin.register(ContactPage)
class ContactPageAdmin(admin.ModelAdmin):
    inlines = [ContactServiceInline]
    list_display = ("title",)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_replied")
    list_filter = ("is_replied", "created_at")

@admin.register(Homepage)
class HomepageAdmin(admin.ModelAdmin):
    list_display = ("hero_title", "updated_at")
    fieldsets = (
        ('Hero Section', {
            'fields': ('hero_background', 'season_tag', 'hero_title', 'hero_subtitle', 'explore_button_text', 'watch_button_text', 'watch_button_url')
        }),
        ('Announcement Bar', {
            'fields': ('announcement_1', 'announcement_2', 'announcement_3')
        }),
        ('Featured Grid', {
            'fields': (
                ('featured_image_1', 'featured_label_1'),
                ('featured_image_2', 'featured_label_2'),
                ('featured_image_3', 'featured_label_3')
            )
        }),
        ('Newsletter Section', {
            'fields': ('newsletter_title', 'newsletter_subtitle', 'newsletter_button_text')
        }),
        ('Footer', {
            'fields': ('footer_brand_description', 'footer_newsletter_title', 'footer_newsletter_description', 'footer_newsletter_button')
        }),
    )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "subscribed_at", "unsubscribed_at")
    list_filter = ("is_active", "subscribed_at", "unsubscribed_at")
    search_fields = ("email",)
    readonly_fields = ("subscribed_at", "unsubscribed_at")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("subject", "status", "created_at", "scheduled_at", "sent_at", "sent_count")
    list_filter = ("status", "created_at", "sent_at")
    search_fields = ("subject", "content")
    readonly_fields = ("sent_at", "sent_count")
    fieldsets = (
        ('Newsletter Details', {
            'fields': ('subject', 'status', 'scheduled_at')
        }),
        ('Content', {
            'fields': ('content', 'html_content'),
            'classes': ('collapse',)
        }),
        ('Sending Info', {
            'fields': ('sent_at', 'sent_count'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # If status changed to 'sent', send the newsletter
        if obj.status == 'sent' and (not change or obj.status != Newsletter.objects.get(pk=obj.pk).status):
            from .utils import send_newsletter_to_all
            sent_count = send_newsletter_to_all(obj)
            obj.sent_count = sent_count
            obj.sent_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(SocialMedia)
class SocialMediaAdmin(admin.ModelAdmin):
    list_display = ("platform", "url", "is_active", "display_order", "get_icon_preview")
    list_filter = ("platform", "is_active")
    list_editable = ("is_active", "display_order")
    search_fields = ("platform", "url")
    ordering = ("display_order", "platform")
    list_per_page = 20

    fieldsets = (
        ('Social Media Details', {
            'fields': ('platform', 'url', 'is_active', 'display_order'),
            'description': 'Configure social media links that appear in the website footer.'
        }),
    )

    actions = ['activate_links', 'deactivate_links', 'reorder_display_order']

    def get_icon_preview(self, obj):
        """Display the icon for this social media platform"""
        return f'<i class="{obj.get_icon_class()}"></i> {obj.get_platform_display()}'
    get_icon_preview.short_description = 'Platform'
    get_icon_preview.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('display_order', 'platform')

    def activate_links(self, request, queryset):
        """Activate selected social media links"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Successfully activated {updated} social media link(s).')
    activate_links.short_description = 'Activate selected links'

    def deactivate_links(self, request, queryset):
        """Deactivate selected social media links"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Successfully deactivated {updated} social media link(s).')
    deactivate_links.short_description = 'Deactivate selected links'

    def reorder_display_order(self, request, queryset):
        """Reorder display order sequentially"""
        links = list(queryset.order_by('display_order', 'platform'))
        for i, link in enumerate(links, 1):
            link.display_order = i
            link.save()
        self.message_user(request, f'Successfully reordered {len(links)} social media link(s).')
    reorder_display_order.short_description = 'Reorder display order'

    def save_model(self, request, obj, form, change):
        """Custom save method to ensure unique display_order"""
        if not change:  # New object
            # Set default display_order to max + 1
            max_order = SocialMedia.objects.aggregate(max_order=models.Max('display_order'))['max_order'] or 0
            if not obj.display_order:
                obj.display_order = max_order + 1
        super().save_model(request, obj, form, change)