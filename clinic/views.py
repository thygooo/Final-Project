from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Medicine, MedicineCategory, MedicineRequest, Patient
from .forms import (SignUpForm, MedicineForm, MedicineCategoryForm,
                    MedicineRequestForm, MedicineRequestProcessForm)
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta
from django.db import models


def is_staff(user):
    return user.is_staff


def home(request):
    return render(request, 'clinic/home.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'clinic/signup.html', {'form': form})


@login_required
def inventory(request):
    query = request.GET.get('q', '')
    categories = MedicineCategory.objects.all()

    # Get all medicines for search
    medicines = Medicine.objects.all()
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(shelf_location__icontains=query)
        )

    low_stock = Medicine.objects.filter(quantity__lte=F('reorder_level'))
    near_expiry = Medicine.objects.filter(expiry_date__lte=timezone.now().date() + timedelta(days=30))

    context = {
        'categories': categories,
        'low_stock': low_stock,
        'near_expiry': near_expiry,
        'medicines': medicines,  # Add this for search results
        'search_query': query
    }
    return render(request, 'clinic/inventory.html', context)


@login_required
def category_medicines(request, category_id):
    category = get_object_or_404(MedicineCategory, pk=category_id)
    shelf = request.GET.get('shelf')
    medicines = Medicine.objects.filter(category=category)

    if shelf:
        medicines = medicines.filter(shelf_location=shelf)

    return render(request, 'clinic/category_medicines.html', {
        'category': category,
        'medicines': medicines,
        'shelf_filter': shelf
    })


@login_required
@user_passes_test(is_staff)
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine added successfully!')
            return redirect('inventory')
    else:
        form = MedicineForm()
    return render(request, 'clinic/medicine_form.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def edit_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine updated successfully!')
            return redirect('category_medicines', category_id=medicine.category.id)
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'clinic/medicine_form.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def delete_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, pk=medicine_id)
    category_id = medicine.category.id
    medicine.delete()
    messages.success(request, 'Medicine deleted successfully!')
    return redirect('category_medicines', category_id=category_id)


@login_required
def request_medicine(request):
    available_medicines = Medicine.objects.filter(quantity__gt=0)

    if request.method == 'POST':
        form = MedicineRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.patient = request.user.patient
            request_obj.save()
            messages.success(request, 'Medicine request submitted successfully!')
            return redirect('my_requests')
    else:
        form = MedicineRequestForm()

    return render(request, 'clinic/request_medicine.html', {
        'form': form,
        'available_medicines': available_medicines
    })


@login_required
def my_requests(request):
    requests = MedicineRequest.objects.filter(patient=request.user.patient).order_by('-request_date')
    return render(request, 'clinic/my_requests.html', {'requests': requests})


@login_required
@user_passes_test(is_staff)
def manage_requests(request):
    pending_requests = MedicineRequest.objects.filter(status='pending').order_by('request_date')
    return render(request, 'clinic/manage_requests.html', {'requests': pending_requests})


@login_required
@user_passes_test(is_staff)
def process_request(request, request_id):
    medicine_request = get_object_or_404(MedicineRequest, pk=request_id)
    if request.method == 'POST':
        form = MedicineRequestProcessForm(request.POST, instance=medicine_request)
        if form.is_valid():
            processed_request = form.save(commit=False)
            processed_request.processed_by = request.user
            processed_request.save()
            messages.success(request, 'Request processed successfully!')
            return redirect('manage_requests')
    else:
        form = MedicineRequestProcessForm(instance=medicine_request)
    return render(request, 'clinic/process_request.html', {
        'form': form,
        'request': medicine_request,
    })

@login_required
@user_passes_test(is_staff)
def alerts(request):
    low_stock = Medicine.objects.filter(quantity__lte=F('reorder_level'))
    near_expiry = Medicine.objects.filter(expiry_date__lte=timezone.now().date() + timedelta(days=30))

    context = {
        'low_stock': low_stock,
        'near_expiry': near_expiry,
        'now': timezone.now().date()  # Add this line
    }
    return render(request, 'clinic/alerts.html', context)

@login_required
@user_passes_test(is_staff)
def category_list(request):
    categories = MedicineCategory.objects.all()
    return render(request, 'clinic/category_list.html', {'categories': categories})

@login_required
@user_passes_test(is_staff)
def add_category(request):
    if request.method == 'POST':
        form = MedicineCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('inventory')  # Changed from 'category_list' to 'inventory'
    else:
        form = MedicineCategoryForm()
    return render(request, 'clinic/category_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def edit_category(request, category_id):
    category = get_object_or_404(MedicineCategory, pk=category_id)
    if request.method == 'POST':
        form = MedicineCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('inventory')  # Changed from 'category_list' to 'inventory'
    else:
        form = MedicineCategoryForm(instance=category)
    return render(request, 'clinic/category_form.html', {'form': form})

@login_required
@user_passes_test(is_staff)
def delete_category(request, category_id):
    category = get_object_or_404(MedicineCategory, pk=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('inventory')  # Changed from 'category_list' to 'inventory'
    return render(request, 'clinic/category_confirm_delete.html', {'category': category})