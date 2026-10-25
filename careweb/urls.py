from django.urls import path

from . import views

app_name = 'careweb'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('our-care/', views.ServiceListView.as_view(), name='services'),
    path('our-care/<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('how-it-works/', views.HowItWorksView.as_view(), name='how_it_works'),
    path('faqs/', views.FAQView.as_view(), name='faqs'),
    path('careers/', views.CareersView.as_view(), name='careers'),
    path('careers/<slug:slug>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/thank-you/', views.ContactThanksView.as_view(), name='contact_thanks'),
    path('privacy/', views.LegalView.as_view(page='privacy'), name='privacy'),
    path('cookies/', views.LegalView.as_view(page='cookies'), name='cookies'),
    path('accessibility/', views.LegalView.as_view(page='accessibility'), name='accessibility'),
]
