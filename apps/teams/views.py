from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Team, TeamMember
from .forms import TeamCreateForm, TeamEditForm, AddMemberForm
from .decorators import team_required, owner_required
from apps.core.decorators import plan_required


@login_required
@plan_required('teams')
def team_list(request):
    teams = Team.objects.filter(members__user=request.user).distinct()
    return render(request, 'teams/list.html', {'teams': teams})


@login_required
@plan_required('teams')
def team_create(request):
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.owner = request.user
            team.save()
            TeamMember.objects.create(user=request.user, team=team, role='owner')
            messages.success(request, f'Team "{team.name}" created successfully')
            return redirect('team_detail', team_id=team.pk)
    else:
        form = TeamCreateForm()
    return render(request, 'teams/create.html', {'form': form})


@login_required
@plan_required('teams')
@team_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    members = team.members.select_related('user').all()
    user_membership = TeamMember.objects.get(user=request.user, team=team)
    return render(request, 'teams/detail.html', {
        'team': team,
        'members': members,
        'user_membership': user_membership,
    })


@login_required
@plan_required('teams')
@owner_required
def team_settings(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    if request.method == 'POST':
        form = TeamEditForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team settings updated')
            return redirect('team_detail', team_id=team.pk)
    else:
        form = TeamEditForm(instance=team)
    return render(request, 'teams/settings.html', {'team': team, 'form': form})


@login_required
@plan_required('teams')
@team_required
def team_add_member(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    user_membership = TeamMember.objects.get(user=request.user, team=team)

    if user_membership.role not in ('owner', 'admin'):
        messages.error(request, 'Only owners and admins can add members')
        return redirect('team_detail', team_id=team.pk)

    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            role = form.cleaned_data['role']
            user = User.objects.get(username=username)

            if TeamMember.objects.filter(user=user, team=team).exists():
                messages.error(request, f'{username} is already a member')
                return redirect('team_detail', team_id=team.pk)

            TeamMember.objects.create(user=user, team=team, role=role)
            messages.success(request, f'{username} added to the team')
            return redirect('team_detail', team_id=team.pk)
    else:
        form = AddMemberForm()

    return render(request, 'teams/add_member.html', {'team': team, 'form': form})


@login_required
@plan_required('teams')
@team_required
def team_remove_member(request, team_id, member_id):
    team = get_object_or_404(Team, pk=team_id)
    member = get_object_or_404(TeamMember, pk=member_id, team=team)
    user_membership = TeamMember.objects.get(user=request.user, team=team)

    if user_membership.role not in ('owner', 'admin'):
        messages.error(request, 'Only owners and admins can remove members')
        return redirect('team_detail', team_id=team.pk)

    if member.role == 'owner':
        messages.error(request, 'Cannot remove the team owner')
        return redirect('team_detail', team_id=team.pk)

    if request.method == 'POST':
        member.delete()
        messages.success(request, f'{member.user.username} removed from the team')
        return redirect('team_detail', team_id=team.pk)

    return render(request, 'teams/remove_member.html', {'team': team, 'member': member})


@login_required
@plan_required('teams')
@team_required
def team_leave(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    membership = TeamMember.objects.get(user=request.user, team=team)

    if membership.role == 'owner':
        messages.error(request, 'Owners cannot leave. Transfer ownership first.')
        return redirect('team_detail', team_id=team.pk)

    if request.method == 'POST':
        membership.delete()
        messages.success(request, f'You left {team.name}')
        return redirect('team_list')

    return render(request, 'teams/leave.html', {'team': team})


@login_required
@plan_required('teams')
@team_required
def team_usage(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    member_ids = team.members.values_list('user_id', flat=True)

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    from apps.documents.models import DocumentJob

    usage_by_member = DocumentJob.objects.filter(
        user_id__in=member_ids,
        created_at__gte=thirty_days_ago
    ).values('user__username').annotate(
        total_jobs=Count('id'),
        completed_jobs=Count('id', filter=Q(status='completed')),
        total_pages=Sum('page_count'),
        total_characters=Sum('character_count'),
    ).order_by('-total_jobs')

    total_usage = DocumentJob.objects.filter(
        user_id__in=member_ids,
        created_at__gte=thirty_days_ago
    ).aggregate(
        total_jobs=Count('id'),
        completed_jobs=Count('id', filter=Q(status='completed')),
        total_pages=Sum('page_count'),
        total_characters=Sum('character_count'),
    )

    daily_usage = DocumentJob.objects.filter(
        user_id__in=member_ids,
        created_at__gte=thirty_days_ago,
        status='completed'
    ).extra(
        select={'day': "date(created_at)"}
    ).values('day').annotate(
        jobs=Count('id'),
        pages=Sum('page_count'),
    ).order_by('day')

    return render(request, 'teams/usage.html', {
        'team': team,
        'usage_by_member': usage_by_member,
        'total_usage': total_usage,
        'daily_usage': daily_usage,
    })
