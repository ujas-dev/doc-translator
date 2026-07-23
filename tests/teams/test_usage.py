import pytest
from django.contrib.auth.models import User
from apps.teams.models import Team, TeamMember


@pytest.fixture
def team(user):
    return Team.objects.create(name="Test Team", owner=user)


@pytest.fixture
def team_with_members(user, user2, team):
    TeamMember.objects.create(user=user, team=team, role='owner')
    TeamMember.objects.create(user=user2, team=team, role='member')
    return team


@pytest.fixture
def user2(db):
    from apps.accounts.models import UserProfile
    u = User.objects.create_user(username="testuser2", email="test2@test.com", password="testpass123")
    UserProfile.objects.create(user=u, plan="free")
    return u


@pytest.mark.django_db
class TestTeamUsageView:
    def test_team_usage_loads(self, authenticated_client, team_with_members):
        resp = authenticated_client.get(f'/teams/{team_with_members.pk}/usage/')
        assert resp.status_code == 200

    def test_team_usage_requires_login(self, client, team_with_members):
        resp = client.get(f'/teams/{team_with_members.pk}/usage/')
        assert resp.status_code == 302

    def test_team_usage_not_member(self, authenticated_client, team):
        resp = authenticated_client.get(f'/teams/{team.pk}/usage/')
        assert resp.status_code == 403
