from django.contrib import admin
from django.utils import timezone
from .models import AboutPage, ContactPage, ContactService, ContactMessage, Homepage, NewsletterSubscriber, Newsletter

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