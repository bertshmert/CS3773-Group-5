# Django packages
from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.views.generic.edit import FormView
from BookFair.forms import ProductForm
# Model packages
from BookFair.models import Customer, Category, Product, Cart
# Form packages
from BookFair.forms import SearchBoxNav, SearchBoxFull, CustomerSignupForm, LoginForm
# Python packages
import random
from functools import reduce
import operator
# Logger
import logging

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
            cat_products_sorted = cat_products.order_by('prod_name').all()

    return render(request, "BookFair/category.html", {"category": req_category, "cat_products": cat_products_sorted})

def product(request, prod_id):
    form = ProductForm()
    req_product = get_object_or_404(Product, pk=prod_id)
    ######### Sketch code
    if request.method == "POST":
            messages.success(request, f"{Product.prod_name} added to your cart.")
            return redirect("BookFair:add_to_cart", product_id=prod_id)
            
    context = { 
      "product": product,
      }
    #########
    context['form'] = form
    return render(request, "BookFair/product.html", {"product": req_product})
    #return render(request, "BookFair/product.html", context)

@login_required
def add_to_cart(request, product_id):
    #cart_item  = Cart.objects.filter(Q(user=request.user, product=product_id)).first()
    cart_item = get_object_or_404(Product, pk=product_id)
    if cart_item:
      #  cart_item.quantity += 1
       # cart_item.save()
        messages.success(request, "Item added to your cart.")
    else:
        Cart.objects.create(user=request.user, product=prod_id)
        messages.success(request, "Item added to your cart.")

    return redirect("BookFair:cart_detail")

@login_required
def remove_from_cart(request, cart_item_id):
     cart_item = get_object_or_404(Cart, id=cart_item_id)

     if cart_item.delete == request.user:
       cart_item.delete()
       messages.success(request, "Item removed from your cart.")
     
     return redirect("BookFair:cart_detail")


@login_required
def cart_detail(request):
    cart_items = Cart.objects.filter(Q(user=request.user))
    #cart_item = get_object_or_404(Product, pk=product_id)
    total_item_prices = [sum(item.quantity * item.product.price) for item in cart_items]
    item_prices = None

    context = {
            "cart_items": cart_items,
            "total_item_prices": total_item_prices,
        }

    return render(request, "BookFair/cart_detail.html", context)


def profile(request):
    # Get customer that corresponds to signed-in user
    cur_user = request.user
    # Initialize cur_customer to none
    cur_customer = None

    if (cur_user is not None) & (cur_user.is_authenticated):
        cur_customer = Customer.objects.get(user=cur_user)

    return render(request, 'BookFair/profile.html', {'customer': cur_customer})

def LogoutView(request):
    # Simple logout page
    logout(request)

    return render(request, 'BookFair/logout.html')

class SignupView(FormView):
    template_name = "BookFair/signup.html"
    form_class = CustomerSignupForm

    def get_success_url(self):
        return reverse(profile)

    def post(self, request, *args, **kwargs):
        # Get form object to validate
        form = self.get_form()
        if form.is_valid():
            # Check that password is the same -- form validation does not help here
            if form.cleaned_data['password1'] == form.cleaned_data['password2']:
                messages.success(request, "Successfully signed up!")
                return self.form_valid(form)
            else:
                messages.error(request, "Invalid password.")
                return self.form_invalid(form)

        return self.form_invalid(form)

    # A function that actually creates a user (and the corresponding customer) objects
    @transaction.atomic
    def create_user_transact(self, form):
        user = User.objects.create_user(
            form.cleaned_data['username'],
            form.cleaned_data['email'],
            form.cleaned_data['password1']
        )
        Customer.objects.create(
            user = user,
            cus_lname = form.cleaned_data['last_name'],
            cus_fname = form.cleaned_data['first_name'],
            cus_initial = form.cleaned_data['initial_name'],
            cus_email = form.cleaned_data['email'],
            cus_phone = form.cleaned_data['phone_number'],
            cus_phone_country = form.cleaned_data['phone_country']
        ).save()

        return user

    # A function that is called once the form has been checked for validity.
    def form_valid(self, form):
        self.create_user_transact(form)
        
        user = authenticate(
            username = form.cleaned_data['username'],
            password = form.cleaned_data['password1']
        )
        
        login(self.request, user)

        return super().form_valid(form)

# Login
class CustomerLoginView(LoginView):

    form_class = LoginForm
    template_name = "BookFair/login.html"

    def get_success_url(self):
        return reverse(profile)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            messages.error(request, "Invalid login. Check your username and password.")
            return self.form_invalid(form)


# Search
def search(request):
    # The search query is to be submitted as a GET request
    search_form_full = SearchBoxFull()
    # Initialize query, query_results to none
    query = None
    query_results_sorted = None

    # Get the query in the GET request
    if request.GET.get('q'):
        # Make a form object and include the data in the request for validation
        ## First attempt it with SearchBoxFull (also setting search_form_full to fill it in w/ user value)
        search_form = search_form_full = SearchBoxFull(request.GET)
        ## Check if the form is not valid -- if it isn't, update it to check the nav form submission
        if not search_form.is_valid():
            search_form = SearchBoxNav(request.GET)
        ## Finally, if the form is valid on either try, get its query; if it's not, log an error.
        if search_form.is_valid():
            query = search_form.cleaned_data['q']

            # Separate query into tokens for word-by-word matching -- inspired by https://stackoverflow.com/questions/28278150/mysql-efficient-search-with-partial-word-match-and-relevancy-score-fulltext
            query_tokens = query.split()

            query_results = Product.objects.filter(
                # Q(prod_name__icontains = token)
                reduce(operator.or_, [Q(prod_name__icontains = token) for token in query_tokens])
                |
                reduce(operator.or_, [Q(prod_descript__icontains = token) for token in query_tokens])
                # Q(prod_descript__icontains = query)
            )

            # Sort time
            # Try to get sort -- if it's not in the POST request, just order it by name
            try:
                sort = search_form.cleaned_data['sort']

                match sort:
                    case "name":
                        query_results_sorted = query_results.order_by('prod_name')
                    case "price-lh":
                        query_results_sorted = query_results.order_by('prod_price')
                    case "price-hl":
                        query_results_sorted = query_results.order_by('-prod_price')
                    case "stock-lh":
                        query_results_sorted = query_results.order_by('prod_stock')
                    case "stock-hl":
                        query_results_sorted = query_results.order_by('-prod_stock')
                    case _:
                        query_results_sorted = query_results.order_by('prod_name')
            except KeyError:
                query_results_sorted = query_results.order_by('prod_name')
        else:
            logging.error('Invalid search form!')
    else:
        logging.error('No search query given!')

    return render(request, "BookFair/search.html", {'search_form': search_form_full, 'search_results': query_results_sorted, 'query': query})
