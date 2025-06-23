"""
URL configuration for mobilerepair project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from tkinter.font import names

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from repair import views
from django.conf import settings
from django.conf.urls.static import static

from repair.sitemaps import StaticViewSitemap
from repair.views_api import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
sitemaps = {
    'static': StaticViewSitemap,
}

from repair.views import home, MyPasswordResetView, MyPasswordResetDoneView, MyPasswordResetConfirmView, \
    MyPasswordResetCompleteView


urlpatterns = [
    # 🔧 Admin
    path('admin/', admin.site.urls),
    path('', views.main_view, name='main'),  # Root URL


    # 🔐 Authentication
    path('login', views.login_view, name='login_register'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # 🏠 Dashboard & Home
    path('home/', views.home, name='home'),
    path('technician_dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('add_repair_request/', views.repair_add_request, name='add_repair_request'),

    # 📁 Firmware Management
    path('firmware/<slug:folder_slug>/', views.folder_detail_view, name='folder_detail'),
    path('firmwares/<int:firmware_id>/', views.firmware_info, name='firmware_info'),


    # 🛠️ Repair Services
    path('add_repair/', views.Add_Repair_request, name='add_repair'),
    path('edit_repair/<int:repair_id>/', views.edit_repair, name='edit_repair'),
    path('delete_repair/<int:repair_id>/', views.delete_repair, name='delete_repair'),
    path('generate_invoice/', views.Add_Repair_request, name='generate_invoice'),  # Optional shortcut
    path('generate_invoice/<int:repair_id>/', views.generate_invoice, name='generate_invoice'),
    path('pdf_template/', views.delete_repair, name='pdf_template'),  # ⚠️ Confirm view logic

    # 👥 Customer & Staff
    path("add_customer_ac/", views.add_customer_account, name="add_customer_account"),
    path('add_technician/', views.add_technician, name='add_technician'),
    path('add_staff/', views.add_staff, name='add_staff'),

    # 📦 Phone Model / Device Details
    path('add_phone_model/', views.add_phone_model, name='add_phone_model'),
    path('get-device-models/', views.get_device_models, name='get_device_models'),
    path('delete-phone-model/<int:model_id>/', views.delete_phone_model, name='delete_phone_model'),

    # ⚙️ Profile & Account
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # 📤 Export
    path('export-csv/', views.export_csv, name='export_csv'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),

    # 🔐 Password Reset
    path("reset_password/", views.MyPasswordResetView.as_view(), name="password_reset"),
    path("reset_password_sent/", views.MyPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.MyPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('reset_password_complete/', views.MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),


    # 🔔 Subscriptions & Access
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('grant-access/', views.grant_access_view, name='grant_access'),

    # 📱 Samsung Tools
    path('samsung/tools/', views.samsung_tools, name='samsung_tools'),  # Samsung-specific
    path('samsung/read-info/', views.samsung_read_info, name='samsung_read_info'),
    path('samsung-frp-support/', views.samsung_frp_support_list, name='samsung_frp_support_list'),

    path('tools/', views.tools_activation_view, name='tools_activation'),
    path('tools/<int:tool_id>/', views.tool_detail_view, name='tool_detail'),
    path('activate/<int:tool_id>/', views.activate_tool, name='activate_tool'),
    path('payment/<int:tool_id>/', views.payment_page, name='payment_page'),
    path('submit-activation/', views.submit_activation, name='submit_activation'),
    path('activation/<int:payment_id>/', views.activation_detail, name='activation_detail'),


    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("update-order-status/<int:order_id>/", views.update_order_status, name="update_order_status"),
    path('update-payment/<int:payment_id>/', views.update_payment_status, name='update_payment_status'),


    path("approve-order/<int:order_id>/", views.approve_order, name="approve_order"),

    #Imei icloud

    path('imei-order/', views.imei_order_view, name='imei_order_view'),
    path("submit-order/", views.payment_model, name="payment_model"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("order-history/", views.imei_order_history, name="imei_order_history"),
    path('update-imei-order/<int:order_id>/', views.update_imei_order, name='update_imei_order'),
    # path('imei/dashboard/', views.imei_dashboard, name='imei_dashboard'),





    ### setting
    path('settings/', views.user_settings, name='user_settings'),
    path('settings/update-profile/', views.update_profile, name='update_profile'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/manage-users/', views.manage_users, name='manage_users'),
    path('settings/site-config/', views.site_config, name='site_config'),
    path('settings/add_user/', views.manage_users, name='add_user'),

    path('settings/edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('settings/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('settings/activate-user/<int:user_id>/', views.activate_user, name='activate_user'),
    path('settings/deactivate-user/<int:user_id>/', views.deactivate_user, name='deactivate_user'),

    path('api/', include(router.urls)),

    path("settings/create-group/", views.create_group, name="create_group"),
    path("settings/groups/", views.list_groups, name="list_groups"),
    path("settings/edit-group/<int:group_id>/", views.edit_group, name="edit_group"),
    path("settings/delete-group/<int:group_id>/", views.delete_group, name="delete_group"),
    # customer view
    path('customers/', views.customer_list, name='view_repairs'),
    path('check-imei/', views.imei_checker_view, name='check_imei_info'),








]

# ⚙️ Static/Media Files for Development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




