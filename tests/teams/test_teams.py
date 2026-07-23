import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.teams.models import Team, TeamMember
from apps.teams.decorators import team_required, owner_required, admin_or_owner_required


@pytest.fixture
def user2(db):
    u = User.objects.create_user(username="testuser2", email="test2@test.com", password="testpass123")
    from apps.accounts.models import UserProfile
    UserProfile.objects.create(user=u, plan="free")
    return u


@pytest.fixture
def team(user):
    return Team.objects.create(name="Test Team", owner=user)


@pytest.fixture
def team_member(user, team):
    return TeamMember.objects.create(user=user, team=team, role='owner')


@pytest.mark.django_db
class TestTeamModel:
    def test_team_creation(self, user):
        team = Team.objects.create(name="My Team", owner=user)
        assert team.pk is not None
        assert team.name == "My Team"
        assert team.owner == user

    def test_team_str(self, user):
        team = Team.objects.create(name="My Team", owner=user)
        assert str(team) == "My Team"

    def test_team_member_count(self, user, team):
        TeamMember.objects.create(user=user, team=team, role='owner')
        assert team.member_count == 1

    def test_team_ordering(self, user):
        team1 = Team.objects.create(name="First", owner=user)
        team2 = Team.objects.create(name="Second", owner=user)
        teams = list(Team.objects.all())
        assert teams[0] == team2
        assert teams[1] == team1


@pytest.mark.django_db
class TestTeamMemberModel:
    def test_member_creation(self, user, team):
        member = TeamMember.objects.create(user=user, team=team, role='member')
        assert member.pk is not None
        assert member.role == 'member'

    def test_member_str(self, user, team):
        member = TeamMember.objects.create(user=user, team=team, role='admin')
        assert "testuser" in str(member)
        assert "Test Team" in str(member)
        assert "admin" in str(member)

    def test_unique_together(self, user, team):
        TeamMember.objects.create(user=user, team=team, role='member')
        with pytest.raises(Exception):
            TeamMember.objects.create(user=user, team=team, role='admin')


@pytest.mark.django_db
class TestTeamViews:
    def test_team_list(self, authenticated_client, team_member):
        resp = authenticated_client.get('/teams/')
        assert resp.status_code == 200

    def test_team_create_get(self, authenticated_client):
        resp = authenticated_client.get('/teams/create/')
        assert resp.status_code == 200

    def test_team_create_post(self, authenticated_client, user):
        resp = authenticated_client.post('/teams/create/', {'name': 'New Team'})
        assert resp.status_code == 302
        assert Team.objects.filter(name='New Team').exists()

    def test_team_detail(self, authenticated_client, team_member):
        resp = authenticated_client.get(f'/teams/{team_member.team.pk}/')
        assert resp.status_code == 200

    def test_team_detail_other_user(self, authenticated_client, team, user2):
        resp = authenticated_client.get(f'/teams/{team.pk}/')
        assert resp.status_code == 403

    def test_team_settings_get(self, authenticated_client, team_member):
        resp = authenticated_client.get(f'/teams/{team_member.team.pk}/settings/')
        assert resp.status_code == 200

    def test_team_add_member_get(self, authenticated_client, team_member):
        resp = authenticated_client.get(f'/teams/{team_member.team.pk}/members/add/')
        assert resp.status_code == 200

    def test_team_add_member_post(self, authenticated_client, team, user2):
        resp = authenticated_client.post(
            f'/teams/{team.pk}/members/add/',
            {'username': 'testuser2', 'role': 'member'}
        )
        assert resp.status_code == 302
        assert TeamMember.objects.filter(user=user2, team=team).exists()

    def test_team_remove_member(self, authenticated_client, team, user2):
        member = TeamMember.objects.create(user=user2, team=team, role='member')
        resp = authenticated_client.post(f'/teams/{team.pk}/members/{member.pk}/remove/')
        assert resp.status_code == 302
        assert not TeamMember.objects.filter(pk=member.pk).exists()

    def test_team_leave(self, authenticated_client, team, user):
        member = TeamMember.objects.create(user=user, team=team, role='member')
        resp = authenticated_client.post(f'/teams/{team.pk}/leave/')
        assert resp.status_code == 302
        assert not TeamMember.objects.filter(pk=member.pk).exists()

    def test_team_owner_cannot_leave(self, authenticated_client, team_member):
        resp = authenticated_client.post(f'/teams/{team_member.team.pk}/leave/')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestTeamDecorators:
    def test_team_required_decorator(self, client, user, team):
        @team_required
        def my_view(request, team_id):
            from django.http import HttpResponse
            return HttpResponse("OK")

        client.login(username="testuser", password="testpass123")
        resp = client.get(f'/fake/{team.pk}/')
        assert resp.status_code == 403

    def test_owner_required_decorator(self, client, user, team):
        @owner_required
        def my_view(request, team_id):
            from django.http import HttpResponse
            return HttpResponse("OK")

        client.login(username="testuser", password="testpass123")
        member = TeamMember.objects.create(user=user, team=team, role='member')
        resp = client.get(f'/fake/{team.pk}/')
        assert resp.status_code == 403
