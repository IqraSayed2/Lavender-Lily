from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Newsletter
from core.utils import send_newsletter_to_all


class Command(BaseCommand):
    help = 'Send scheduled newsletters to all active subscribers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--newsletter-id',
            type=int,
            help='Send a specific newsletter by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        newsletter_id = options.get('newsletter_id')
        dry_run = options.get('dry_run', False)

        if newsletter_id:
            # Send specific newsletter
            try:
                newsletter = Newsletter.objects.get(id=newsletter_id)
                self.send_single_newsletter(newsletter, dry_run)
            except Newsletter.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Newsletter with ID {newsletter_id} does not exist')
                )
        else:
            # Send all scheduled newsletters that are due
            scheduled_newsletters = Newsletter.objects.filter(
                status='scheduled',
                scheduled_at__lte=timezone.now()
            )

            if not scheduled_newsletters.exists():
                self.stdout.write('No scheduled newsletters to send.')
                return

            for newsletter in scheduled_newsletters:
                self.send_single_newsletter(newsletter, dry_run)

    def send_single_newsletter(self, newsletter, dry_run=False):
        self.stdout.write(
            self.style.SUCCESS(f'Processing newsletter: "{newsletter.subject}"')
        )

        if dry_run:
            # Count subscribers without sending
            from core.models import NewsletterSubscriber
            subscriber_count = NewsletterSubscriber.objects.filter(is_active=True).count()
            self.stdout.write(
                f'DRY RUN: Would send to {subscriber_count} subscribers'
            )
            return

        # Send the newsletter
        sent_count = send_newsletter_to_all(newsletter)

        # Update newsletter status
        newsletter.status = 'sent'
        newsletter.sent_at = timezone.now()
        newsletter.sent_count = sent_count
        newsletter.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent newsletter "{newsletter.subject}" to {sent_count} subscribers'
            )
        )