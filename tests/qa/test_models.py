import pytest
from apps.qa.models import QARule, QAScore
from apps.documents.models import DocumentJob


@pytest.mark.django_db
class TestQARuleModel:
    def test_qarule_creation(self):
        rule = QARule.objects.create(
            name="Length Check",
            description="Checks length consistency",
            rule_type="length_consistency",
            severity="major",
            weight=1.5,
            enabled=True,
            auto_approve_threshold=0.85,
        )
        assert rule.pk is not None
        assert rule.name == "Length Check"
        assert rule.severity == "major"
        assert rule.weight == 1.5
        assert rule.auto_approve_threshold == 0.85

    def test_qarule_str(self):
        rule = QARule.objects.create(name="Term Check", severity="critical")
        s = str(rule)
        assert "Term Check" in s
        assert "critical" in s

    def test_qarule_defaults(self):
        rule = QARule.objects.create(name="Default Rule", rule_type="test")
        assert rule.severity == "major"
        assert rule.weight == 1.0
        assert rule.enabled is True
        assert rule.auto_approve_threshold == 0.8

    def test_qarule_ordering(self):
        r1 = QARule.objects.create(name="Light", weight=0.5)
        r2 = QARule.objects.create(name="Heavy", weight=2.0)
        rules = list(QARule.objects.all())
        assert rules[0].pk == r2.pk
        assert rules[1].pk == r1.pk


@pytest.mark.django_db
class TestQAScoreModel:
    def test_qascore_creation(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status='completed')
        rule = QARule.objects.create(name="Length", rule_type="length_consistency")
        score = QAScore.objects.create(
            job=job,
            rule=rule,
            score=0.85,
            details={"ratio": 1.2},
        )
        assert score.pk is not None
        assert score.score == 0.85

    def test_qascore_str(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status='completed')
        rule = QARule.objects.create(name="Length", rule_type="length_consistency")
        score = QAScore.objects.create(job=job, rule=rule, score=0.92)
        s = str(score)
        assert str(job.pk) in s
        assert "Length" in s
        assert "0.92" in s

    def test_qascore_unique_together(self, sample_txt_file):
        job = DocumentJob.objects.create(source_file=sample_txt_file, status='completed')
        rule = QARule.objects.create(name="Length", rule_type="length_consistency")
        QAScore.objects.create(job=job, rule=rule, score=0.9)
        with pytest.raises(Exception):
            QAScore.objects.create(job=job, rule=rule, score=0.8)
