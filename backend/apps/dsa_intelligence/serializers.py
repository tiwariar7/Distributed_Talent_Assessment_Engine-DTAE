from rest_framework import serializers
from .models import Company, Topic, DSAQuestion, QuestionCompanyFrequency, FrequencyBucket


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "slug", "logo", "metadata")


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ("id", "name", "slug", "parent")


class QuestionCompanyFrequencySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_slug = serializers.CharField(source="company.slug", read_only=True)

    class Meta:
        model = QuestionCompanyFrequency
        fields = (
            "company_name",
            "company_slug",
            "frequency_bucket",
            "frequency_percentage",
            "source_repo",
            "metadata",
        )


class DSAQuestionSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    company_frequencies = QuestionCompanyFrequencySerializer(many=True, read_only=True)

    class Meta:
        model = DSAQuestion
        fields = (
            "id",
            "title",
            "slug",
            "leetcode_url",
            "difficulty",
            "prompt",
            "acceptance_rate",
            "topics",
            "company_frequencies",
        )


class SmartAssessmentGeneratorSerializer(serializers.Serializer):
    company_slug = serializers.SlugField(required=True)
    frequency_bucket = serializers.ChoiceField(
        choices=FrequencyBucket.choices,
        default=FrequencyBucket.ALL
    )
    easy_count = serializers.IntegerField(min_value=0, max_value=10, default=1)
    medium_count = serializers.IntegerField(min_value=0, max_value=10, default=1)
    hard_count = serializers.IntegerField(min_value=0, max_value=10, default=1)
    topic_slug = serializers.SlugField(required=False, allow_null=True, allow_blank=True)
    title = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)

