"""
URL configuration for projet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from goodDoctor import views


#from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Afficher directement goodDoctor sur la page d'accueil
    #path('goodDoctor/', views.index, name='goodDoctor'),
    path('register/', views.register_patient, name='register'),
    path('register_medecin/', views.register_medecin, name='register_medecin'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Pour la déconnexion
    # path('medecin_dashboard/', views.medecin_dashboard, name='medecin_dashboard'),
    # path('patient_dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/medecin/', views.medecin_dashboard, name='medecin_dashboard'),
    path('dashboard/responsable/', views.dashboard_responsable, name='dashboard_responsable'),
    path('recherche_medecin/', views.recherche_medecin, name='recherche_medecin'),
    path('prendre_rendez_vous/<int:medecin_id>/', views.prendre_rendez_vous, name='prendre_rendez_vous'),

]
