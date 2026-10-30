from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'careapp'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.SecureLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('careapp:login')), name='logout'),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('settings/<slug:page>/', views.SettingsView.as_view(), name='settings'),
    path('<slug:section>/', views.SectionListView.as_view(), name='section_list'),
    path('<slug:section>/new/', views.SectionCreateView.as_view(), name='section_create'),
    path('<slug:section>/<int:pk>/', views.SectionUpdateView.as_view(), name='section_edit'),
    path('<slug:section>/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
]
