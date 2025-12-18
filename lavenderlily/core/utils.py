from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import NewsletterSubscriber, Newsletter
import logging

logger = logging.getLogger(__name__)

def send_newsletter_to_all(newsletter):
    """
    Send newsletter to all active subscribers
    Returns the number of emails sent successfully
    """
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    sent_count = 0

    for subscriber in subscribers:
        try:
            # Create email message
            email = EmailMessage(
                subject=newsletter.subject,
                body=newsletter.html_content if newsletter.html_content else newsletter.content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscriber.email],
            )

            # If HTML content exists, set it as HTML alternative
            if newsletter.html_content:
                email.content_subtype = "html"
                email.body = newsletter.html_content
            else:
                # Plain text fallback
                email.body = newsletter.content

            # Send the email
            email.send(fail_silently=False)
            sent_count += 1

        except Exception as e:
            logger.error(f"Failed to send newsletter to {subscriber.email}: {e}")
            continue

    return sent_count


def send_newsletter_email(email, email_type):
    """Send newsletter-related emails"""
    subject_templates = {
        'welcome': 'Welcome to Lavender Lily Newsletter!',
        'welcome_back': 'Welcome back to Lavender Lily Newsletter!'
    }

    message_templates = {
        'welcome': f"""
        Welcome to the Lavender Lily family! 🌸

        Thank you for subscribing to our newsletter. You'll be the first to know about:

        ✨ New collection launches
        🎨 Exclusive behind-the-scenes content
        🌿 Sustainable fashion tips
        💝 Special offers and events

        Stay elegant,
        The Lavender Lily Team
        """,
        'welcome_back': f"""
        Welcome back to Lavender Lily! 🌸

        We're thrilled to have you back in our community. You'll continue to receive:

        ✨ New collection launches
        🎨 Exclusive behind-the-scenes content
        🌿 Sustainable fashion tips
        💝 Special offers and events

        Stay elegant,
        The Lavender Lily Team
        """
    }

    subject = subject_templates.get(email_type)
    message = message_templates.get(email_type)

    if subject and message:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send {email_type} email to {email}: {e}")