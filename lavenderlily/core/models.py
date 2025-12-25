from django.db import models
from django.contrib.auth.models import User

class AboutPage(models.Model):
    hero_title = models.CharField(max_length=200)

    section_title = models.CharField(max_length=200)
    section_text = models.TextField()

    feature_title = models.CharField(max_length=200)
    feature_text_1 = models.TextField()
    feature_text_2 = models.TextField()
    feature_image = models.ImageField(upload_to='about/')

    promise_title = models.CharField(max_length=200)
    promise_text = models.TextField()

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "About Page Content"


class ContactPage(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField()

    def __str__(self):
        return "Contact Page"


class ContactService(models.Model):
    page = models.ForeignKey(
        ContactPage,
        related_name="services",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    timing = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200, default="Contact Form Message")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    

class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Homepage(models.Model):
    # Hero Section
    hero_background = models.ImageField(upload_to='homepage/')
    season_tag = models.CharField(max_length=100, default="SPRING / SUMMER 2024")
    hero_title = models.CharField(max_length=100, default="Ethereal")
    hero_subtitle = models.CharField(max_length=100, default="Elegance")
    explore_button_text = models.CharField(max_length=50, default="EXPLORE COLLECTION")
    watch_button_text = models.CharField(max_length=50, default="WATCH CAMPAIGN")
    watch_button_url = models.URLField(blank=True, null=True, help_text="URL for the campaign video (YouTube, Vimeo, etc.)")

    # Announcement Bar
    announcement_1 = models.CharField(max_length=200, default="Complimentary Shipping on Orders Over AED 200")
    announcement_2 = models.CharField(max_length=200, default="Sustainably Sourced Materials")
    announcement_3 = models.CharField(max_length=200, default="Handcrafted in UAE")

    # Featured Grid
    featured_image_1 = models.ImageField(upload_to='homepage/featured/')
    featured_label_1 = models.CharField(max_length=100, default="Style Inspiration")

    featured_image_2 = models.ImageField(upload_to='homepage/featured/')
    featured_label_2 = models.CharField(max_length=100, default="Fine Details")

    featured_image_3 = models.ImageField(upload_to='homepage/featured/')
    featured_label_3 = models.CharField(max_length=100, default="New Collection")

    # Newsletter Section
    newsletter_title = models.CharField(max_length=200, default="Join the Inner Circle")
    newsletter_subtitle = models.TextField(default="Subscribe to receive early access to new collections, exclusive events, and sustainable fashion news.")
    newsletter_button_text = models.CharField(max_length=50, default="Subscribe")

    # Auth Pages Images
    signup_image = models.ImageField(upload_to='homepage/auth/', blank=True, null=True)
    signin_image = models.ImageField(upload_to='homepage/auth/', blank=True, null=True)

    # Footer
    footer_brand_description = models.TextField(default="Timeless elegance inspired by nature. Sustainable fashion for the thoughtful wardrobe.")
    footer_newsletter_title = models.CharField(max_length=100, default="Stay in Bloom")
    footer_newsletter_description = models.TextField(default="Subscribe for new arrivals and exclusive offers.")
    footer_newsletter_button = models.CharField(max_length=50, default="Join")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Homepage Content"

    class Meta:
        verbose_name = "Homepage"
        verbose_name_plural = "Homepage"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"


class Newsletter(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    )

    subject = models.CharField(max_length=200)
    content = models.TextField()
    html_content = models.TextField(blank=True, help_text="HTML version of the newsletter")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_count = models.IntegerField(default=0)

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"
        ordering = ['-created_at']


class SocialMedia(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('pinterest', 'Pinterest'),
        ('snapchat', 'Snapchat'),
        ('whatsapp', 'WhatsApp'),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, unique=True)
    url = models.URLField(help_text="Full URL to your social media profile")
    is_active = models.BooleanField(default=True, help_text="Show this social media link in footer")
    display_order = models.PositiveIntegerField(default=0, help_text="Order to display (lower numbers first)")

    def __str__(self):
        return f"{self.get_platform_display()}"

    def get_icon_class(self):
        """Return the FontAwesome icon class for this platform"""
        icon_map = {
            'instagram': 'fab fa-instagram',
            'facebook': 'fab fa-facebook-f',
            'twitter': 'fab fa-twitter',
            'tiktok': 'fab fa-tiktok',
            'youtube': 'fab fa-youtube',
            'linkedin': 'fab fa-linkedin-in',
            'pinterest': 'fab fa-pinterest-p',
            'snapchat': 'fab fa-snapchat-ghost',
            'whatsapp': 'fab fa-whatsapp',
        }
        return icon_map.get(self.platform, 'fas fa-external-link-alt')

    class Meta:
        verbose_name = "Social Media Link"
        verbose_name_plural = "Social Media Links"
        ordering = ['display_order', 'platform']