from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import AboutPage, ContactPage, ContactService, ContactMessage, UserAddress, Homepage, NewsletterSubscriber, Newsletter
from django.core.mail import send_mail
from django.conf import settings
from orders.models import Order
from store.models import Product, Category, Color
from cart.models import WishlistItem
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .utils import send_newsletter_email

def home(request):
    # Get featured products for homepage carousel
    # Show latest 6 products as "New Arrivals"
    products = Product.objects.all().order_by('-created_at')[:6]

    # Get all categories for the shop by category section
    categories = Category.objects.all().order_by('name')

    # Get homepage content
    homepage = Homepage.objects.first()

    return render(request, 'core/index.html', {
        'products': products,
        'categories': categories,
        'homepage': homepage
    })

def about(request):
    about = AboutPage.objects.first()
    return render(request, "core/about.html", {"about": about})

def contact(request):
    contact_page = ContactPage.objects.first()

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Save message
        contact_msg = ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # EMAIL TO ADMIN
        admin_subject = f"New Contact Message from {name}"
        admin_message = f"""
        New message received on Lavender Lily website.

        Name: {name}
        Email: {email}

        Message:
        {message}
        """

        send_mail(
            admin_subject,
            admin_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        # AUTO-REPLY TO USER
        user_subject = "We received your message – Lavender Lily"
        user_message = f"""
        Hi {name},

        Thank you for contacting Lavender Lily 🤍

        We have received your message and our team will get back to you shortly.

        Your Message:
        "{message}"

        Warm regards,
        Lavender Lily Team
        """

        send_mail(
            user_subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    return render(request, "core/contact.html", {
        "contact": contact_page
    })


def signup_page(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Validate required fields
        if not all([first_name, last_name, email, username, password]):
            messages.error(request, "All fields are required.")
            return redirect("signup")

        # Check if email already exists (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            messages.success(request, "Account created successfully. Please sign in.")
            return redirect("signin")
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect("signup")

    return render(request, "core/auth.html", {"mode": "signup", "homepage": Homepage.objects.first()})


def signin_page(request):
    if request.method == "POST":
        email_or_username = request.POST.get("email")  # The field is named 'email' but can be username
        password = request.POST.get("password")

        user = None

        # Check if input contains @ (likely email) or not (username)
        if '@' in email_or_username:
            # Treat as email
            try:
                user_obj = User.objects.get(email__iexact=email_or_username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            # Treat as username
            user = authenticate(username=email_or_username, password=password)

        if user is None:
            messages.error(request, "Invalid email/username or password.")
            return redirect("signin")

        login(request, user)
        messages.success(request, "Logged in successfully!")
        return redirect("profile")

    return render(request, "core/auth.html", {"mode": "signin", "homepage": Homepage.objects.first()})


def forgot_password_view(request):
    return render(request, "core/password_reset_combined.html", {"step": "request"})


def logout_user(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("signin")


@login_required(login_url='signin')
def profile(request):
    user = request.user

    # SAVE ACCOUNT DETAILS
    if request.method == "POST" and request.POST.get("update_profile"):
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.save()

        # Handle address
        address, created = UserAddress.objects.get_or_create(
            user=user,
            defaults={
                'full_name': request.POST.get("full_name", ""),
                'phone': request.POST.get("phone", ""),
                'address_line': request.POST.get("address_line", ""),
                'city': request.POST.get("city", ""),
                'state': request.POST.get("state", ""),
                'postal_code': request.POST.get("postal_code", ""),
                'country': request.POST.get("country", ""),
            }
        )
        if not created:
            address.full_name = request.POST.get("full_name", address.full_name)
            address.phone = request.POST.get("phone", address.phone)
            address.address_line = request.POST.get("address_line", address.address_line)
            address.city = request.POST.get("city", address.city)
            address.state = request.POST.get("state", address.state)
            address.postal_code = request.POST.get("postal_code", address.postal_code)
            address.country = request.POST.get("country", address.country)
            address.save()

        messages.success(request, "Profile updated successfully!")

    addresses = user.addresses.all()
    orders = Order.objects.filter(user=user).order_by("-created_at")

    wishlist_products = Product.objects.filter(wishlistitem__user=user)

    return render(request, "core/profile.html", {
        "addresses": addresses,
        "orders": orders,
        "wishlist_products": wishlist_products,
    })


@login_required(login_url='signin')
def remove_address(request, address_id):
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address removed successfully.")
    return redirect("profile")


@login_required(login_url='signin')
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX or form submission"""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "message": "Email is required."})
            messages.error(request, "Email is required.")
            return redirect("home")

        # Check if email is already subscribed
        existing_subscriber = NewsletterSubscriber.objects.filter(email=email).first()

        if existing_subscriber:
            if existing_subscriber.is_active:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "message": "This email is already subscribed."})
                messages.warning(request, "This email is already subscribed.")
                return redirect("home")
            else:
                # Reactivate subscription
                existing_subscriber.is_active = True
                existing_subscriber.unsubscribed_at = None
                existing_subscriber.save()

                # Send welcome back email
                send_newsletter_email(email, "welcome_back")

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": True, "message": "Welcome back! You're subscribed again."})
                messages.success(request, "Welcome back! You're subscribed again.")
                return redirect("home")
        else:
            # Create new subscription
            subscriber = NewsletterSubscriber.objects.create(email=email)

            # Send welcome email
            send_newsletter_email(email, "welcome")

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Thank you for subscribing!"})
            messages.success(request, "Thank you for subscribing!")
            return redirect("home")

    # GET request - redirect to home
    return redirect("home")


@login_required(login_url='signin')
def newsletter_management(request):
    """Admin view for managing newsletters"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect("home")

    newsletters = Newsletter.objects.all().order_by('-created_at')
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    subscriber_count = subscribers.count()

    if request.method == "POST":
        if 'create_newsletter' in request.POST:
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            html_content = request.POST.get('html_content', '')

            if subject and content:
                newsletter = Newsletter.objects.create(
                    subject=subject,
                    content=content,
                    html_content=html_content,
                    status='draft'
                )
                messages.success(request, f"Newsletter '{subject}' created successfully!")
                return redirect('newsletter_management')
            else:
                messages.error(request, "Subject and content are required.")

        elif 'send_newsletter' in request.POST:
            newsletter_id = request.POST.get('newsletter_id')
            try:
                newsletter = Newsletter.objects.get(id=newsletter_id)
                if newsletter.status == 'draft':
                    from .utils import send_newsletter_to_all
                    sent_count = send_newsletter_to_all(newsletter)
                    newsletter.status = 'sent'
                    newsletter.sent_at = timezone.now()
                    newsletter.sent_count = sent_count
                    newsletter.save()
                    messages.success(request, f"Newsletter sent to {sent_count} subscribers!")
                else:
                    messages.warning(request, "This newsletter has already been sent.")
            except Newsletter.DoesNotExist:
                messages.error(request, "Newsletter not found.")

    return render(request, "admin/newsletter_management.html", {
        "newsletters": newsletters,
        "subscriber_count": subscriber_count,
    })


@login_required(login_url='signin')
def admin_dashboard(request):
    """Custom admin dashboard for managing the site"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect("home")

    # Product statistics
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_colors = Color.objects.count()

    # Calculate product growth percentage
    now = timezone.now()
    this_month = now.replace(day=1)
    last_month = this_month - relativedelta(months=1)
    last_last_month = last_month - relativedelta(months=1)

    products_this_month = Product.objects.filter(created_at__gte=this_month).count()
    products_last_month = Product.objects.filter(created_at__gte=last_month, created_at__lt=this_month).count()

    if products_last_month > 0:
        product_growth_percentage = ((products_this_month - products_last_month) / products_last_month) * 100
    else:
        product_growth_percentage = 0 if products_this_month == 0 else 100

    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()

    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    # Newsletter statistics
    total_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    total_newsletters = Newsletter.objects.count()
    sent_newsletters = Newsletter.objects.filter(status='sent').count()

    # Contact messages
    unread_messages = ContactMessage.objects.filter(is_replied=False).count()
    recent_messages = ContactMessage.objects.order_by('-created_at')[:5]

    # User statistics
    from django.contrib.auth.models import User
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_colors': total_colors,
        'product_growth_percentage': product_growth_percentage,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'recent_orders': recent_orders,
        'total_subscribers': total_subscribers,
        'total_newsletters': total_newsletters,
        'sent_newsletters': sent_newsletters,
        'unread_messages': unread_messages,
        'recent_messages': recent_messages,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
    }

    return render(request, "admin/admin_dashboard.html", context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_orders(request):
    """Custom order management page"""
    orders = Order.objects.all().order_by('-created_at')

    # Search functionality
    q = request.GET.get('q')
    if q:
        orders = orders.filter(Q(order_number__icontains=q) | Q(user__username__icontains=q) | Q(user__email__icontains=q))

    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'query_params': request.GET.copy(),
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin/manage_orders.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
@require_POST
def update_order_status(request, pk):
    """Update order status"""
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')

    if new_status in dict(Order.STATUS_CHOICES):
        old_status = order.status
        order.status = new_status
        order.save()

        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Order {order.order_number} status updated to {order.get_status_display()}.'
            })
        else:
            messages.success(request, f'Order {order.order_number} status updated to {order.get_status_display()}.')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Invalid status.'
            })
        else:
            messages.error(request, 'Invalid status.')

    return redirect('manage_orders')


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_users(request):
    """Custom user management page"""
    users = User.objects.all().order_by('-date_joined')

    # Search functionality
    q = request.GET.get('q')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))

    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active is not None:
        users = users.filter(is_active=is_active == '1')

    # Filter by staff status
    is_staff = request.GET.get('is_staff')
    if is_staff is not None:
        users = users.filter(is_staff=is_staff == '1')

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'query_params': request.GET.copy(),
    }
    return render(request, 'admin/manage_users.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
@require_POST
def update_user_status(request, pk):
    """Update user active/staff status"""
    user = get_object_or_404(User, pk=pk)
    action = request.POST.get('action')

    if action == 'toggle_active':
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f'User {user.username} has been {status}.')

    elif action == 'toggle_staff':
        user.is_staff = not user.is_staff
        user.save()
        status = "granted" if user.is_staff else "revoked"
        messages.success(request, f'Staff status has been {status} for user {user.username}.')

    return redirect('manage_users')


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_messages(request):
    """Custom contact messages management page"""
    if request.method == "POST":
        if 'delete_message' in request.POST:
            message_id = request.POST.get('delete_message')
            try:
                message = ContactMessage.objects.get(id=message_id)
                subject = message.subject
                message.delete()
                messages.success(request, f'Message "{subject}" deleted successfully.')
            except ContactMessage.DoesNotExist:
                messages.error(request, "Message not found.")
            return redirect('manage_messages')
    
    messages_obj = ContactMessage.objects.all().order_by('-created_at')

    # Filter by replied status
    replied = request.GET.get('replied')
    if replied is not None:
        messages_obj = messages_obj.filter(is_replied=replied == '1')

    # Search functionality
    q = request.GET.get('q')
    if q:
        messages_obj = messages_obj.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))

    # Pagination
    paginator = Paginator(messages_obj, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get specific message if requested
    message_id = request.GET.get('message')
    selected_message = None
    if message_id:
        try:
            selected_message = ContactMessage.objects.get(pk=message_id)
        except ContactMessage.DoesNotExist:
            pass

    context = {
        'messages': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'query_params': request.GET.copy(),
        'selected_message': selected_message,
    }
    return render(request, 'admin/manage_messages.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
@require_POST
def reply_to_message(request, pk):
    """Send reply to message and mark as replied"""
    message = get_object_or_404(ContactMessage, pk=pk)
    
    subject = request.POST.get('subject')
    reply_message = request.POST.get('message')
    
    if subject and reply_message:
        # Send email reply
        try:
            send_mail(
                subject,
                reply_message,
                settings.DEFAULT_FROM_EMAIL,
                [message.email],
                fail_silently=False,
            )
            
            # Mark message as replied
            message.is_replied = True
            message.replied_at = timezone.now()
            message.save()
            
            messages.success(request, f'Reply sent successfully to {message.name}.')
        except Exception as e:
            messages.error(request, f'Failed to send reply: {str(e)}')
    else:
        messages.error(request, 'Subject and message are required.')
    
    return redirect('manage_messages')


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def message_detail(request, pk):
    """Return message details as JSON for AJAX requests"""
    message = get_object_or_404(ContactMessage, pk=pk)
    
    # Mark as read if not already read
    if not message.is_read:
        message.is_read = True
        message.save()
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'name': message.name,
            'email': message.email,
            'subject': message.subject,
            'message': message.message,
            'created_at': message.created_at.strftime('%B %d, %Y at %H:%M'),
            'is_read': message.is_read,
            'is_replied': message.is_replied,
            'replied_at': message.replied_at.strftime('%B %d, %Y at %H:%M') if message.replied_at else None,
        }
    })


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
@require_POST
def delete_message(request, pk):
    """Delete a contact message"""
    message = get_object_or_404(ContactMessage, pk=pk)
    message_name = message.subject
    message.delete()
    
    messages.success(request, f'Message "{message_name}" deleted successfully.')
    return redirect('manage_messages')


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_homepage(request):
    """Custom homepage management page"""
    homepage = Homepage.objects.first()
    if not homepage:
        homepage = Homepage.objects.create()

    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        # Update homepage fields
        homepage.hero_background = request.FILES.get('hero_background') or homepage.hero_background
        homepage.season_tag = request.POST.get('season_tag', homepage.season_tag)
        homepage.hero_title = request.POST.get('hero_title', homepage.hero_title)
        homepage.hero_subtitle = request.POST.get('hero_subtitle', homepage.hero_subtitle)
        homepage.explore_button_text = request.POST.get('explore_button_text', homepage.explore_button_text)
        homepage.watch_button_text = request.POST.get('watch_button_text', homepage.watch_button_text)
        homepage.watch_button_url = request.POST.get('watch_button_url', homepage.watch_button_url)

        # Announcement bar
        homepage.announcement_1 = request.POST.get('announcement_1', homepage.announcement_1)
        homepage.announcement_2 = request.POST.get('announcement_2', homepage.announcement_2)
        homepage.announcement_3 = request.POST.get('announcement_3', homepage.announcement_3)

        # Newsletter section
        homepage.newsletter_title = request.POST.get('newsletter_title', homepage.newsletter_title)
        homepage.newsletter_subtitle = request.POST.get('newsletter_subtitle', homepage.newsletter_subtitle)
        homepage.newsletter_button_text = request.POST.get('newsletter_button_text', homepage.newsletter_button_text)

        # Footer
        homepage.footer_brand_description = request.POST.get('footer_brand_description', homepage.footer_brand_description)
        homepage.footer_newsletter_title = request.POST.get('footer_newsletter_title', homepage.footer_newsletter_title)
        homepage.footer_newsletter_description = request.POST.get('footer_newsletter_description', homepage.footer_newsletter_description)
        homepage.footer_newsletter_button = request.POST.get('footer_newsletter_button', homepage.footer_newsletter_button)

        homepage.save()

        # Handle category cover images
        for category in categories:
            cover_image_key = f'category_cover_{category.id}'
            if cover_image_key in request.FILES:
                category.cover_image = request.FILES[cover_image_key]
                category.save()

        messages.success(request, 'Homepage and category images have been updated successfully.')
        return redirect('manage_homepage')

    context = {
        'homepage': homepage,
        'categories': categories,
    }
    return render(request, 'admin/manage_homepage.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_contact_page(request):
    """Custom contact page management page"""
    contact_page = ContactPage.objects.first()
    if not contact_page:
        contact_page = ContactPage.objects.create()

    services = contact_page.services.all().order_by('id')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_page':
            contact_page.title = request.POST.get('title', contact_page.title)
            contact_page.subtitle = request.POST.get('subtitle', contact_page.subtitle)
            contact_page.save()
            messages.success(request, 'Contact page has been updated.')

        elif action == 'add_service':
            title = request.POST.get('service_title')
            description = request.POST.get('service_description', '')
            email = request.POST.get('service_email', '')
            timing = request.POST.get('service_timing', '')

            if title:
                ContactService.objects.create(
                    page=contact_page,
                    title=title,
                    description=description,
                    email=email,
                    timing=timing
                )
                messages.success(request, f'Service "{title}" has been added.')

        elif action == 'update_service':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(ContactService, pk=service_id, page=contact_page)
            service.title = request.POST.get('service_title')
            service.description = request.POST.get('service_description', '')
            service.email = request.POST.get('service_email', '')
            service.timing = request.POST.get('service_timing', '')
            service.save()
            messages.success(request, f'Service "{service.title}" has been updated.')

        elif action == 'delete_service':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(ContactService, pk=service_id, page=contact_page)
            service_name = service.title
            service.delete()
            messages.success(request, f'Service "{service_name}" has been deleted.')

        return redirect('manage_contact_page')

    context = {
        'contact_page': contact_page,
        'services': services,
    }
    return render(request, 'admin/manage_contact_page.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_about_page(request):
    """Custom about page management page"""
    about_page = AboutPage.objects.first()
    if not about_page:
        about_page = AboutPage.objects.create()

    if request.method == 'POST':
        about_page.hero_title = request.POST.get('hero_title', about_page.hero_title)
        about_page.section_title = request.POST.get('section_title', about_page.section_title)
        about_page.section_text = request.POST.get('section_text', about_page.section_text)
        about_page.feature_title = request.POST.get('feature_title', about_page.feature_title)
        about_page.feature_text_1 = request.POST.get('feature_text_1', about_page.feature_text_1)
        about_page.feature_text_2 = request.POST.get('feature_text_2', about_page.feature_text_2)
        about_page.promise_title = request.POST.get('promise_title', about_page.promise_title)
        about_page.promise_text = request.POST.get('promise_text', about_page.promise_text)

        # Handle image upload
        if 'feature_image' in request.FILES:
            about_page.feature_image = request.FILES['feature_image']

        about_page.save()
        messages.success(request, 'About page has been updated successfully.')
        return redirect('manage_about_page')

    context = {
        'about_page': about_page,
    }
    return render(request, 'admin/manage_about_page.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_newsletters(request):
    """Custom newsletter management page"""
    # Check if editing a newsletter
    edit_newsletter = None
    edit_id = request.GET.get('edit')
    if edit_id:
        try:
            edit_newsletter = Newsletter.objects.get(id=edit_id)
        except Newsletter.DoesNotExist:
            messages.error(request, "Newsletter not found.")
    
    if request.method == "POST":
        if 'create_newsletter' in request.POST:
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            action = request.POST.get('action', 'draft')
            
            if subject and content:
                status = 'draft'
                scheduled_at = None
                
                if action == 'send':
                    status = 'sent'
                elif action == 'schedule':
                    status = 'scheduled'
                    scheduled_at_str = request.POST.get('scheduled_at')
                    if scheduled_at_str:
                        from django.utils.dateparse import parse_datetime
                        scheduled_at = parse_datetime(scheduled_at_str)
                        if not scheduled_at:
                            messages.error(request, "Invalid schedule date/time.")
                            return redirect('manage_newsletters')
                
                newsletter = Newsletter.objects.create(
                    subject=subject,
                    content=content,
                    status=status,
                    scheduled_at=scheduled_at
                )
                
                if action == 'send':
                    from .utils import send_newsletter_to_all
                    sent_count = send_newsletter_to_all(newsletter)
                    newsletter.sent_at = timezone.now()
                    newsletter.sent_count = sent_count
                    newsletter.save()
                    messages.success(request, f"Newsletter sent to {sent_count} subscribers!")
                elif action == 'schedule':
                    messages.success(request, f"Newsletter scheduled for {scheduled_at}!")
                else:
                    messages.success(request, f"Newsletter '{subject}' saved as draft!")
                
                return redirect('manage_newsletters')
            else:
                messages.error(request, "Subject and content are required.")
        
        elif 'update_newsletter' in request.POST:
            newsletter_id = request.POST.get('newsletter_id')
            subject = request.POST.get('subject')
            content = request.POST.get('content')
            
            try:
                newsletter = Newsletter.objects.get(id=newsletter_id)
                if newsletter.status == 'draft':  # Only allow editing drafts
                    newsletter.subject = subject
                    newsletter.content = content
                    newsletter.save()
                    messages.success(request, f"Newsletter '{subject}' updated successfully!")
                else:
                    messages.error(request, "Only draft newsletters can be edited.")
            except Newsletter.DoesNotExist:
                messages.error(request, "Newsletter not found.")
            
            return redirect('manage_newsletters')
        
        elif 'send_newsletter' in request.POST:
            newsletter_id = request.POST.get('send_newsletter')
            try:
                newsletter = Newsletter.objects.get(id=newsletter_id)
                if newsletter.status == 'draft':
                    from .utils import send_newsletter_to_all
                    sent_count = send_newsletter_to_all(newsletter)
                    newsletter.status = 'sent'
                    newsletter.sent_at = timezone.now()
                    newsletter.sent_count = sent_count
                    newsletter.save()
                    messages.success(request, f"Newsletter sent to {sent_count} subscribers!")
                else:
                    messages.warning(request, "This newsletter has already been sent or scheduled.")
            except Newsletter.DoesNotExist:
                messages.error(request, "Newsletter not found.")
            return redirect('manage_newsletters')
        
        elif 'delete_newsletter' in request.POST:
            newsletter_id = request.POST.get('delete_newsletter')
            try:
                newsletter = Newsletter.objects.get(id=newsletter_id)
                subject = newsletter.subject
                newsletter.delete()
                messages.success(request, f"Newsletter '{subject}' deleted successfully!")
            except Newsletter.DoesNotExist:
                messages.error(request, "Newsletter not found.")
            return redirect('manage_newsletters')
    
    newsletters = Newsletter.objects.all().order_by('-created_at')

    # Filter by status
    status = request.GET.get('status')
    if status:
        newsletters = newsletters.filter(status=status)

    # Search functionality
    q = request.GET.get('q')
    if q:
        newsletters = newsletters.filter(Q(subject__icontains=q) | Q(content__icontains=q))

    # Pagination
    paginator = Paginator(newsletters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get subscriber count
    subscriber_count = NewsletterSubscriber.objects.filter(is_active=True).count()

    context = {
        'newsletters': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'query_params': request.GET.copy(),
        'status_choices': Newsletter.STATUS_CHOICES,
        'subscriber_count': subscriber_count,
        'edit_newsletter': edit_newsletter,
    }
    return render(request, 'admin/manage_newsletters.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def newsletter_content(request, pk):
    """Return newsletter content as JSON for AJAX requests"""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return JsonResponse({
        'subject': newsletter.subject,
        'content': newsletter.content,
        'status': newsletter.status,
        'created_at': newsletter.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'scheduled_at': newsletter.scheduled_at.strftime('%Y-%m-%d %H:%M:%S') if newsletter.scheduled_at else None,
        'sent_at': newsletter.sent_at.strftime('%Y-%m-%d %H:%M:%S') if newsletter.sent_at else None,
        'sent_count': newsletter.sent_count,
    })


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_subscribers(request):
    """Custom newsletter subscribers management page"""
    subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')

    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active is not None:
        subscribers = subscribers.filter(is_active=is_active == '1')

    # Search functionality
    q = request.GET.get('q')
    if q:
        subscribers = subscribers.filter(email__icontains=q)

    # Pagination
    paginator = Paginator(subscribers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'subscribers': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'query_params': request.GET.copy(),
    }
    return render(request, 'admin/manage_subscribers.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
@require_POST
def toggle_subscriber_status(request, pk):
    """Toggle subscriber active status"""
    subscriber = get_object_or_404(NewsletterSubscriber, pk=pk)
    subscriber.is_active = not subscriber.is_active
    subscriber.save()

    status = "activated" if subscriber.is_active else "deactivated"
    messages.success(request, f'Subscriber {subscriber.email} has been {status}.')

    return redirect('manage_subscribers')
