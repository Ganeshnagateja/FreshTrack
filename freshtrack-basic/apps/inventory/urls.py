from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("inventory/", views.inventory_list, name="inventory_list"),
    path("inventory/new/", views.inventory_create, name="inventory_create"),
    path("inventory/import/", views.inventory_import, name="inventory_import"),
    path("inventory/template.csv", views.csv_template, name="csv_template"),
    path("inventory/<int:pk>/edit/", views.inventory_update, name="inventory_update"),
    path("alerts/", views.alert_center, name="alert_center"),
]
