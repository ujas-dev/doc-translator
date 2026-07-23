from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import TMEntry
from .services import TranslationMemoryService
from apps.core.decorators import plan_required


@login_required
@plan_required('tm')
def tm_list(request):
    entries = TMEntry.objects.filter(user=request.user)[:50]
    return render(request, 'memory/list.html', {'entries': entries})


@login_required
@plan_required('tm')
def tm_add(request):
    if request.method == 'POST':
        TranslationMemoryService.add_entry(
            user=request.user,
            source_lang=request.POST.get('source_lang', 'en'),
            target_lang=request.POST.get('target_lang', 'hi'),
            source_text=request.POST.get('source_text', ''),
            target_text=request.POST.get('target_text', ''),
            context=request.POST.get('context', ''),
        )
        messages.success(request, 'Entry added to translation memory.')
        return redirect('tm_list')
    return render(request, 'memory/add.html')


@login_required
@plan_required('tm')
def tm_delete(request, pk):
    entry = TMEntry.objects.filter(pk=pk, user=request.user).first()
    if entry and request.method == 'POST':
        entry.delete()
        messages.success(request, 'Entry deleted.')
    return redirect('tm_list')


@login_required
@plan_required('tm')
def tm_export(request, source_lang, target_lang):
    tmx_content = TranslationMemoryService.export_tmx(request.user, source_lang, target_lang)
    response = HttpResponse(tmx_content, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="tm_{source_lang}_{target_lang}.tmx"'
    return response


@login_required
@plan_required('tm')
def tm_leverage(request):
    """Return TM leverage percentage for a given text."""
    text = request.GET.get('text', '')
    source_lang = request.GET.get('source_lang', 'en')
    target_lang = request.GET.get('target_lang', 'hi')

    if not text:
        return JsonResponse({'error': 'text is required'}, status=400)

    matches = TranslationMemoryService.find_matches(
        user=request.user,
        source_lang=source_lang,
        target_lang=target_lang,
        text=text,
        threshold=0.5,
    )

    total_chars = len(text)
    matched_chars = 0
    for match in matches:
        matched_chars += len(match['source'])

    leverage = min(100, round((matched_chars / total_chars * 100), 1)) if total_chars > 0 else 0

    return JsonResponse({
        'leverage_percentage': leverage,
        'total_segments': len(matches),
        'matches': matches[:10],
    })
