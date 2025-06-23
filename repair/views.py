import base64
import csv
from datetime import datetime
from decimal import InvalidOperation, Decimal
from io import BytesIO
import qrcode
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group
from django.db import IntegrityError, models
from django.http import  JsonResponse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm

from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa
from django.contrib.auth import views as auth_views
from .models import Customer, Technician, Firmware, FirmwareAccess, DeviceModel, FirmwareFolder, WindowsAppFile, \
    WindowsFirmware, ImageModel, CustomRegisterForm, SamsungModel, SamsungOrder, ToolActivation, PricingPlan, \
    MobileDriver, ActivationRequest, Tool, PaymentConfirmation, IMEIService, IMEICategory, IMEIOrder
from django.shortcuts import render, get_object_or_404, redirect
from .models import FirmwareFolder, RepairRequest
from .forms import SubscriberForm, BulkSamsungUploadForm, SubscribeForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.contrib.auth.forms import UserChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
import requests
from django.shortcuts import render
from django.contrib import messages

# Create a form for updating profile
class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('update_profile')
    else:
        form = UpdateProfileForm(instance=request.user)

    return render(request, 'repair/settings/update_profile.html', {'form': form})

# Superuser check
def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('manage_users')
    else:
        form = UserChangeForm(instance=user)
    return render(request, 'repair/settings/edit_user.html', {'form': form, 'user_obj': user})


@login_required
@user_passes_test(is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('manage_users')
    return render(request, 'repair/settings/confirm_delete.html', {'user_obj': user})


@login_required
@user_passes_test(is_superuser)
def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f'✅ {user.username} activated successfully.')
    return redirect('manage_users')


@login_required
@user_passes_test(is_superuser)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user == user:
        messages.warning(request, "⚠️ You can't deactivate your own account.")
    else:
        user.is_active = False
        user.save()
        messages.success(request, f'❌ {user.username} deactivated successfully.')
    return redirect('manage_users')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New user added successfully!')
            return redirect('manage_users')
    else:
        form = UserCreationForm()
    return render(request, 'repair/settings/add_user.html', {'form': form})

@login_required
def site_config(request):
    # Replace this with actual model/database values if needed
    if request.method == 'POST':
        site_name = request.POST.get('site_name')
        logo_url = request.POST.get('logo_url')
        contact_email = request.POST.get('contact_email')
        footer_text = request.POST.get('footer_text')

        # You can save these to a SiteSettings model, or just display success
        messages.success(request, "Site settings updated successfully!")
        return redirect('site_config')

    return render(request, 'repair/settings/site_config.html', {
        'site_name': 'Mobile Repair Imphal',
        'logo_url': 'https://yourdomain.com/static/images/logo.png',
        'contact_email': 'support@yourdomain.com',
        'footer_text': '© 2025 Mobile Repair Imphal. All rights reserved.'
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps user logged in
            messages.success(request, 'Your password has been updated successfully.')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'repair/settings/change_password.html', {'form': form})



@login_required
def user_settings(request):
    return render(request, 'repair/settings/settings.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    users = User.objects.all().order_by('id')
    return render(request, 'repair/settings/manage_users.html', {'users': users})







# repair add request
def repair_add_request(request):
    # Search and pagination
    search_query = request.GET.get("search", "").strip()
    repairs_qs = RepairRequest.objects.select_related("customer", "technician")

    if search_query:
        repairs_qs = repairs_qs.filter(
            Q(customer__name__icontains=search_query) |
            Q(device_model__icontains=search_query) |
            Q(issue_description__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    paginator = Paginator(repairs_qs, 13)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "repair/add_repair_request.html", {
        "repairs": page_obj,
        "search_query": search_query,

    })


# Home
@login_required
def home(request):
    # ✅ Handle first-time login modal
    show_modal = False
    if request.session.get("show_modal"):
        show_modal = True
        del request.session["show_modal"]  # Only show once

    # Load firmware folders
    folders = FirmwareFolder.objects.all()

    # YouTube videos
    raw_videos = [
        "https://youtu.be/rVKSSqtrOvs?si=0u1CMU6dhWlKM6GI",
        "https://youtu.be/j1tca3qFCtw?si=19jMUQxuYDzTgrTB",
        "https://youtu.be/QFj92b_i86Q?si=vrL7-kwfVsqjG60v",
        "https://youtu.be/VQDJKifr4IE?si=z-Cu6M_XJEaRyo8H",
    ]
    def to_embed(url):
        if "youtu.be/" in url:
            return f"https://www.youtube.com/embed/{url.split('youtu.be/')[1].split('?')[0]}"
        elif "watch?v=" in url:
            return f"https://www.youtube.com/embed/{url.split('watch?v=')[1].split('&')[0]}"
        return url
    videos = [to_embed(link) for link in raw_videos]

    # Newsletter subscription
    form = SubscriberForm()
    images = ImageModel.objects.all()
    if request.method == "POST":
        form = SubscriberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for subscribing!")
            return redirect("home")

    return render(request, "repair/home.html", {
        "videos": videos,
        "form": form,
        "folders": folders,
        "show_modal": show_modal,  # ✅ Pass modal flag to template
        "image" : images
    })

# firmware home
def firmware_home(request):
    folders = FirmwareFolder.objects.all()
    return render(request, 'repair/firmware/redmi_eng_firmware.html', {'folders': folders})

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import FirmwareFolder, Firmware, WindowsAppFile, MobileDriver, WindowsFirmware

# folder detail view
def folder_detail_view(request, folder_slug):
    folder = get_object_or_404(FirmwareFolder, slug=folder_slug)

    firmwares = []
    windows_files = []
    windows_iso = []
    drivers = []

    # Apply logic based on slug
    if folder_slug == "redmi_eng_firmware":
        firmwares = Firmware.objects.all().order_by('-name')

    elif folder_slug == "windows_app":
        windows_files = WindowsAppFile.objects.all().order_by('-uploaded_at')

    elif folder_slug == "mobile_driver_collection":
        query = request.GET.get("q", "")
        drivers = MobileDriver.objects.filter(
            Q(model__icontains=query) |
            Q(brand__icontains=query) |
            Q(chipset__icontains=query)
        ).order_by('brand', 'model')

    elif folder_slug == "windows_iso":
        windows_iso = WindowsFirmware.objects.all().order_by('-uploaded_at')

    return render(request, f'repair/firmware/{folder_slug}.html', {
        'folder': folder,
        'firmwares': firmwares,
        'windows_files': windows_files,
        'windows_iso': windows_iso,
        'drivers': drivers,
        'query': request.GET.get("q", ""),
    })

# def folder_detail_view(request, folder_slug):
#     folder = get_object_or_404(FirmwareFolder, slug=folder_slug)
#     firmwares = folder.firmwares.all()  # ✅ will now work
#     return render(request, f'repair/firmware/{folder.slug}.html', {
#         'folder': folder,
#         'firmwares': firmwares,
#         'files': [],  # optional
#     })

# generate invoice
def generate_invoice(request, repair_id):
    repair = get_object_or_404(RepairRequest, id=repair_id)
    # Generate invoice logic here...
    return render(request, 'repair/invoice.html', {'repair': repair})
# export pdf
def export_pdf(request):
    # Filter with safe parameters if needed, or just export all
    repairs = RepairRequest.objects.select_related('customer', 'technician').all()

    template_path = 'repair/pdf_template.html'
    context = {'repairs': repairs}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="repair_report.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors generating the PDF <pre>' + html + '</pre>')
    return response

# export csv
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="repair_requests.csv"'
    writer = csv.writer(response)
    writer.writerow(['Customer Name', 'Phone', 'Device Model', 'Issue', 'Technician', 'Status', 'Date Received'])

    for r in RepairRequest.objects.select_related('customer', 'technician'):
        writer.writerow([
            r.customer.name,
            r.customer.phone,
            r.device_model,
            r.issue_description,
            r.technician.name if r.technician else 'Not Assigned',
            r.get_status_display(),
            r.date_received.strftime('%Y-%m-%d'),
        ])

    return response

# sdd staff
def add_staff(request):
    if request.method == "POST":
        username = request.POST.get("staff_username")
        email = request.POST.get("staff_email")
        password = request.POST.get("staff_password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("add_staff")

        User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_staff=True
        )
        messages.success(request, f"✅ Staff '{username}' created successfully.")
        return redirect("profile")
    return redirect("profile")



# add customer account
def add_customer_account(request):
    if request.method == 'POST':
        username = request.POST.get('customer_username')
        email = request.POST.get('customer_email')
        password = request.POST.get('customer_password')
        name = request.POST.get('customer_name')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Customer.objects.create(user=user, name=name)
            messages.success(request, "Customer account created successfully.")
            return redirect('profile')  # or 'profile_info'

    return render(request, 'repair/profile_info.html')





# def add_customer(request):
#     if request.method == "POST":
#         name = request.POST.get("name").strip()
#         phone = request.POST.get("phone").strip()
#         address = request.POST.get("address", "").strip()
#
#         if name and phone:
#             # ✅ Check if customer already exists
#             if Customer.objects.filter(name__iexact=name, phone=phone).exists():
#                 messages.info(request, "Customer already exists.")
#             else:
#                 Customer.objects.create(name=name, phone=phone, address=address)
#                 messages.success(request, "Customer added successfully!")
#         else:
#             messages.error(request, "Please fill in the required fields.")
#
#         return redirect('home')  # Or your dashboard URL
#
#     return redirect(request, "repair/add_customer.html")  # fallback for GET requests

# add repair request
def Add_Repair_request(request):
    if request.method == 'POST':
        customer_name = request.POST.get("customer_name")
        device_model = request.POST.get("device_model")
        issue_description = request.POST.get("issue_description")
        technician_id = request.POST.get("technician")
        status = request.POST.get("status")
        repair_name = request.POST.get("repair_name")
        charge = request.POST.get("charge")
        bonus = request.POST.get("bonus")

        # Create or get a user with the same username as customer_name
        user, _ = User.objects.get_or_create(username=customer_name)

        # Create or get the Customer linked to this user
        customer, _ = Customer.objects.get_or_create(user=user, defaults={'name': customer_name})

        # Safely get technician object
        technician = None
        if technician_id:
            try:
                technician = Technician.objects.get(id=technician_id)
            except Technician.DoesNotExist:
                technician = None  # Fallback if ID is invalid

        # Create new repair request
        RepairRequest.objects.create(
            customer=customer,
            device_model=device_model,
            issue_description=issue_description,
            technician=technician,
            status=status,
            repair_name=repair_name,
            charge=charge or 0,
            bonus=bonus or 0
        )

        # Add success message ✅
        messages.success(request, "✅ Repair added successfully!")

        return redirect('add_repair_request')

    # For GET request, render form
    technicians = Technician.objects.all()
    return render(request, 'repair/add_repair.html', {'technicians': technicians})



# customer list
def customer_list(request):
    customers = Customer.objects.all().order_by('-id')  # Latest first
    return render(request, 'repair/customer_list.html', {'customers': customers})

# delete repair
def delete_repair(request, repair_id):
    repair = get_object_or_404(RepairRequest, pk=repair_id)
    repair.delete()
    return redirect('home')  #

# edit repair
def edit_repair(request, repair_id):
    repair = get_object_or_404(RepairRequest, id=repair_id)
    customers = Customer.objects.all()
    technicians = Technician.objects.all()

    if request.method == 'POST':
        repair.customer_id = request.POST.get('customer')
        repair.device_model = request.POST.get('device_model')
        repair.issue_description = request.POST.get('issue_description')

        tech_id = request.POST.get('technician')
        repair.technician_id = tech_id if tech_id else None
        repair.status = request.POST.get('status')
        repair.save()
        messages.success(request, "Repair request updated successfully.")
        return redirect('add_repair_request')

    return render(request, 'repair/edit_repair.html', {
        'repair': repair,
        'customers': customers,
        'technicians': technicians,
    })


@csrf_exempt
def grant_access_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        firmware_id = request.POST.get('firmware_id')

        try:
            user = User.objects.get(id=user_id)
            firmware = Firmware.objects.get(id=firmware_id)

            # Create access record (add has_paid=True if the model supports it)
            access_obj, created = FirmwareAccess.objects.get_or_create(
                user=user,
                firmware=firmware,
                defaults={'has_paid': True}  # only if has_paid exists in model
            )

            if not created:
                # Optional: update it if already exists
                access_obj.has_paid = True  # if field exists
                access_obj.save()

            return JsonResponse({'status': 'success', 'message': 'Access granted'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def firmware_info(request, firmware_id):
    firmware = get_object_or_404(Firmware, pk=firmware_id)
    has_access = False

    if request.user.is_authenticated:
        has_access = FirmwareAccess.objects.filter(
            user=request.user,
            firmware=firmware,
            has_paid=True
        ).exists()

    # Get back URL from referer
    back_url = request.META.get('HTTP_REFERER', '/')

    return render(request, 'repair/firmware/model_info.html', {
        'firmware': firmware,
        'has_access': has_access,
        'back_url': back_url,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)
                messages.info(request, "🔐 Session will expire when browser closes (Remember me unchecked).")
            else:
                request.session.set_expiry(1209600)  # 2 weeks
                messages.info(request, "✅ You will stay logged in (Remember me checked).")

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "❌ Invalid username or password.")

    return render(request, 'repair/login_register.html', {'form': form})



def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    merged_errors = []

    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data.get('full_name')
            user.email = form.cleaned_data.get('email')
            user.save()
            login(request, user)
            messages.success(request, f"Account created! Welcome, {user.username}")
            return redirect('login_register')
        else:
            # Handle field-specific errors
            for field in form.errors:
                if field in form.fields:
                    field_label = form.fields[field].label or field.replace("_", " ").title()
                    error_text = form.errors[field].as_text().replace("* ", "")
                    merged_errors.append(f"{field_label}: {error_text}")
                elif field == '__all__':
                    # Handle non-field errors (e.g. password mismatch)
                    for err in form.non_field_errors():
                        merged_errors.append(err)
    else:
        form = CustomRegisterForm()

    return render(request, 'repair/register.html', {
        'form': form,
        'merged_errors': merged_errors,
        'show_errors': request.method == 'POST',
    })




def logout_view(request):
    logout(request)
    return redirect('main')  # or wherever your login page is




@login_required
def technician_dashboard(request):
    accesses = FirmwareAccess.objects.filter(user=request.user).select_related('firmware')
    technicians = Technician.objects.all()
    return render(request, 'repair/technician_dashboard.html', {
        'accesses': accesses,
        'technicians': technicians
    })

# def technician_dashboard(request):
#     context = {
#         'technicians': Technician.objects.all()
#     }
#     return render(request, 'repair/technician_dashboard.html', context)


def add_technician(request):
    if request.method == 'POST':
        name = request.POST.get('technician_name', '').strip()
        phone = request.POST.get('technician_phone', '').strip()
        tech_type = request.POST.get('type', '').strip()

        if name and phone:
            # ✅ Check if technician with same name and phone already exists
            if Technician.objects.filter(name__iexact=name, phone=phone).exists():
                messages.info(request, "Technician already exists.")
            else:
                Technician.objects.create(name=name, phone=phone, type=tech_type)
                messages.success(request, "Technician added successfully.")
        else:
            messages.error(request, "Both name and phone are required.")

    return redirect('profile')


# views.py
def subscribe_view(request):
    if request.method == "POST":
        form = SubscriberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')  # or any success page
    else:
        form = SubscriberForm()

    return render(request, 'repair/subscribe.html', {'form': form})

# thext ssend emaill
# def add_technician(request):
#     send_mail(
#         'Test Email',
#         'This is a test email from Django.',
#         'repairmymobileimphal@gmail.com',
#         ['malemakcom@gmail.com'],
#         fail_silently=False,
#     )
#     return HttpResponse("Email sent")




class MyPasswordResetView(auth_views.PasswordResetView):
    template_name = 'repair/password_reset_form.html'
    email_template_name = 'repair/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class MyPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'repair/password_reset_done.html'

class MyPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'repair/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class MyPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'repair/password_reset_complete.html'



@login_required
def profile_view(request):
    device_models_qs = DeviceModel.objects.all().order_by('brand', 'model_name')
    paginator = Paginator(device_models_qs, 15)
    page_number_ = request.GET.get("page")
    page_obj_model = paginator.get_page(page_number_)

    bulk_form = BulkSamsungUploadForm()
    subscribe_form = SubscribeForm()

    if request.method == 'POST' and 'bulk_data' in request.POST:
        bulk_form = BulkSamsungUploadForm(request.POST)
        if bulk_form.is_valid():
            lines = bulk_form.cleaned_data['bulk_data'].strip().splitlines()
            objects = []
            for line in lines:
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    number = parts[1].strip()
                    support = parts[2].strip().lower() in ['yes', 'true', '1']
                    objects.append(SamsungModel(model_name=name, model_number=number, is_supported=support))
            SamsungModel.objects.bulk_create(objects)
            return redirect('profile')

    context = {
        'page_obj': page_obj_model,
        'accesses': FirmwareAccess.objects.filter(user=request.user),
        'technicians': Technician.objects.all(),
        'device_models': device_models_qs,
        'bulk_form': bulk_form,
        'subscribe_form': subscribe_form,  # ✅ added here
    }

    if request.user.is_superuser:
        context['admins'] = User.objects.filter(is_superuser=True)
        context['staffs'] = User.objects.filter(is_staff=True, is_superuser=False)
        context['customers'] = User.objects.filter(is_staff=False, is_superuser=False)
    elif request.user.is_staff:
        context['customers'] = User.objects.filter(is_staff=False, is_superuser=False)

    return render(request, 'repair/profile_info.html', context)





@login_required
def edit_profile(request):
    return render(request, 'repair/edit_profile.html')  # Create this template later



@login_required
def account(request):
    admins = User.objects.filter(is_superuser=True)
    staffs = User.objects.filter(is_staff=True, is_superuser=False)
    customers = User.objects.filter(is_staff=False, is_superuser=False)

    return render(request, 'repair/technician_dashboard.html', {
        'admins': admins,
        'staffs': staffs,
        'customers': customers,
    })


@login_required
def check_page(request):
    return render(request, 'repair/check_page.html', {
        'user': request.user,
        'ip': request.META.get('REMOTE_ADDR'),
        'agent': request.META.get('HTTP_USER_AGENT'),
    })

def device_model_suggestions(request):
    query = request.GET.get("term", "")
    results = DeviceModel.objects.filter(model_name__icontains=query)[:10]
    suggestions = [f"{d.brand} {d.model_name}" for d in results]
    return JsonResponse(suggestions, safe=False)

def add_phone_model(request):
    if request.method == 'POST':
        brand = request.POST.get('brand', '').strip()
        model_name = request.POST.get('model_name', '').strip()

        if brand and model_name:
            # Check if already exists
            if DeviceModel.objects.filter(brand__iexact=brand, model_name__iexact=model_name).exists():
                messages.warning(request, f"The model '{brand} {model_name}' already exists.")
            else:
                try:
                    DeviceModel.objects.create(brand=brand, model_name=model_name)
                    messages.success(request, "Phone model added successfully.")
                except IntegrityError:
                    messages.error(request, f"Could not add '{brand} {model_name}' — already exists.")
        else:
            messages.error(request, "Both brand and model name are required.")

    return redirect('profile_info')


def get_device_models(request):
    term = request.GET.get('term', '').strip()

    # Search both brand and model_name
    models = DeviceModel.objects.filter(
        Q(model_name__icontains=term) | Q(brand__icontains=term)
    ).distinct()[:10]

    suggestions = [f"{m.brand} {m.model_name}" for m in models]
    return JsonResponse(suggestions, safe=False)




@login_required
def delete_phone_model(request, model_id):
    if request.method == 'POST':
        try:
            DeviceModel.objects.get(id=model_id).delete()
            messages.success(request, "Model deleted.")
        except DeviceModel.DoesNotExist:
            messages.error(request, "Model not found.")
    return redirect('profile')


# def samsung_read_info(request):
#     if request.method == "POST":
#         model = request.POST.get("model")
#         imei = request.POST.get("imei")
#
#         # Process the data here...
#         messages.success(request, f"Model: {model}, IMEI: {imei} submitted successfully.")
#
#         return redirect("samsung_tools")  # Replace with your page URL name
#     return render(request, "repair/samsung_tools.html")



def samsung_read_info(request):
    if request.method == "POST":
        model = request.POST.get("model")
        imei = request.POST.get("imei")

        # Optional: validate/store info
        if len(imei) < 14:
            messages.error(request, "Invalid IMEI. Must be at least 14 digits.")
        else:
            messages.success(request, f"Model: {model}, IMEI: {imei} submitted!")

        return redirect("samsung_tools")
    return redirect("samsung_tools")

@login_required
def samsung_frp_support_list(request):
    samsung_models = SamsungModel.objects.all().order_by('model_name', 'model_number')
    return render(request, 'repair/samsung_frp_support_list.html', {
        'samsung_models': samsung_models
    })



def samsung_tools(request):
    if request.method == "POST":
        model = request.POST.get("model")
        imei = request.POST.get("imei")
        result = request.POST.get("result")
        created_at_str = request.POST.get("created_at")

        user_name = request.POST.get("user_name")
        email = request.POST.get("email")
        tool_id = request.POST.get("tool_id")
        plan = request.POST.get("plan")
        price = request.POST.get("price")

        try:
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S") if created_at_str else None
        except ValueError:
            created_at = None

        if not imei or len(imei) < 14:
            messages.error(request, "Invalid IMEI. Must be at least 14 digits.")
        else:
            SamsungOrder.objects.create(
                user=request.user,
                model=model,
                imei=imei,
                result=result,
                created_at=created_at,
                status="processing"
            )

            if tool_id and user_name and email and price:
                tool = get_object_or_404(ToolActivation, id=tool_id)
                PaymentConfirmation.objects.create(
                    user=request.user,
                    tool=tool,
                    user_name=user_name.strip(),
                    email=email,
                    month=plan,
                    amount=price,
                    payment_time=now(),
                    message=f"{plan} month(s) payment for {tool.name}"
                )

            messages.success(request, f"✅ Model: {model}, IMEI: {imei} and payment recorded.")
        return redirect("samsung_tools")

    # ✅ GET request: unified and separate search filters
    query = request.GET.get("q", "").strip()
    order_query = request.GET.get("order_search", "")
    payment_query = request.GET.get("payment_search", "")

    # Orders
    order_list = SamsungOrder.objects.filter(user=request.user)
    if query:
        order_list = order_list.filter(
            Q(custom_id=query) |
            Q(model__icontains=query) |
            Q(imei__icontains=query) |
            Q(status__icontains=query)
        )
    elif order_query:
        order_list = order_list.filter(
            Q(custom_id=query) |
            Q(model__icontains=order_query) |
            Q(imei__icontains=order_query) |
            Q(status__icontains=order_query)
        )
    order_list = order_list.order_by("-id")
    order_paginator = Paginator(order_list, 10)
    order_page = request.GET.get("order_page")
    orders = order_paginator.get_page(order_page)

    # Payments
    payment_list = PaymentConfirmation.objects.filter(user=request.user)
    if query:
        payment_list = payment_list.filter(
            Q(tool__name__icontains=query) |
            Q(month__icontains=query) |
            Q(amount__icontains=query) |
            Q(status__icontains=query)
        )
    elif payment_query:
        payment_list = payment_list.filter(
            Q(tool__name__icontains=payment_query) |
            Q(month__icontains=payment_query) |
            Q(amount__icontains=payment_query) |
            Q(status__icontains=payment_query)
        )
    payment_list = payment_list.order_by("-payment_time")
    payment_paginator = Paginator(payment_list, 10)
    payment_page1 = request.GET.get("payment_page")
    payments = payment_paginator.get_page(payment_page1)

    # All IMEI orders for admin
    orders_imei = IMEIOrder.objects.all().order_by('-created_at')

    return render(request, "repair/samsung_tools.html", {
        "orders": orders,
        "payments": payments,
        "order_query": order_query,
        "payment_query": payment_query,
        "query": query,
        "orders_imei": orders_imei,
    })


@user_passes_test(lambda u: u.is_staff)
def approve_order(request, order_id):
    order = get_object_or_404(SamsungOrder, id=order_id)

    if request.method == "POST":
        result = request.POST.get("result", "").strip()
        if result:
            order.result = result
            order.status = "done"  # Match status values used in dropdowns
            order.save()
            messages.success(request, f"✅ Order #{order.custom_id} approved successfully!")
        else:
            messages.warning(request, "⚠️ Result field cannot be empty.")
        return redirect("admin_dashboard")

    return render(request, "repair/approve_order.html", {"order": order})




@user_passes_test(lambda u: u.is_staff)
def update_order_status(request, order_id):
    order = get_object_or_404(SamsungOrder, id=order_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        result_text = request.POST.get("result", "").strip()

        updated = False

        # Update status
        if new_status in ["processing", "done", "rejected"] and order.status != new_status:
            order.status = new_status
            updated = True
            messages.success(request, f"✅ Order #{order.custom_id or order.id} status updated to '{new_status.capitalize()}'")

        # Update result
        if result_text and result_text != order.result:
            order.result = result_text
            updated = True
            messages.success(request, f"📝 Result info updated for Order #{order.custom_id or order.id}")

        if updated:
            order.save()
        else:
            messages.info(request, "⚠️ No changes detected.")

    return redirect("admin_dashboard")

#### ADMIN DASHBOARD FUNCTION
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    query = request.GET.get('q', '')

    # Samsung Order search
    samsung_orders = SamsungOrder.objects.all().order_by('-id')
    if query:
        samsung_orders = samsung_orders.filter(
            Q(custom_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(model__icontains=query) |
            Q(imei__icontains=query) |
            Q(result__icontains=query)
        )

    # Activation (Payment) search
    payments = PaymentConfirmation.objects.all().order_by('-payment_time')
    if query:
        payments = payments.filter(
            Q(user_name__icontains=query) |
            Q(tool__name__icontains=query) |
            Q(month__icontains=query) |
            Q(email__icontains=query)
        )

    # Paginate Samsung orders
    samsung_paginator = Paginator(samsung_orders, 10)
    samsung_page_number = request.GET.get('samsung_page')
    samsung_page_obj = samsung_paginator.get_page(samsung_page_number)

    # Paginate Payments
    payment_paginator = Paginator(payments, 10)
    payment_page_number = request.GET.get('payment_page')
    payment_page_obj = payment_paginator.get_page(payment_page_number)

    # All IMEI orders for admin
    orders_imei = IMEIOrder.objects.all().order_by('-created_at')

    return render(request, 'repair/admin_dashboard.html', {
        'orders': samsung_page_obj,
        'payments': payment_page_obj,
        'query': query,
        'orders_imei': orders_imei,
    })



@require_POST
@user_passes_test(lambda u: u.is_staff)
def update_payment_status(request, payment_id):
    payment = get_object_or_404(PaymentConfirmation, id=payment_id)
    payment.status = request.POST.get('status', payment.status)
    payment.message = request.POST.get('message', payment.message)
    payment.save()
    messages.success(request, "✅ Payment status updated.")
    return redirect('admin_dashboard')



def about(request):
    form = SubscribeForm()
    return render(request, 'repair/about.html', {'form': form})


def main_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to /home/ if already logged in

    return redirect('login_register')  # Or render a welcome/landing page if you have one


def tool_detail_view(request, tool_id):  # match the URL param name
    tool = get_object_or_404(ToolActivation, id=tool_id)
    plans = PricingPlan.objects.filter(tool=tool).order_by('duration_months')
    return render(request, 'repair/firmware/tool_detail.html', {
        'tool': tool,
        'plans': plans,
    })



def tools_activation_view(request):
    tools = ToolActivation.objects.all()
    return render(request, 'repair/firmware/mobile_tools_activation.html', {'tools': tools})


def payment_page(request, tool_id):
    tool = get_object_or_404(ToolActivation, id=tool_id)
    price = request.GET.get('price', '0')
    month = request.GET.get('month', '12')

    upi_id = "malemakcom-1@okhdfcbank"
    upi_url = f"upi://pay?pa={upi_id}&pn=Malem Akoijam&am={price}&cu=INR"

    # ✅ Generate QR code using Python
    qr = qrcode.make(upi_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    qr_code_base64 = f"data:image/png;base64,{img_str}"

    context = {
        "tool": tool,
        "price": price,
        "month": month,
        "upi_id": upi_id,
        "upi_url": upi_url,
        "qr_code_base64": qr_code_base64,  # 🔁 Use this in HTML
    }

    return render(request, 'repair/payment_model.html', context)


@login_required
def submit_activation(request):
    if request.method == 'POST':
        tool_id = request.POST.get('tool_id')
        price = request.POST.get('price')
        plan = request.POST.get('plan')
        user_name = request.POST.get('user_name') or request.user.username
        email = request.POST.get('email') or request.user.email

        tool = get_object_or_404(ToolActivation, id=tool_id)

        # ✅ Save payment confirmation
        payment = PaymentConfirmation.objects.create(
            tool=tool,
            user=request.user,
            user_name=user_name.strip(),
            email=email.strip(),
            amount=price,
            month=plan,
            payment_time=timezone.now(),
            message=f"{plan} plan confirmation by {user_name}",
        )

        # messages.success(request, "✅ Payment confirmation submitted successfully.")
        # 🔁 Redirect to detail page
        return redirect('activation_detail', payment_id=payment.id)

    return redirect('samsung_tools')



@login_required
def activation_detail(request, payment_id):
    payment = get_object_or_404(PaymentConfirmation, id=payment_id, user=request.user)
    return render(request, 'repair/activation_detail.html', {'payment': payment})


def activate_tool(request, tool_id):
    if request.method == 'POST':
        # ✅ Get the tool object or 404 if invalid ID
        tool = get_object_or_404(Tool, id=tool_id)

        # ✅ Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        plan = request.POST.get('plan')

        # ✅ Optional: Basic validation
        if not username or not email or not plan:
            messages.error(request, "All fields (username, email, plan) are required.")
            return redirect('tool_detail', tool_id=tool_id)

        # ✅ Create activation request record
        ActivationRequest.objects.create(
            tool=tool,
            username=username,
            email=email,
            plan=plan
        )

        # ✅ Confirmation message and redirect
        messages.success(request, f"✅ Activation requested for {tool.name} with plan {plan}")
        return redirect('tools_activation')

    # If not POST, redirect back
    return redirect('tools_activation')




# 📌 Show the IMEI order form
@login_required
def imei_order_view(request):
    services = IMEIService.objects.all()
    groups = IMEIService.objects.values_list('group', flat=True).distinct()
    return render(request, 'repair/imei_order.html', {
        'services': services,
        'groups': groups
    })


@login_required
def payment_model(request):
    if request.method == 'POST':
        service_name = request.POST.get('service_name')
        service_price_raw = request.POST.get('service_price')
        serial_numbers = request.POST.get('serial_numbers')
        frequent_use = request.POST.get('frequent_use') == 'on'

        # Validate price input
        try:
            service_price = Decimal(service_price_raw)
        except (InvalidOperation, TypeError):
            return render(request, "repair/payment_error.html", {
                "error": "Invalid price format. Please try again."
            })

        # Save order with validated price
        IMEIOrder.objects.create(
            user=request.user,
            service_name=service_name,
            service_price=service_price,  # FIXED: use the Decimal object
            serial_numbers=serial_numbers,
            frequent_use=frequent_use
        )

        return redirect('payment_success')

    return redirect('imei_order_view')

# 📌 Show success page
@login_required
def payment_success(request):
    return render(request, "repair/payment_success.html")


# 📌 View IMEI order history
@login_required
def imei_order_history(request):
    orders = IMEIOrder.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "repair/imei_order_history.html", {"orders": orders})

def update_imei_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(IMEIOrder, id=order_id)
        order.remarks = request.POST.get('remarks', '')
        order.save()
    return redirect('admin_dashboard')  # or wherever you want to go back


@login_required
def update_imei_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(IMEIOrder, id=order_id)

        # Optional: restrict update to staff or the user who placed the order
        if request.user != order.user and not request.user.is_staff:
            messages.error(request, "You don't have permission to update this order.")
            return redirect('admin_dashboard')  # Replace with your actual view name


        order.status = request.POST.get('status', order.status)
        order.remarks = request.POST.get('remarks', '')
        order.save()

        messages.success(request, "Order updated successfully.")

    return redirect(f'{reverse("admin_dashboard")}?updated={order_id}')



# create group
@user_passes_test(lambda u: u.is_superuser)
def create_group(request):
    if request.method == "POST":
        group_name = request.POST.get("name")
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                messages.success(request, f"✅ Group '{group_name}' created successfully.")
            else:
                messages.warning(request, f"⚠️ Group '{group_name}' already exists.")
            return redirect("list_groups")  # or change to another page if needed

    return render(request, "repair/group/create_group.html")


from django.contrib.auth.models import Group, Permission
def list_groups(request):
    groups = Group.objects.all()
    return render(request, 'repair/group/list_groups.html', {'groups': groups})

    group = get_object_or_404(Group, pk=group_id)
    all_permissions = Permission.objects.select_related('content_type').all()

    if request.method == 'POST':
        group.name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        group.permissions.set(permission_ids)
        group.save()
        messages.success(request, "Group updated successfully.")
        return redirect('list_groups')

def edit_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    all_permissions = Permission.objects.select_related('content_type').all()

    if request.method == 'POST':
        group.name = request.POST.get('name')
        permission_ids = request.POST.getlist('permissions')
        group.permissions.set(permission_ids)
        group.save()
        messages.success(request, "Group updated successfully.")
        return redirect('list_groups')

    return render(request, 'repair/group/edit_group.html', {
        'group': group,
        'all_permissions': all_permissions,
    })


def delete_group(request, group_id):
    Group.objects.filter(id=group_id).delete()
    messages.success(request, "Group deleted.")
    return redirect("list_groups")


def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    all_groups = Group.objects.all()

    if request.method == "POST":
        user.email = request.POST.get("email")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        selected_groups = request.POST.getlist("groups")
        user.groups.set(selected_groups)  # assign selected groups
        user.save()
        messages.success(request, "User updated successfully.")
        return redirect("manage_users")

    return render(request,"repair/users/edit_user.html", {
        "user_obj": user,
        "all_groups": all_groups,
    })


import json
import requests
from django.shortcuts import render
from django.contrib import messages
from django.utils.safestring import mark_safe

API_KEY = "568503aa-3bef-4777-acd6-dbf7306b8fce"

def imei_checker_view(request):
    services = []
    imei_data = None
    imei_json = ""
    error = None
    extracted = ""

    # Load services (GET or on load_services param)
    if request.method == "GET" or "load_services" in request.GET:
        try:
            res = requests.get(
                "https://dash.imei.info/api/service/services/",
                params={"API_KEY": API_KEY},
                headers={"accept": "application/json"},
                timeout=10
            )
            if res.status_code == 200:
                raw_services = res.json()
                services = [
                    {"id": s["id"], "name": s["name"]}
                    for s in raw_services
                    if s.get("name") and "id" in s
                ]
            elif res.status_code == 401:
                messages.error(request, "🔐 Invalid API token.")
            elif res.status_code == 403:
                messages.error(request, "🚫 No authentication provided.")
            elif res.status_code == 404:
                messages.error(request, "❌ Services not found.")
            else:
                messages.warning(request, f"⚠️ Unexpected error: {res.status_code}")
        except Exception as e:
            messages.error(request, f"❗ Service load failed: {e}")

    if request.method == "POST":
        imei = request.POST.get("imei", "").strip()
        imei2 = request.POST.get("imei2", "").strip()
        sn = request.POST.get("sn", "").strip()
        service_id = request.POST.get("service_id", "").strip()

        if not imei or not imei.isdigit() or len(imei) not in (14, 15):
            error = "❗ IMEI must be 14 or 15 digits."
        elif not service_id:
            error = "❗ Please select a valid service."
        else:
            try:
                url = f"https://dash.imei.info/api/check/{service_id}/"
                response = requests.get(
                    url,
                    params={"API_KEY": API_KEY, "imei": imei, "imei2": imei2, "sn": sn},
                    headers={"accept": "application/json"},
                    timeout=10
                )

                status = response.status_code
                if status == 200:
                    imei_data = response.json()
                    imei_json = mark_safe(json.dumps(imei_data, indent=2))
                    result = imei_data.get("result", {})
                    if isinstance(result, dict):
                        extracted = "\n".join([f"{k}: {v}" for k, v in result.items()])
                    else:
                        extracted = str(result)
                elif status == 202:
                    messages.info(request, "⏳ Result is processing. Try again later.")
                elif status == 401:
                    error = "🔐 Invalid API key."
                elif status == 403:
                    error = "🚫 Access denied."
                elif status == 404:
                    error = "❌ Service not found."
                elif status == 402:
                    error = "💰 Insufficient credits for this check."
                else:
                    error = f"⚠️ Unexpected response code: {status}"
            except Exception as e:
                error = f"❗ IMEI check error: {e}"

        # Reload services if empty
        if not services:
            try:
                res = requests.get(
                    "https://dash.imei.info/api/service/services/",
                    params={"API_KEY": API_KEY},
                    headers={"accept": "application/json"},
                    timeout=10
                )
                if res.status_code == 200:
                    raw_services = res.json()
                    services = [
                        {"id": s["id"], "name": s["name"]}
                        for s in raw_services
                        if s.get("name") and "id" in s
                    ]
            except:
                pass

    return render(request, "repair/check_imei.html", {
        "services": services,
        "imei_data": imei_data,
        "imei_json": imei_json,
        "extracted": extracted,
        "error": error
    })
