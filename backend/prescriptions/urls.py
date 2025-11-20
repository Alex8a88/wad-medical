from django.urls import path
from . import views

urlpatterns = [
    path('medicamentos/', views.MedicamentoListCreateView.as_view(), name='medicamento-list-create'),
    path('medicamentos/<int:pk>/', views.MedicamentoDetailView.as_view(), name='medicamento-detail'),
    path('medicos/', views.MedicoListView.as_view(), name='medico-list'),
    path('medicos/register/', views.doctor_register, name='doctor-register'),
    path('recetas/', views.RecetaListCreateView.as_view(), name='receta-list-create'),
    path('recetas/<int:pk>/', views.RecetaDetailView.as_view(), name='receta-detail'),
    path('recetas/<int:receta_id>/enviar/', views.enviar_receta_email, name='enviar-receta-email'),
    path('recetas/paciente/<str:num_afiliacion>/', views.recetas_by_patient, name='recetas-by-patient'),
]