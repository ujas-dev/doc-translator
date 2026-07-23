from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from apps.documents.models import DocumentJob
from apps.glossaries.models import Glossary, GlossaryEntry
from .models import QAScore, QARule
from .services import QAScoringService
from apps.core.decorators import plan_required


@login_required
@plan_required('qa')
def qa_dashboard(request):
    jobs = DocumentJob.objects.filter(user=request.user, status='completed').order_by('-created_at')[:20]
    return render(request, 'qa/dashboard.html', {'jobs': jobs})


@login_required
@plan_required('qa')
def qa_review(request, job_id):
    try:
        job = DocumentJob.objects.get(pk=job_id, user=request.user)
    except DocumentJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
    scores = QAScore.objects.filter(job=job).select_related('rule')
    return render(request, 'qa/review.html', {'job': job, 'scores': scores})


@login_required
@plan_required('qa')
def qa_run_check(request, job_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        job = DocumentJob.objects.get(pk=job_id, user=request.user)
    except DocumentJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    source_text = ''
    translation_text = ''

    if job.source_file:
        try:
            source_path = job.source_file.path
            with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_text = f.read()
        except Exception:
            pass

    if job.output_file:
        try:
            output_path = job.output_file.path
            with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
                translation_text = f.read()
        except Exception:
            pass

    glossary_terms = {}
    if hasattr(job, 'glossary') and job.glossary:
        for entry in job.glossary.entries.all()[:50]:
            glossary_terms[entry.source] = entry.target

    segments = [s.strip() for s in translation_text.split('\n') if s.strip()]

    results = QAScoringService.run_all_checks(
        source=source_text,
        translation=translation_text,
        glossary_terms=glossary_terms if glossary_terms else None,
        segments=segments if segments else None,
    )

    return JsonResponse({'results': results})
