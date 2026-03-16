# analyzer/forms.py

from django import forms
from .models import ResumeUpload, JobDescription


class ResumeUploadForm(forms.Form):
    """
    The form users fill out on the homepage.
    Handles both the resume file and job description text.
    """

    # ── Resume File Field ────────────────────────────
    resume_file = forms.FileField(
        label='Upload Your Resume',
        help_text='Accepted formats: PDF or DOCX (Max 10MB)',
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': '.pdf,.docx',  # Browser-level filter
            'id': 'resume-file-input',
        })
    )

    # ── Job Title Field ──────────────────────────────
    job_title = forms.CharField(
        label='Job Title',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Senior Python Developer',
            'id': 'job-title-input',
        })
    )

    # ── Company Name (Optional) ──────────────────────
    company_name = forms.CharField(
        label='Company Name (Optional)',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Google, Microsoft...',
        })
    )

    # ── Job Description Text ─────────────────────────
    job_description = forms.CharField(
        label='Paste Job Description',
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Paste the full job description here...',
            'rows': 12,
            'id': 'job-description-input',
        })
    )

    # ── Custom Validation ────────────────────────────
    def clean_resume_file(self):
        """
        This method runs automatically when the form is submitted.
        It checks that the file is a valid PDF or DOCX.
        """
        file = self.cleaned_data.get('resume_file')

        if file:
            # Check file extension
            filename = file.name.lower()
            if not (filename.endswith('.pdf') or filename.endswith('.docx')):
                raise forms.ValidationError(
                    'Invalid file type. Please upload a PDF or DOCX file only.'
                )

            # Check file size (10MB max)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    'File too large. Maximum size is 10MB.'
                )

        return file

    def clean_job_description(self):
        """Check that job description has enough content to analyze."""
        jd_text = self.cleaned_data.get('job_description', '')

        if len(jd_text.strip()) < 50:
            raise forms.ValidationError(
                'Job description is too short. Please paste the full job description (at least 50 characters).'
            )

        return jd_text