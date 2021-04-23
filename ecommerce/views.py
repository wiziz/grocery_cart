from django.shortcuts import render, redirect
# from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User, Group
# from .forms import UserRegisterForm
from .models import User, Product, ProductImage, Contact
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from accounts.views import *

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.template import RequestContext, Template
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.urls import reverse_lazy, reverse
from django import forms

# from .forms import ContactForm

def homeMain(request):
    product = Product.objects.all()
    if request.user.groups.filter(name='Customer').exists():
        try:
            cart = Cart.objects.get(user=request.user, ordered=False)
            totalCount = cart.cartitem_set.count()
            request.session['key'] = totalCount
        except:
            pass
        context = {'product': product,
                'title': 'Home Page', }
        template = 'html/homeMain.html'
        return render(request, template, context)
    elif request.user.groups.filter(name='Retailer').exists():
        return redirect('retailerDash')
    else :
        return redirect('wholesalerDash')

def search(request): 
    try:
        search = request.GET.get('search')
    except: 
        search = None

    if search: 
        product = Product.objects.filter(title__icontains = search)
        context = {'query': search, 'product': product}
        template = 'html/search.html'
    else: 
        return redirect('homeMain')
    return render(request, template, context)

def category(request):
    try: 
        chooseCategory= request.GET.get('category')
    except: 
        raise Http404(" A category does not exist")

    if chooseCategory: 
        category = Product.objects.filter(category = chooseCategory)

        context = {'category': category, }
        template = 'html/category.html'
    else: 
        return redirect('homeMain')
    
    return render(request, template, context)

def about(request):
    # u = User.objects.get(username=request.user.username)

    return render(request, 'html/about.html', {'title': 'About'})

#  sign in function
def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('homeMain')
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('signin')
    else:
        return render(request, 'html/signin.html', {'title': 'Sign in'})

# Logout function
# should set name function is different than logout unless the recusion problem happens.
def logout_views(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect('homeMain')


# register function
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        password1 = request.POST['password1']
        usertype = request.POST['usertype']
        if password == password1:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
            else:
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                                password=password, email=email)
                user.save()
                group = Group.objects.get(name=usertype)
                group.user_set.add(user)
                messages.success(request, f'Account created {user.username}!')
                return redirect('signin')
        else:
            messages.error(request, 'Does not match password')
    # else:
    #     form = UserCreationForm()
    return render(request, 'html/register.html')

# for a specific product
# @login_required
def UniqueProduct(request,slug):
    try:
        product = Product.objects.get(slug=slug)
        # print(products.title)
        # images = ProductImage.productimage_set.all()
        images = ProductImage.objects.filter(product=product)
        context = {'product': product,'images': images, 
                   'title': 'Home Page'}
        template = 'html/product.html'
        return render(request, template, context) 
    except product.DoesNotExist:
        raise Http404("Does not exist")


def contact(request): 
    request.session.set_expiry(120000)
    try:
        user = request.user
        context = { 'user':user, }
    except: 
        pass
    
    if request.method == 'POST':
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        email = request.POST['email']
        if request.user.is_authenticated: 
            contact = Contact.objects.create( user=request.user, firstName=firstName, lastName=lastName,email=email)
            contact.save()
        else:
            contact = Contact.objects.create(firstName=firstName, lastName=lastName,email=email)
            contact.save()
        messages.info(request, "Your feedback / questions has sent")
        return redirect('add_address')

    template = 'accounts/newaddress.html'
    return render(request, template, context)

class RetailerDash(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = User
    template_name = 'store/retailer_dash.html'
    context_object_name = 'userObject'

    def test_func(self):
        return self.request.user.groups.filter(name='Retailer').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['userObject'] = context['userObject']

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['userObject'] = context['userObject'].filter(
                name__icontains=search_input)

            context['search_input'] = search_input
        return context


class WholesalerDash(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = Product
    template_name = 'store/wholesaler_dash.html'
    context_object_name = 'productsObject'

    def test_func(self):
        return self.request.user.groups.filter(name='Wholesaler').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productsObject'] = context['productsObject'].filter(
            user=self.request.user.id)

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['productsObject'] = context['productsObject'].filter(
                name__icontains=search_input)

            context['search_input'] = search_input
        return context


class ProductDetail(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'store/product_details.html'
    context_object_name = 'details'


class CreateProduct(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    def test_func(self):
        return not self.request.user.groups.filter(name='Customer').exists()
    model = Product
    template_name = 'store/create_Product.html'
    fields = ['title', 'description', 'price', 'photo', 'availability']
    success_url = reverse_lazy('homeMain')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(CreateProduct, self).form_valid(form)


class UpdateProduct(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    def test_func(self):
        return not self.request.user.groups.filter(name='customer').exists()
    model = Product
    template_name = 'store/update_Product.html'
    fields = ['title', 'description', 'price', 'photo', 'availability']
    success_url = reverse_lazy('products')


class DeleteProduct(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    def test_func(self):
        return not self.request.user.groups.filter(name='customer').exists()
    model = Product
    context_object_name = 'productsObject'
    template_name = 'store/delete_Product.html'
    success_url = reverse_lazy('products')


