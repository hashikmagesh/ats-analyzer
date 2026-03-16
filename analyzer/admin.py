from django.contrib import admin
from .models import ResumeUpload, JobDescription, AnalysisResult


@admin.register(ResumeUpload)
class ResumeUploadAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'company_name', 'created_at']
    readonly_fields = ['created_at']


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['pk', 'resume', 'job_description', 'overall_score', 'status', 'created_at']
    readonly_fields = ['created_at']