import os
import json
import re
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .forms import ResumeUploadForm
from .models import ResumeUpload, JobDescription, AnalysisResult
from .services.resume_extractor import extract_resume_text
from .services.section_detector import detect_sections
from .services.jd_analyzer import analyze_job_description 
from .services.skill_extractor import extract_resume_skills
from .services.semantic_matcher import match_skills 
from .services.ats_scorer import calculate_ats_score 
from .services.gap_analyzer import analyze_skill_gaps
from .services.ai_suggester import generate_suggestions
from .services.resume_rewriter import rewrite_resume
from django.http import HttpResponse
from .services.resume_exporter import (
    export_as_pdf,
    export_as_docx,
    extract_candidate_name,
)

def home(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)

        if form.is_valid():
            resume_file  = form.cleaned_data['resume_file']
            job_title    = form.cleaned_data['job_title']
            company_name = form.cleaned_data.get('company_name', '')
            jd_text      = form.cleaned_data['job_description']

            # ── Save resume ───────────────────────────
            resume = ResumeUpload.objects.create(
                resume_file=resume_file,
                original_filename=resume_file.name,
            )

            # ── Extract text ──────────────────────────
            file_path = os.path.join(
                settings.MEDIA_ROOT,
                resume.resume_file.name
            )
            extraction = extract_resume_text(file_path)

            if extraction['success']:
                resume.extracted_text = extraction['text']
                resume.save()

                # ── Detect sections ───────────────────
                sections = detect_sections(extraction['text'])

            else:
                sections = {}
                messages.warning(
                    request,
                    f'⚠️ Extraction issue: {extraction["error"]}'
                )

            # ── Extract resume skills ─────────────────
            resume_skills_data = {}
            resume_skills_list = []
            if extraction['success']:
                resume_skills_data = extract_resume_skills(
                    extraction['text'], sections
                )
                resume_skills_list = resume_skills_data.get(
                    'all_skills', []
                )

            # ── Analyze job description ───────────────
            jd_analysis = analyze_job_description(jd_text)

            # ── Semantic matching ─────────────────────
            match_result = match_skills(
                resume_skills  = resume_skills_list,
                jd_required    = jd_analysis.get(
                    'required_skills', []
                ),
                jd_preferred   = jd_analysis.get(
                    'preferred_skills', []
                ),
            )

            # ── Calculate ATS score ───────────────────
            ats_score = calculate_ats_score(
                resume_text   = extraction.get('text', ''),
                sections      = sections,
                resume_skills = resume_skills_data,
                jd_data       = jd_analysis,
                match_result  = match_result,
            )

            # ── Analyze skill gaps ────────────────────────
            gap_analysis = analyze_skill_gaps(
                missing_skills = match_result.get(
                    'missing_required', []
                ),
                resume_skills  = resume_skills_data,
                jd_data        = jd_analysis,
                match_result   = match_result,
            )

            # ── Generate suggestions ──────────────────────
            suggestions = generate_suggestions(
                resume_text   = extraction.get('text', ''),
                sections      = sections,
                resume_skills = resume_skills_data,
                jd_data       = jd_analysis,
                match_result  = match_result,
                ats_score     = ats_score,
            )

            # ── Save job description with analysis ────
            job_desc = JobDescription.objects.create(
                job_title=job_title,
                company_name=company_name,
                job_text=jd_text,
                analyzed_data=jd_analysis,      # ← save analysis
            )

            analysis = AnalysisResult.objects.create(
                resume=resume,
                job_description=job_desc,
                status='completed',

                # Save all scores
                overall_score    = ats_score['overall_score'],
                skill_score      = ats_score['skill_score'],
                keyword_score    = ats_score['keyword_score'],
                experience_score = ats_score['experience_score'],
                education_score  = ats_score['education_score'],
                format_score     = ats_score['format_score'],
                score_data       = ats_score,

                # Save skill data
                matched_skills   = match_result.get(
                    'matched_required', []
                ),
                missing_skills   = match_result.get(
                    'missing_required', []
                ),
                suggestions = suggestions.get('critical', []) +
                  suggestions.get('improvements', []),

            )

            messages.success(
                request,
                f'✅ ATS Analysis complete! '
                f'Your score: {ats_score["overall_score"]}/100 '
                f'(Grade: {ats_score["grade"]})'
            )

            return redirect('results', pk=analysis.pk)

        else:
            messages.error(request, 'Please fix the errors below.')

    else:
        form = ResumeUploadForm()

    return render(request, 'upload.html', {'form': form})


def analyze(request):
    """Placeholder — full logic coming in Steps 6-12"""
    return redirect('home')


def rewrite(request, pk):
    """
    Runs AI rewrite on demand when user clicks the button.
    Saves result to AnalysisResult.optimized_resume.
    """
    try:
        analysis = AnalysisResult.objects.get(pk=pk)
    except AnalysisResult.DoesNotExist:
        messages.error(request, 'Analysis not found.')
        return redirect('home')

    force = request.GET.get('force', '0') == '1'
    # Only rewrite if not done OR force=1
    if not analysis.optimized_resume or force:

        resume_text = analysis.resume.extracted_text or ''
        sections    = detect_sections(resume_text)
        sections.pop('_metadata', {})

        jd_data      = analysis.job_description.analyzed_data or {}
        resume_skills = extract_resume_skills(
            resume_text, sections
        )
        match_result = match_skills(
            resume_skills = resume_skills.get('all_skills', []),
            jd_required   = jd_data.get('required_skills', []),
            jd_preferred  = jd_data.get('preferred_skills', []),
        )

        # Get gap analysis for context
        from .services.gap_analyzer import analyze_skill_gaps
        gap_analysis = analyze_skill_gaps(
            missing_skills = match_result.get(
                'missing_required', []
            ),
            resume_skills  = resume_skills,
            jd_data        = jd_data,
            match_result   = match_result,
        )

        # Run the rewriter
        rewrite_result = rewrite_resume(
            resume_text  = resume_text,
            sections     = sections,
            jd_data      = jd_data,
            match_result = match_result,
            gap_analysis = gap_analysis,
        )

        # Save to DB
        import json
        analysis.optimized_resume = json.dumps({
            'text':     rewrite_result.get(
                'optimized_resume', ''
            ),
            'changes':  rewrite_result.get(
                'changes_made', []
            ),
            'sections': rewrite_result.get(
                'sections_rewritten', []
            ),
            'ai':       rewrite_result.get(
                'ai_powered', False
            ),
            'model':    rewrite_result.get(
                'model_used', ''
            ),
        })
        analysis.save()

        if rewrite_result.get('ai_powered'):
            messages.success(
                request,
                f'🤖 AI rewrite complete using '
                f'{rewrite_result["model_used"]}!'
            )
        else:
            messages.info(
                request,
                '✅ Resume optimized using rule-based engine. '
                'Add an API key for AI-powered rewriting.'
            )
    else:
        messages.info(
            request, 'Using previously generated rewrite.'
        )

    return redirect('results', pk=pk)

def results(request, pk):
    try:
        analysis = AnalysisResult.objects.get(pk=pk)
    except AnalysisResult.DoesNotExist:
        messages.error(request, 'Analysis not found.')
        return redirect('home')

    sections = {}
    sections_found = []

    resume_skills  = {}
    match_result   = {}

    ats_score      = {}
    
    import json
    rewrite_data = {}
    if analysis.optimized_resume:
        try:
            rewrite_data = json.loads(analysis.optimized_resume)
        except Exception:
            rewrite_data = {}

    if analysis.resume.extracted_text:
        sections = detect_sections(analysis.resume.extracted_text)
        # Fix: Django templates can't access underscore keys like _metadata
        # So we pop it out and pass it separately
        meta = sections.pop('_metadata', {})
        sections_found = meta.get('sections_found', [])

        # Re-run skill extraction for display
        resume_skills = extract_resume_skills(
            analysis.resume.extracted_text,
            sections
        )

        # Run semantic matching
        jd_data      = analysis.job_description.analyzed_data or {}
        match_result = match_skills(
            resume_skills  = resume_skills.get('all_skills', []),
            jd_required    = jd_data.get('required_skills', []),
            jd_preferred   = jd_data.get('preferred_skills', []),
        )

        #gap_analysis
        gap_analysis = analyze_skill_gaps(
            missing_skills = match_result.get('missing_required', []),
            resume_skills  = resume_skills,
            jd_data        = jd_data,
            match_result   = match_result,
        )

        suggestions = generate_suggestions(
            resume_text   = analysis.resume.extracted_text,
            sections      = sections,
            resume_skills = resume_skills,
            jd_data       = jd_data,
            match_result  = match_result,
            ats_score     = ats_score,
        )

        # Use saved score or recalculate
        if analysis.score_data:
            ats_score = analysis.score_data
        else:
            ats_score = calculate_ats_score(
                resume_text   = analysis.resume.extracted_text,
                sections      = sections,
                resume_skills = resume_skills,
                jd_data       = jd_data,
                match_result  = match_result,
            )

     # ── Get JD analysis data ──────────────────────
    jd_data = analysis.job_description.analyzed_data or {}

    return render(request, 'results.html', {
        'analysis': analysis,
        'sections': sections,
        'sections_found': sections_found,  # ← now passed separately
        'jd_data' : jd_data,   # ← pass to template
        'resume_skills':  resume_skills,
        'match_result':   match_result,     # ← ADD
        'ats_score':      ats_score,        # ← ADD
        'gap_analysis':   gap_analysis, 
        'suggestions': suggestions,
        'rewrite_data': rewrite_data,
    })

def debug_analysis(request, pk):
    """
    Temporary debug view — visit /debug/1/ to see 
    exactly what was extracted and detected.
    Remove this after debugging is done.
    """
    try:
        analysis = AnalysisResult.objects.get(pk=pk)
    except AnalysisResult.DoesNotExist:
        return JsonResponse({'error': 'Not found'})

    extracted = analysis.resume.extracted_text or ''
    sections = detect_sections(extracted) if extracted else {}

    return JsonResponse({
        '1_file_saved':       str(analysis.resume.resume_file),
        '2_extracted_length': len(extracted),
        '3_extracted_preview': extracted[:300],
        '4_sections_detected': sections.get('_metadata', {}),
        '5_summary_found':    bool(sections.get('summary')),
        '6_experience_found': bool(sections.get('experience')),
        '7_skills_found':     bool(sections.get('skills')),
        '8_education_found':  bool(sections.get('education')),
    }, json_dumps_params={'indent': 2})

# ─────────────────────────────────────────────────────
def export_pdf(request, pk):
    """
    Generates and streams the optimized resume as PDF.
    """
    try:
        analysis = AnalysisResult.objects.get(pk=pk)
    except AnalysisResult.DoesNotExist:
        messages.error(request, 'Analysis not found.')
        return redirect('home')

    # Get resume text — prefer optimized, fallback original
    resume_text = _get_export_text(analysis)

    if not resume_text:
        messages.error(
            request,
            'No resume text available. '
            'Please run the rewriter first.'
        )
        return redirect('results', pk=pk)

    # Extract candidate name for filename
    name     = extract_candidate_name(resume_text)
    safe     = re.sub(r'[^\w\s-]', '', name).strip()
    filename = f"{safe}_ATS_Optimized.pdf" \
               if safe else "ATS_Optimized_Resume.pdf"

    try:
        pdf_bytes = export_as_pdf(resume_text, name)

        response = HttpResponse(
            pdf_bytes,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"'
        )
        return response

    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        messages.error(
            request,
            f'PDF export failed: {str(e)}'
        )
        return redirect('results', pk=pk)


def export_docx(request, pk):
    """
    Generates and streams the optimized resume as DOCX.
    """
    try:
        analysis = AnalysisResult.objects.get(pk=pk)
    except AnalysisResult.DoesNotExist:
        messages.error(request, 'Analysis not found.')
        return redirect('home')

    resume_text = _get_export_text(analysis)

    if not resume_text:
        messages.error(
            request,
            'No resume text available. '
            'Please run the rewriter first.'
        )
        return redirect('results', pk=pk)

    name     = extract_candidate_name(resume_text)
    safe     = re.sub(r'[^\w\s-]', '', name).strip()
    filename = f"{safe}_ATS_Optimized.docx" \
               if safe else "ATS_Optimized_Resume.docx"

    try:
        docx_bytes = export_as_docx(resume_text, name)

        response = HttpResponse(
            docx_bytes,
            content_type=(
                'application/vnd.openxmlformats-'
                'officedocument.wordprocessingml.document'
            )
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"'
        )
        return response

    except Exception as e:
        logger.error(f"DOCX export failed: {e}")
        messages.error(
            request,
            f'DOCX export failed: {str(e)}'
        )
        return redirect('results', pk=pk)


# ─────────────────────────────────────────────────────
# HELPER: Get best available resume text for export
# ─────────────────────────────────────────────────────
def _get_export_text(analysis):
    """
    Returns optimized text if available,
    otherwise falls back to original extracted text.
    """
    # Try optimized resume first
    if analysis.optimized_resume:
        try:
            data = json.loads(analysis.optimized_resume)
            text = data.get('text', '').strip()
            if text:
                return text
        except Exception:
            pass

    # Fallback to original extracted text
    return analysis.resume.extracted_text or ''