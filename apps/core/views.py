from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse


def home(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and not profile.onboarding_completed:
            return redirect('onboarding_wizard')
        return render(request, 'documents/upload.html')
    return render(request, 'landing.html')


@login_required
def dashboard(request):
    from apps.documents.models import DocumentJob
    from django.db.models import Sum, Count, F
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    jobs = DocumentJob.objects.filter(user=request.user)

    status_filter = request.GET.get('status')
    if status_filter:
        jobs = jobs.filter(status=status_filter)

    source_lang = request.GET.get('source_lang')
    if source_lang:
        jobs = jobs.filter(source_language=source_lang)

    target_lang = request.GET.get('target_lang')
    if target_lang:
        jobs = jobs.filter(target_language=target_lang)

    date_range = request.GET.get('date_range')
    if date_range == 'today':
        jobs = jobs.filter(created_at__date=now.date())
    elif date_range == 'week':
        jobs = jobs.filter(created_at__gte=now - timedelta(days=7))
    elif date_range == 'month':
        jobs = jobs.filter(created_at__gte=now - timedelta(days=30))
    elif date_range == 'quarter':
        jobs = jobs.filter(created_at__gte=now - timedelta(days=90))

    jobs = jobs.order_by('-created_at')[:50]

    stats = {
        'total': DocumentJob.objects.filter(user=request.user).count(),
        'completed': DocumentJob.objects.filter(user=request.user, status='completed').count(),
        'processing': DocumentJob.objects.filter(user=request.user, status__in=['processing', 'queued']).count(),
        'failed': DocumentJob.objects.filter(user=request.user, status='failed').count(),
    }

    usage_stats = DocumentJob.objects.filter(
        user=request.user,
        created_at__gte=thirty_days_ago
    ).aggregate(
        total_pages=Sum('page_count'),
        total_characters=Sum('character_count'),
        total_jobs=Count('id'),
    )

    daily_usage = DocumentJob.objects.filter(
        user=request.user,
        created_at__gte=thirty_days_ago,
        status='completed'
    ).extra(
        select={'day': "date(created_at)"}
    ).values('day').annotate(
        jobs=Count('id'),
        pages=Sum('page_count'),
    ).order_by('day')

    for job in jobs:
        job.source_file_name = job.source_file.name.split('/')[-1] if job.source_file else 'Unknown'

    return render(request, 'documents/dashboard.html', {
        'jobs': jobs,
        'stats': stats,
        'usage_stats': usage_stats,
        'daily_usage': daily_usage,
    })


def pricing(request):
    current_plan = 'free'
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            current_plan = profile.plan or 'free'
    return render(request, 'billing/pricing.html', {'current_plan': current_plan})


@login_required
def onboarding_wizard(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.onboarding_completed:
        return redirect('home')

    user_plan = (profile.plan if profile else 'free') or 'free'
    has_glossary = user_plan in ('pro', 'team', 'enterprise')

    if request.method == 'POST':
        step = request.POST.get('step', 'welcome')

        if step == 'finish':
            if profile:
                profile.onboarding_completed = True
                profile.save(update_fields=['onboarding_completed'])
            return redirect('home')

        next_step = {
            'welcome': 'language',
            'language': 'glossary' if has_glossary else 'done',
            'glossary': 'done',
        }
        next_page = next_step.get(step, 'welcome')
        return render(request, f'onboarding/{next_page}.html', {
            'step': next_page,
            'user_plan': user_plan,
        })

    return render(request, 'onboarding/welcome.html', {'step': 'welcome', 'user_plan': user_plan})


@login_required
def onboarding_skip(request):
    profile = getattr(request.user, 'profile', None)
    if profile and not profile.onboarding_completed:
        profile.onboarding_completed = True
        profile.save(update_fields=['onboarding_completed'])
    return redirect('home')


def help_page(request):
    return render(request, 'help/index.html')
