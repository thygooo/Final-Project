from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Medicine, MedicineCategory, MedicineRequest, Patient, Transaction
from .forms import (SignUpForm, MedicineForm, MedicineCategoryForm,
                    MedicineRequestForm, MedicineRequestProcessForm, RestockForm)
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import models
from openpyxl import Workbook


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
    available_medicines = Medicine.objects.filter(quantity__gt=0).order_by('name')

    if request.method == 'POST':
        form = MedicineRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.patient = request.user.patient
            request_obj.save()

            Transaction.objects.create(
                transaction_type='REQUEST',
                medicine=request_obj.medicine,
                quantity=request_obj.quantity,
                user=request.user,
                patient=request.user.patient,
                notes=request_obj.notes
            )

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

def base_context(request):
    if request.user.is_authenticated and request.user.is_staff:
        pending_count = MedicineRequest.objects.filter(status='pending').count()
        return {'pending_request_count': pending_count}
    return {}


@login_required
@user_passes_test(is_staff)
def process_request(request, request_id):
    medicine_request = get_object_or_404(MedicineRequest, pk=request_id)
    remaining_stock = medicine_request.medicine.quantity - medicine_request.quantity

    context = {
        'request': medicine_request,
        'remaining_stock': remaining_stock,
        # ... other context ...
    }

    if request.method == 'POST':
        form = MedicineRequestProcessForm(request.POST, instance=medicine_request)
        action = request.POST.get('action')

        if form.is_valid():
            if action == 'approve':
                # Additional stock check (in case someone bypasses the UI)
                if medicine_request.quantity > medicine_request.medicine.quantity:
                    messages.error(request, 'Cannot approve - insufficient stock!')
                    return redirect('manage_requests')

                medicine_request.status = 'approved'
                medicine_request.medicine.quantity -= medicine_request.quantity
                medicine_request.medicine.save()
                messages.success(request, 'Request approved successfully!')

            elif action == 'reject':
                medicine_request.status = 'rejected'
                messages.success(request, 'Request rejected.')

            medicine_request.processed_by = request.user
            medicine_request.processed_date = timezone.now()
            medicine_request.save()

            # Log transaction
            Transaction.objects.create(
                transaction_type=action.upper(),
                medicine=medicine_request.medicine,
                quantity=medicine_request.quantity,
                user=request.user,
                patient=medicine_request.patient,
                notes=form.cleaned_data['notes']
            )

            return redirect('manage_requests')

    else:
        form = MedicineRequestProcessForm(instance=medicine_request)

    return render(request, 'clinic/process_request.html', {
        'request': medicine_request,
        'form': form
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


@login_required
def transaction_history(request):
    transactions = Transaction.objects.all().order_by('-timestamp')
    return render(request, 'clinic/transaction_history.html', {'transactions': transactions})


@login_required
def export_transactions(request):
    # Create Excel workbook
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="transactions_{}.xls"'.format(
        datetime.now().strftime('%Y-%m-%d'))

    wb = Workbook()
    ws = wb.active
    ws.title = "Transaction History"

    # Add headers
    headers = ['Date', 'Type', 'Medicine', 'Category', 'Quantity', 'Staff', 'Patient', 'Notes']
    ws.append(headers)

    # Add data
    for t in Transaction.objects.all().order_by('-timestamp'):
        ws.append([
            t.timestamp.strftime('%Y-%m-%d %H:%M'),
            t.get_transaction_type_display(),
            t.medicine.name if t.medicine else 'N/A',
            t.medicine.category.name if t.medicine else 'N/A',
            t.quantity,
            t.user.get_full_name() if t.user else 'System',
            t.patient.user.get_full_name() if t.patient else 'N/A',
            t.notes
        ])

    wb.save(response)
    return response


@login_required
@user_passes_test(is_staff)
def restock_medicine(request):
    initial = {}
    medicine_id = request.GET.get('medicine_id')
    if medicine_id:
        medicine = get_object_or_404(Medicine, pk=medicine_id)
        initial['medicine'] = medicine
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            medicine = form.cleaned_data['medicine']
            quantity = form.cleaned_data['quantity']

            # Update stock
            medicine.quantity += quantity
            medicine.save()

            # Log transaction
            Transaction.objects.create(
                transaction_type='RESTOCK',
                medicine=medicine,
                quantity=quantity,
                user=request.user,
                notes=form.cleaned_data['notes']
            )

            messages.success(request, f'Successfully added {quantity} items to {medicine.name}')
            return redirect('inventory')
    else:
        form = RestockForm(initial=initial)

    return render(request, 'clinic/restock_form.html', {'form': form})

@login_required
def restock_history(request):
    restocks = Transaction.objects.filter(
        transaction_type='RESTOCK'
    ).order_by('-timestamp')
    return render(request, 'clinic/restock_history.html', {'restocks': restocks})


@login_required
@user_passes_test(is_staff)
def process_request_action(request, request_id, action):
    medicine_request = get_object_or_404(MedicineRequest, pk=request_id)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')

        if action == 'approve':
            medicine_request.status = 'approved'
            medicine_request.processed_by = request.user
            medicine_request.processed_date = timezone.now()
            medicine_request.notes = notes

            # Deduct from inventory
            medicine_request.medicine.quantity -= medicine_request.quantity
            medicine_request.medicine.save()

            messages.success(request, 'Request approved successfully!')
        elif action == 'reject':
            medicine_request.status = 'rejected'
            medicine_request.processed_by = request.user
            medicine_request.processed_date = timezone.now()
            medicine_request.notes = notes
            messages.success(request, 'Request rejected.')

        medicine_request.save()

        # Log transaction
        Transaction.objects.create(
            transaction_type='APPROVE' if action == 'approve' else 'REJECT',
            medicine=medicine_request.medicine,
            quantity=medicine_request.quantity,
            user=request.user,
            patient=medicine_request.patient,
            notes=notes
        )

        return redirect('manage_requests')

    return redirect('process_request', request_id=request_id)