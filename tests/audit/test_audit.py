import pytest
from apps.audit.models import AuditLog


@pytest.mark.django_db
class TestAuditLogModel:
    def test_audit_log_creation(self, user):
        log = AuditLog.objects.create(
            user=user,
            action='create',
            resource_type='document',
            resource_id='42',
            details={'filename': 'test.pdf'},
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0',
        )
        assert log.pk is not None
        assert log.user == user
        assert log.action == 'create'
        assert log.resource_type == 'document'
        assert log.resource_id == '42'
        assert log.details == {'filename': 'test.pdf'}
        assert log.ip_address == '127.0.0.1'
        assert log.user_agent == 'Mozilla/5.0'

    def test_audit_log_str(self, user):
        log = AuditLog.objects.create(
            user=user,
            action='login',
            resource_type='session',
            resource_id='1',
        )
        s = str(log)
        assert 'testuser' in s
        assert 'login' in s

    def test_audit_log_str_with_empty_resource(self, user):
        log = AuditLog.objects.create(
            user=user,
            action='logout',
        )
        s = str(log)
        assert 'testuser' in s
        assert 'logout' in s

    def test_audit_log_default_details(self, user):
        log = AuditLog.objects.create(
            user=user,
            action='create',
        )
        assert log.details == {}

    def test_audit_log_null_user(self):
        log = AuditLog.objects.create(
            user=None,
            action='delete',
            resource_type='glossary',
            resource_id='5',
        )
        assert log.user is None
        assert log.action == 'delete'

    def test_audit_log_ordering(self, user):
        log1 = AuditLog.objects.create(user=user, action='create')
        log2 = AuditLog.objects.create(user=user, action='update')
        logs = list(AuditLog.objects.all())
        assert logs[0].pk == log2.pk
        assert logs[1].pk == log1.pk

    def test_audit_log_log_classmethod(self, user):
        log = AuditLog.log(
            user=user,
            action='export',
            resource_type='glossary',
            resource_id='10',
            details={'format': 'csv'},
        )
        assert log.pk is not None
        assert log.action == 'export'
        assert log.details == {'format': 'csv'}

    def test_audit_log_log_with_request(self, user):
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/dashboard/', REMOTE_ADDR='192.168.1.1')
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'
        log = AuditLog.log(
            user=user,
            action='login',
            request=request,
        )
        assert log.ip_address == '192.168.1.1'
        assert 'TestAgent/1.0' in log.user_agent

    def test_audit_log_log_without_request(self, user):
        log = AuditLog.log(
            user=user,
            action='translate',
            resource_type='document',
            resource_id='99',
        )
        assert log.ip_address is None
        assert log.user_agent == ''

    def test_audit_log_action_choices(self, user):
        valid_actions = [
            'create', 'update', 'delete', 'login', 'logout',
            'translate', 'export', 'import', 'share',
        ]
        for action in valid_actions:
            log = AuditLog.objects.create(user=user, action=action)
            assert log.action == action
            log.delete()


@pytest.mark.django_db
class TestAuditLogViews:
    def test_audit_list(self, authenticated_client, user):
        AuditLog.objects.create(user=user, action='create', resource_type='document')
        resp = authenticated_client.get('/audit/')
        assert resp.status_code == 200

    def test_audit_list_requires_login(self, client):
        resp = client.get('/audit/')
        assert resp.status_code == 302

    def test_audit_list_filters_by_action(self, authenticated_client, user):
        AuditLog.objects.create(user=user, action='create')
        AuditLog.objects.create(user=user, action='login')
        resp = authenticated_client.get('/audit/?action=create')
        assert resp.status_code == 200

    def test_audit_list_filters_by_resource_type(self, authenticated_client, user):
        AuditLog.objects.create(user=user, action='create', resource_type='document')
        AuditLog.objects.create(user=user, action='create', resource_type='glossary')
        resp = authenticated_client.get('/audit/?resource_type=document')
        assert resp.status_code == 200

    def test_audit_list_empty(self, authenticated_client):
        resp = authenticated_client.get('/audit/')
        assert resp.status_code == 200

    def test_audit_detail(self, authenticated_client, user):
        log = AuditLog.objects.create(
            user=user, action='create', resource_type='document',
            resource_id='42', details={'key': 'value'},
            ip_address='10.0.0.1', user_agent='TestBrowser',
        )
        resp = authenticated_client.get(f'/audit/{log.pk}/')
        assert resp.status_code == 200

    def test_audit_detail_not_found(self, authenticated_client):
        resp = authenticated_client.get('/audit/99999/')
        assert resp.status_code == 404

    def test_audit_detail_other_users_log(self, authenticated_client, pro_user):
        log = AuditLog.objects.create(
            user=pro_user, action='create', resource_type='document',
        )
        resp = authenticated_client.get(f'/audit/{log.pk}/')
        assert resp.status_code == 404

    def test_audit_export(self, authenticated_client, user):
        AuditLog.objects.create(user=user, action='create')
        AuditLog.objects.create(user=user, action='login')
        resp = authenticated_client.get('/audit/export/')
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/json'

    def test_audit_export_requires_login(self, client):
        resp = client.get('/audit/export/')
        assert resp.status_code == 302

    def test_audit_export_empty(self, authenticated_client):
        resp = authenticated_client.get('/audit/export/')
        assert resp.status_code == 200
        data = resp.json()
        assert 'logs' in data
        assert len(data['logs']) == 0

    def test_audit_export_user_isolation(self, authenticated_client, pro_user):
        AuditLog.objects.create(user=pro_user, action='create')
        resp = authenticated_client.get('/audit/export/')
        data = resp.json()
        assert len(data['logs']) == 0
