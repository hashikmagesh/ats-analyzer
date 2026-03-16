# analyzer/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),           # Homepage
    path('analyze/', views.analyze, name='analyze'),  # Analysis endpoint
    path('results/<int:pk>/', views.results, name='results'),  # Results page
    path('rewrite/<int:pk>/', views.rewrite, name='rewrite'),
    path('debug/<int:pk>/', views.debug_analysis, name='debug'),
    path('export/<int:pk>/pdf/',  views.export_pdf,  name='export_pdf'),   # ← ADD
    path('export/<int:pk>/docx/', views.export_docx, name='export_docx'),
]