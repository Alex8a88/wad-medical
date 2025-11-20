from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.patient_register, name='patient_register'),
    path('search/', views.patient_search, name='patient_search'),
    path('upload-to-drive/', views.upload_patient_to_drive, name='upload_patient_to_drive'),
    path('<str:num_afiliacion>/', views.patient_detail, name='patient_detail'),
    path('<str:num_afiliacion>/update/', views.patient_update, name='patient_update'),
]