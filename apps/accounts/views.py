from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm, APIKeyForm
from .models import UserProfile, APIKey


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None and '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'auth/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Doc Translator.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def api_keys_view(request):
    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            APIKey.objects.create(
                user=request.user,
                name=form.cleaned_data['name'],
            )
            messages.success(request, 'API key created successfully.')
            return redirect('api-keys')
    else:
        form = APIKeyForm()

    keys = APIKey.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/api_keys.html', {'form': form, 'keys': keys})


@login_required
def delete_api_key_view(request, key_id):
    key = APIKey.objects.get(pk=key_id, user=request.user)
    key.delete()
    messages.success(request, 'API key deleted.')
    return redirect('api-keys')
