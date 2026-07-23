from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Glossary, GlossaryEntry
from .forms import GlossaryForm, GlossaryEntryForm, CSVImportForm
from .services import GlossaryService
from .export import export_tbx, export_xliff
from apps.core.decorators import plan_required


@login_required
@plan_required('glossary')
def glossary_list(request):
    glossaries = Glossary.objects.filter(user=request.user)
    return render(request, 'glossaries/list.html', {'glossaries': glossaries})


@login_required
@plan_required('glossary')
def glossary_create(request):
    if request.method == 'POST':
        form = GlossaryForm(request.POST)
        if form.is_valid():
            glossary = form.save(commit=False)
            glossary.user = request.user
            glossary.save()
            messages.success(request, 'Glossary created.')
            return redirect('glossary_detail', pk=glossary.pk)
    else:
        form = GlossaryForm()
    return render(request, 'glossaries/create.html', {'form': form})


@login_required
@plan_required('glossary')
def glossary_detail(request, pk):
    glossary = get_object_or_404(Glossary, pk=pk, user=request.user)
    entries = glossary.entries.all()
    entry_form = GlossaryEntryForm()
    import_form = CSVImportForm()

    if request.method == 'POST':
        if 'add_entry' in request.POST:
            entry_form = GlossaryEntryForm(request.POST)
            if entry_form.is_valid():
                entry = entry_form.save(commit=False)
                entry.glossary = glossary
                entry.save()
                messages.success(request, 'Entry added.')
                return redirect('glossary_detail', pk=pk)

        elif 'import_csv' in request.POST:
            import_form = CSVImportForm(request.POST, request.FILES)
            if import_form.is_valid():
                csv_file = request.FILES['file']
                content = csv_file.read().decode('utf-8')
                result = GlossaryService.import_csv(glossary, content)
                messages.success(request, f"Imported {result['created']} entries, skipped {result['skipped']}.")
                return redirect('glossary_detail', pk=pk)

    return render(request, 'glossaries/detail.html', {
        'glossary': glossary,
        'entries': entries,
        'entry_form': entry_form,
        'import_form': import_form,
    })


@login_required
@plan_required('glossary')
def glossary_delete(request, pk):
    glossary = get_object_or_404(Glossary, pk=pk, user=request.user)
    if request.method == 'POST':
        glossary.delete()
        messages.success(request, 'Glossary deleted.')
        return redirect('glossary_list')
    return render(request, 'glossaries/delete.html', {'glossary': glossary})


@login_required
@plan_required('glossary')
def glossary_export(request, pk):
    glossary = get_object_or_404(Glossary, pk=pk, user=request.user)
    export_format = request.GET.get('format', 'csv')

    if export_format == 'tbx':
        content = export_tbx(glossary)
        response = HttpResponse(content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{glossary.name}.tbx"'
    elif export_format == 'xliff':
        content = export_xliff(glossary)
        response = HttpResponse(content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{glossary.name}.xliff"'
    else:
        content = GlossaryService.export_csv(glossary)
        response = HttpResponse(content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{glossary.name}.csv"'

    return response


@login_required
@plan_required('glossary')
def entry_delete(request, glossary_pk, entry_pk):
    entry = get_object_or_404(GlossaryEntry, pk=entry_pk, glossary__pk=glossary_pk, glossary__user=request.user)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Entry deleted.')
    return redirect('glossary_detail', pk=glossary_pk)


@login_required
@plan_required('glossary')
def glossary_suggest(request):
    if request.method == 'POST':
        text = request.POST.get('text', '')
        glossary_id = request.POST.get('glossary_id')
        if not text or not glossary_id:
            return JsonResponse({'error': 'text and glossary_id required'}, status=400)
        glossary = get_object_or_404(Glossary, pk=glossary_id, user=request.user)
        suggestions = GlossaryService.suggest_terms(text, glossary)
        total_matches = len(suggestions)
        word_count = len(text.split())
        coverage = 0
        if word_count > 0:
            matched_words = sum(s['frequency'] for s in suggestions)
            coverage = round((matched_words / word_count) * 100, 1)
        return JsonResponse({
            'suggestions': suggestions,
            'total_matches': total_matches,
            'coverage_percentage': coverage,
        })
    return JsonResponse({'error': 'POST required'}, status=400)
