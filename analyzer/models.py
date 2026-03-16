# analyzer/models.py

from django.db import models
from django.utils import timezone


class ResumeUpload(models.Model):
    """
    Stores the uploaded resume file and extracted text.
    Think of this as one row in a spreadsheet — each upload gets its own row.
    """

    # File field — stores the actual PDF/DOCX file in media/resumes/
    resume_file = models.FileField(upload_to='resumes/')

    # Original filename (e.g. "john_resume.pdf")
    original_filename = models.CharField(max_length=255)

    # The raw text we extract from the resume (filled in Step 4)
    extracted_text = models.TextField(blank=True, null=True)

    # When was this uploaded?
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Resume: {self.original_filename} ({self.uploaded_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-uploaded_at']  # Newest first


class JobDescription(models.Model):
    """
    Stores the job description the user pastes in.
    """

    # Job title (e.g. "Senior Python Developer")
    job_title = models.CharField(max_length=255)

    # The full job description text
    job_text = models.TextField()

    # Company name (optional)
    company_name = models.CharField(max_length=255, blank=True, null=True)

    # ── ADD THIS FIELD ────────────────────────────
    # Stores the analyzed result as JSON
    analyzed_data = models.JSONField(default=dict, blank=True)
    # ─────────────────────────────────────────────


    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.job_title} at {self.company_name or 'Unknown Company'}"

    class Meta:
        ordering = ['-created_at']


class AnalysisResult(models.Model):
    """
    Stores the complete analysis result linking a resume to a job description.
    This is the central table — everything connects here.
    """

    # Link to the resume (if resume is deleted, delete this too)
    resume = models.ForeignKey(
        ResumeUpload,
        on_delete=models.CASCADE,
        related_name='analyses'
    )

    # Link to the job description
    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.CASCADE,
        related_name='analyses'
    )

    # ── Scores (0-100) ──────────────────────────────
    overall_score = models.FloatField(default=0.0)
    keyword_score = models.FloatField(default=0.0)
    skill_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)

    # ── ADD THIS ──────────────────────────────────────
    format_score     = models.FloatField(default=0.0)
    score_data       = models.JSONField(default=dict, blank=True)
    # ─────────────────────────────────────────────────

    # ── Analysis Data (stored as JSON text) ─────────
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    optimized_resume = models.TextField(blank=True, null=True)

    # ── Status tracking ──────────────────────────────
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Analysis #{self.pk} — Score: {self.overall_score:.1f}%"

    class Meta:
        ordering = ['-created_at']

