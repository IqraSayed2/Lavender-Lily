from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review, Category, Color, Size
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from cart.models import WishlistItem

@login_required(login_url='signin')
def shop(request):
    qs = Product.objects.all().order_by("-created_at")

    # SEARCH
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))

    # FILTERS
    categories = request.GET.getlist("category")
    if categories:
        # Remove empty strings
        categories = [c for c in categories if c]
        if categories:
            # If specific categories selected, filter by them
            qs = qs.filter(category__name__in=categories)
        # If only "" was selected, or none, no filter

    color = request.GET.get("color")
    if color:
        qs = qs.filter(color__name=color)

    # price range
    max_price = request.GET.get("max_price")
    try:
        if max_price:
            qs = qs.filter(price__lte=float(max_price))
    except ValueError:
        pass

    # SORT
    sort = request.GET.get("sort")
    if sort == "price_asc":
        qs = qs.order_by("price")
    elif sort == "price_desc":
        qs = qs.order_by("-price")
    elif sort == "newest":
        qs = qs.order_by("-created_at")

    # PAGINATION
    paginator = Paginator(qs, 8)  # 8 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # unique categories & colors for sidebar filters
    categories_list = sorted(Product.objects.values_list("category__name", flat=True).distinct())
    colors_list = Color.objects.filter(name__in=Product.objects.values_list("color__name", flat=True).distinct()).order_by("name")

    context = {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "categories": categories_list,
        "colors": colors_list,
        "query_params": request.GET.copy(),
        "selected_categories": request.GET.getlist("category"),
    }
    return render(request, "store/shop.html", context)


@login_required(login_url='signin')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # images list (image_main first)
    images = [product.image_main.url]
    for f in [product.image1, product.image2, product.image3, product.image4]:
        if f:
            images.append(f.url)

    # POST review
    if request.method == "POST" and request.POST.get("review_submit"):
        name = request.POST.get("name") or "Anonymous"
        rating = int(request.POST.get("rating", 5))
        comment = request.POST.get("comment", "")
        user = request.user if request.user.is_authenticated else None
        if comment.strip():
            Review.objects.create(product=product, user=user, name=name, rating=rating, comment=comment)
            messages.success(request, "Thanks - your review has been posted.")
            return redirect(product.get_absolute_url())
        else:
            messages.error(request, "Please write a comment before submitting.")

    reviews = product.reviews.filter(approved=True)

    from .models import Size
    all_sizes = Size.objects.all()
    available_sizes = product.sizes.all()

    # Get product variants (same variant_group, different colors)
    variants = Product.objects.filter(variant_group=product.variant_group).exclude(pk=product.pk).order_by('color__name')
    all_variants = [product] + list(variants)

    context = {
        "product": product,
        "images": images,
        "reviews": reviews,
        "all_sizes": all_sizes,
        "available_sizes": available_sizes,
        "all_variants": all_variants,
    }
    return render(request, "store/productdetail.html", context)


@login_required(login_url='signin')
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist_item, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        # Item was already in wishlist, so remove it
        wishlist_item.delete()
        messages.info(request, "Removed from wishlist.")
    else:
        # Item was added to wishlist
        messages.success(request, "Added to wishlist.")

    # redirect back
    next_url = request.META.get("HTTP_REFERER", "/")
    return redirect(next_url)


def size_chart(request):
    return render(request, "store/size_chart.html")


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_products(request):
    """Custom product management page"""
    products = Product.objects.all().order_by('-created_at')

    # Search functionality
    q = request.GET.get('q')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q))

    # Filter by category
    category = request.GET.get('category')
    if category:
        products = products.filter(category__name=category)

    # Filter by color
    color = request.GET.get('color')
    if color:
        products = products.filter(color__name=color)

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    categories = Category.objects.all().order_by('name')
    colors = Color.objects.all().order_by('name')

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'categories': categories,
        'colors': colors,
        'query_params': request.GET.copy(),
    }
    return render(request, 'admin/manage_products.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def add_product(request):
    """Add new product"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            variant_group = request.POST.get('variant_group', '').strip()
            category_id = request.POST.get('category')
            color_id = request.POST.get('color')
            price = request.POST.get('price')
            description = request.POST.get('description', '')
            sku = request.POST.get('sku', '')
            material = request.POST.get('material', '')
            care = request.POST.get('care', '')
            size_ids = request.POST.getlist('sizes')

            # Validate required fields
            if not all([name, category_id, color_id, price]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('add_product')

            # Create product
            category = get_object_or_404(Category, pk=category_id)
            color = get_object_or_404(Color, pk=color_id)

            product = Product.objects.create(
                name=name,
                variant_group=variant_group or name,  # Use name if variant_group empty
                category=category,
                color=color,
                price=price,
                description=description,
                sku=sku,
                material=material,
                care=care,
            )

            # Add sizes
            if size_ids:
                sizes = Size.objects.filter(pk__in=size_ids)
                product.sizes.set(sizes)

            # Handle images
            if 'image_main' in request.FILES:
                product.image_main = request.FILES['image_main']
            if 'image1' in request.FILES:
                product.image1 = request.FILES['image1']
            if 'image2' in request.FILES:
                product.image2 = request.FILES['image2']
            if 'image3' in request.FILES:
                product.image3 = request.FILES['image3']
            if 'image4' in request.FILES:
                product.image4 = request.FILES['image4']

            product.save()

            messages.success(request, f'Product "{product.name}" has been created successfully.')
            return redirect('manage_products')

        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            return redirect('add_product')

    # GET request - show form
    categories = Category.objects.all().order_by('name')
    colors = Color.objects.all().order_by('name')
    sizes = Size.objects.all().order_by('order')
    variant_groups = sorted(Product.objects.values_list('variant_group', flat=True).distinct())

    context = {
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'variant_groups': variant_groups,
    }
    return render(request, 'admin/add_product.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def edit_product(request, pk):
    """Edit existing product"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            variant_group = request.POST.get('variant_group', '').strip()
            category_id = request.POST.get('category')
            color_id = request.POST.get('color')
            price = request.POST.get('price')
            description = request.POST.get('description', '')
            sku = request.POST.get('sku', '')
            material = request.POST.get('material', '')
            care = request.POST.get('care', '')
            size_ids = request.POST.getlist('sizes')

            # Validate required fields
            if not all([name, category_id, color_id, price]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('edit_product', pk=pk)

            # Update product
            category = get_object_or_404(Category, pk=category_id)
            color = get_object_or_404(Color, pk=color_id)

            product.name = name
            product.variant_group = variant_group or name
            product.category = category
            product.color = color
            product.price = price
            product.description = description
            product.sku = sku
            product.material = material
            product.care = care

            # Update sizes
            if size_ids:
                sizes = Size.objects.filter(pk__in=size_ids)
                product.sizes.set(sizes)
            else:
                product.sizes.clear()

            # Handle images
            if 'image_main' in request.FILES:
                product.image_main = request.FILES['image_main']
            if 'image1' in request.FILES:
                product.image1 = request.FILES['image1']
            if 'image2' in request.FILES:
                product.image2 = request.FILES['image2']
            if 'image3' in request.FILES:
                product.image3 = request.FILES['image3']
            if 'image4' in request.FILES:
                product.image4 = request.FILES['image4']

            product.save()

            messages.success(request, f'Product "{product.name}" has been updated successfully.')
            return redirect('manage_products')

        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            return redirect('edit_product', pk=pk)

    # GET request - show form with current data
    categories = Category.objects.all().order_by('name')
    colors = Color.objects.all().order_by('name')
    sizes = Size.objects.all().order_by('order')
    variant_groups = sorted(Product.objects.values_list('variant_group', flat=True).distinct())

    context = {
        'product': product,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'selected_sizes': [size.pk for size in product.sizes.all()],
        'variant_groups': variant_groups,
    }
    return render(request, 'admin/edit_product.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
@require_POST
def delete_product(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    product_name = product.name

    try:
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting product: {str(e)}')

    return redirect('manage_products')


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_categories(request):
    """Manage categories"""
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description', '')

            if name:
                try:
                    Category.objects.create(name=name, description=description)
                    messages.success(request, f'Category "{name}" has been created.')
                except Exception as e:
                    messages.error(request, f'Error creating category: {str(e)}')
            else:
                messages.error(request, 'Category name is required.')

        elif action == 'edit':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description', '')

            if category_id and name:
                try:
                    category = get_object_or_404(Category, pk=category_id)
                    category.name = name
                    category.description = description
                    category.save()
                    messages.success(request, f'Category "{name}" has been updated.')
                except Exception as e:
                    messages.error(request, f'Error updating category: {str(e)}')
            else:
                messages.error(request, 'Category name is required.')

        elif action == 'delete':
            category_id = request.POST.get('category_id')
            if category_id:
                try:
                    category = get_object_or_404(Category, pk=category_id)
                    category_name = category.name
                    category.delete()
                    messages.success(request, f'Category "{category_name}" has been deleted.')
                except Exception as e:
                    messages.error(request, f'Error deleting category: {str(e)}')

        return redirect('manage_categories')

    context = {
        'categories': categories,
    }
    return render(request, 'admin/manage_categories.html', context)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff)
def manage_colors(request):
    """Manage colors"""
    colors = Color.objects.all().order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name')
            hex_code = request.POST.get('hex_code', '')

            if name:
                try:
                    Color.objects.create(name=name, hex_code=hex_code)
                    messages.success(request, f'Color "{name}" has been created.')
                except Exception as e:
                    messages.error(request, f'Error creating color: {str(e)}')
            else:
                messages.error(request, 'Color name is required.')

        elif action == 'edit':
            color_id = request.POST.get('color_id')
            name = request.POST.get('name')
            hex_code = request.POST.get('hex_code', '')

            if color_id and name:
                try:
                    color = get_object_or_404(Color, pk=color_id)
                    color.name = name
                    color.hex_code = hex_code
                    color.save()
                    messages.success(request, f'Color "{name}" has been updated.')
                except Exception as e:
                    messages.error(request, f'Error updating color: {str(e)}')
            else:
                messages.error(request, 'Color name is required.')

        elif action == 'delete':
            color_id = request.POST.get('color_id')
            if color_id:
                try:
                    color = get_object_or_404(Color, pk=color_id)
                    color_name = color.name
                    color.delete()
                    messages.success(request, f'Color "{color_name}" has been deleted.')
                except Exception as e:
                    messages.error(request, f'Error deleting color: {str(e)}')

        return redirect('manage_colors')

    context = {
        'colors': colors,
    }
    return render(request, 'admin/manage_colors.html', context)
