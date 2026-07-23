from django import template

from apps.accounts.models import UserProfile

register = template.Library()


@register.simple_tag(takes_context=True)
def has_plan_feature(context, feature):
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.has_feature(feature)


@register.simple_tag(takes_context=True)
def user_plan(context):
    user = context.get('user')
    if not user or not user.is_authenticated:
        return ''
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.plan
