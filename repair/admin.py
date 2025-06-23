from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group

from .models import (Customer, Technician, RepairRequest, Firmware, FirmwareAccess,
                     FirmwareFolder, DeviceModel, Profile, \
                     WindowsAppFile, WindowsFirmware, ImageModel, SamsungOrder, ToolActivation, PricingPlan,
                     MobileDriver, ActivationRequest, IMEICategory, IMEIService, IMEIOrder)
from .models import Subscriber

admin.site.register(ImageModel)
admin.site.register(Profile)
admin.site.register(Customer)
admin.site.register(Technician)
admin.site.register(RepairRequest)

admin.site.register(Subscriber)
admin.site.register(Firmware)
admin.site.register(FirmwareAccess)
admin.site.register(DeviceModel)
admin.site.register(FirmwareFolder)
admin.site.register(WindowsAppFile)
admin.site.register(WindowsFirmware)
admin.site.register(SamsungOrder)
admin.site.register(ToolActivation)
admin.site.register(PricingPlan)
admin.site.register(MobileDriver)
admin.site.register(ActivationRequest)

# IMEI Category Admin
@admin.register(IMEICategory)
class IMEICategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# IMEI Service Admin
@admin.register(IMEIService)
class IMEIServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'category', 'price', 'ios_supported')
    list_filter = ('group', 'category')
    search_fields = ('name', 'ios_supported')
    list_editable = ('price',)

@admin.register(IMEIOrder)
class IMEIOrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'service_name', 'service_price', 'frequent_use', 'created_at']

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)