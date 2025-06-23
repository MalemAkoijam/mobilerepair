# Create your models here.
import math
import random
import string

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django import forms



class SamsungModel(models.Model):
    model_name = models.CharField(max_length=100)
    model_number = models.CharField(max_length=255)
    is_supported = models.BooleanField(default=False)

    def __str__(self):
        return self.model_name

class CustomRegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    login_ip = models.GenericIPAddressField(null=True, blank=True)
    agent = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username


class ImageModel(models.Model):
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Image {self.id}"

# models.py
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username} ({self.name})"


# models.py
class Technician(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    type = models.CharField(max_length=20, choices=[('Software', 'Software'), ('Hardware', 'Hardware')])

    def __str__(self):
        return f"{self.name} ({self.type})"



class RepairRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    device_model = models.CharField(max_length=100)
    issue_description = models.TextField()
    date_received = models.DateField(auto_now_add=True)
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    repair_name = models.CharField(max_length=255, blank=True, null=True)
    charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)


    def __str__(self):
        return f"{self.device_model} - {self.customer.name}"



# models.py
class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email




class Firmware(models.Model):
    folder = models.ForeignKey('FirmwareFolder', on_delete=models.CASCADE, related_name='firmwares')  # ✅ Add this line
    name = models.CharField(max_length=100)
    image = models.URLField()
    format_type = models.CharField(max_length=50)
    description = models.TextField()
    android_version = models.CharField(max_length=20)
    size = models.CharField(max_length=20)
    file_url = models.URLField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return ''




class FirmwareAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firmware = models.ForeignKey(Firmware, on_delete=models.CASCADE)
    has_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'firmware')  # Ensure one access per user per firmware

    def __str__(self):
        return f"{self.user.username} - {self.firmware.name}"


class DeviceModel(models.Model):
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('brand', 'model_name')

    def __str__(self):
        return f"{self.brand} {self.model_name}"


class FirmwareFolder(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)  # ✅ Make sure this is included!

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while FirmwareFolder.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name




# in models.py

class FileMixin:
    def formatted_size(self):
        if self.file_size == 0:
            return "0 Bytes"
        size_name = ("Bytes", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(self.file_size, 1024)))
        p = math.pow(1024, i)
        s = round(self.file_size / p, 2)
        return f"{s} {size_name[i]}"


### WIndow Firmware
class WindowsFirmware(models.Model, FileMixin):
    file_name = models.CharField(max_length=255)
    cloud_url = models.URLField()
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.file_name

### window file
class WindowsAppFile(models.Model):
    file_name = models.CharField(max_length=255)
    cloud_url = models.URLField()
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.file_name


def generate_custom_order_id():
    while True:
        custom_id = 'FRP-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not SamsungOrder.objects.filter(custom_id=custom_id).exists():
            return custom_id

class SamsungOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    custom_id = models.CharField(max_length=20, unique=True, editable=False, default=generate_custom_order_id)
    model = models.TextField()
    imei = models.CharField(max_length=17)
    result = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('rejected', 'Rejected')
    ], default='processing')

    def __str__(self):
        return f"{self.model} - {self.imei}"

# models.py
class ToolActivation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='tools/')
    plan_3_month = models.DecimalField(max_digits=2, decimal_places=0, default=0)
    plan_6_month = models.DecimalField(max_digits=2, decimal_places=0, default=0)
    plan_12_month = models.DecimalField(max_digits=2, decimal_places=0, default=0)
    price_3_month = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_6_month = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_12_month = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name



class PaymentConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    tool = models.ForeignKey(ToolActivation, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100)
    email = models.EmailField()
    month = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True)
    payment_time = models.DateTimeField(default=timezone.now)
    whatsapp_sent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="pending")  # Optional

    def __str__(self):
        return f"{self.user_name} - {self.tool.name} - ₹{self.amount}"




class PaymentConfirmationForm(forms.ModelForm):
    class Meta:
        model = PaymentConfirmation
        fields = ['user_name', 'email', 'message']


class PricingPlan(models.Model):
    tool = models.ForeignKey(ToolActivation, on_delete=models.CASCADE, related_name='pricing_plans')
    duration_months = models.PositiveIntegerField()  # 3, 6, 12
    old_price = models.DecimalField(max_digits=6, decimal_places=2)
    current_price = models.DecimalField(max_digits=6, decimal_places=2)
    package_code = models.CharField(max_length=10)
    label = models.CharField(max_length=20, blank=True, null=True)  # e.g., "Starter", "Popular"

    def __str__(self):
        return f"{self.tool.name} - {self.duration_months} Months - {self.package_code}"

# models.py
class ActivationRequest(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    tool = models.ForeignKey(ToolActivation, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.tool.name}"



class MobileDriver(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    chipset = models.CharField(max_length=100)
    download_link = models.URLField()

    def __str__(self):
        return f"{self.brand} {self.model}"

# models.py

class Tool(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='tools/')

    def __str__(self):
        return self.name



# IMEI Register
class IMEIOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    serial_numbers = models.TextField()
    frequent_use = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')

    def __str__(self):
        return f"{self.service_name} - {self.user.username}"


class IMEICategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class IMEIService(models.Model):
    GROUP_CHOICES = [
        ('iremoval_pro_v4_iphone', 'iRemoval Pro V4.0'),
        ('iremoval_pro_v3_ipad', 'iRemoval Pro V3.0'),
    ]

    name = models.CharField("Service Name", max_length=255)
    ios_supported = models.CharField("iOS Supported", max_length=100, blank=True)
    price = models.DecimalField("Price (₹)", max_digits=10, decimal_places=2)
    group = models.CharField("Device Group", max_length=50, choices=GROUP_CHOICES)
    category = models.ForeignKey(
        IMEICategory,
        on_delete=models.CASCADE,
        related_name='imei_services',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

