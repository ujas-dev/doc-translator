import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse

from apps.teams.models import Team, TeamMember
from apps.teams.decorators import team_required, owner_required, admin_or_owner_required


@pytest.fixture
def user2(db):
    from apps.accounts.models import UserProfile
    u = User.objects.create_user(username="testuser2", email="test2@test.com", password="testpass123")
    UserProfile.objects.create(user=u, plan="free")
    return u


@pytest.fixture
def team(user):
    return Team.objects.create(name="Test Team", owner=user)


@pytest.mark.django_db
class TestAdminOrOwnerRequired:
    def test_owner_passes(self, client, user, team):
        TeamMember.objects.create(user=user, team=team, role='owner')
        client.login(username="testuser", password="testpass123")

        @admin_or_owner_required
        def my_view(request, team_id):
            return HttpResponse("OK")

        resp = client.get(f'/fake/{team.pk}/')
        assert resp.status_code == 200

    def test_admin_passes(self, client, user, team):
        TeamMember.objects.create(user=user, team=team, role='admin')
        client.login(username="testuser", password="testpass123")

        @admin_or_owner_required
        def my_view(request, team_id):
            return HttpResponse("OK")

        resp = client.get(f'/fake/{team.pk}/')
        assert resp.status_code == 200

    def test_member_fails(self, client, user, team):
        TeamMember.objects.create(user=user, team=team, role='member')
        client.login(username="testuser", password="testpass123")

        @admin_or_owner_required
        def my_view(request, team_id):
            return HttpResponse("OK")

        resp = client.get(f'/fake/{team.pk}/')
        assert resp.status_code == 403

    def test_non_member_fails(self, client, user, team):
        client.login(username="testuser", password="testpass123")

        @admin_or_owner_required
        def my_view(request, team_id):
            return HttpResponse("OK")

        resp = client.get(f'/fake/{team.pk}/')
        assert resp.status_code == 403


@pytest.mark.django_db
class TestTeamPermissionEdgeCases:
    def test_owner_cannot_be_removed(self, authenticated_client, user, team):
        owner = TeamMember.objects.create(user=user, team=team, role='owner')
        resp = authenticated_client.post(f'/teams/{team.pk}/members/{owner.pk}/remove/')
        assert resp.status_code == 302
        assert TeamMember.objects.filter(pk=owner.pk).exists()

    def test_duplicate_member_prevented(self, authenticated_client, user, team, user2):
        TeamMember.objects.create(user=user2, team=team, role='member')
        resp = authenticated_client.post(
            f'/teams/{team.pk}/members/add/',
            {'username': 'testuser2', 'role': 'member'}
        )
        assert resp.status_code == 302
        assert TeamMember.objects.filter(user=user2, team=team).count() == 1

    def test_non_admin_cannot_add_member(self, client, user, user2, team):
        TeamMember.objects.create(user=user, team=team, role='member')
        client.login(username="testuser", password="testpass123")
        resp = client.post(
            f'/teams/{team.pk}/members/add/',
            {'username': 'testuser2', 'role': 'member'}
        )
        assert resp.status_code == 302
        assert not TeamMember.objects.filter(user=user2, team=team).exists()

    def test_non_admin_cannot_remove_member(self, client, user, user2, team):
        TeamMember.objects.create(user=user, team=team, role='member')
        member2 = TeamMember.objects.create(user=user2, team=team, role='member')
        client.login(username="testuser", password="testpass123")
        resp = client.post(f'/teams/{team.pk}/members/{member2.pk}/remove/')
        assert resp.status_code == 302
        assert TeamMember.objects.filter(pk=member2.pk).exists()

    def test_team_settings_update(self, authenticated_client, team):
        resp = authenticated_client.post(
            f'/teams/{team.pk}/settings/',
            {'name': 'Updated Team Name'}
        )
        assert resp.status_code == 302
        team.refresh_from_db()
        assert team.name == 'Updated Team Name'
