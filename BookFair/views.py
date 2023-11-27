# Django packages
from django.shortcuts import render, HttpResponse, get_object_or_404
# Model packages
from BookFair.models import Category, Product
# Python packages
import random

# Create your views here.
def home(request):
    # Get 4 random object IDs
    num_products = Product.objects.count()
    rand_product_ids = random.sample(range(1,num_products), 4)
    # Get corresponding product objects
    rand_product_objs = [Product.objects.get(pk=prod_id) for prod_id in rand_product_ids]

    return render(request, "BookFair/home.html", {"featured_products": rand_product_objs})

def category(request, cat_id):
    req_category = get_object_or_404(Category, pk=cat_id)

    cat_products = req_category.product_set

    # Sorting options
    match request.GET.get('sort'):
        case "name":
            cat_products_sorted = cat_products.order_by('prod_name')
        case "price-lh":
            cat_products_sorted = cat_products.order_by('prod_price')
        case "price-hl":
            cat_products_sorted = cat_products.order_by('-prod_price')
        case "stock-lh":
            cat_products_sorted = cat_products.order_by('prod_stock')
        case "stock-hl":
            cat_products_sorted = cat_products.order_by('-prod_stock')
        case _:
            cat_products_sorted = cat_products.order_by('prod_id').all()

    return render(request, "BookFair/category.html", {"category": req_category, "cat_products": cat_products_sorted})

def product(request, prod_id):
    req_product = get_object_or_404(Product, pk=prod_id)

    return render(request, "BookFair/product.html", {"product": req_product})

<<<<<<< Updated upstream
=======
def add_to_cart(request, prod_id):
    product = get_object_or_404(Product, pk=prod_id)
    user_profile = UserProfile.objects.get(user=request.user)

    # Check if the user has an existing cart
    if not hasattr(user_profile, 'cart'):
        cart = Cart.objects.create(user_profile=user_profile)
        user_profile.cart = cart
        user_profile.save()

    # Add the product to the cart
    user_profile.cart.products.add(product)
    messages.success(request, 'Product added to cart!')
    return redirect('user_profile')


def view_cart(request):
    user_profile = UserProfile.objects.get(user=request.user)
    cart = user_profile.cart
    cart_products = cart.products.all()
    return render(request, 'BookFair/view_cart.html', {'cart_products': cart_products})

def cart(request):
    #user_profile = UserProfile.objects.get(user=request.user)
    #cart = user_profile.cart
    #cart_products = cart.products.all()
    return render(request, 'BookFair/cart.html', {'cart_products': cart_products})


def user_profile(request):
    user = request.user
    return render(request, 'BookFair/user_profile.html', {'user': user})

>>>>>>> Stashed changes
def signup_profile(request):
    return render(request, 'BookFair/signup_profile.html')
