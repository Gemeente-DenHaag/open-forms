from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from ..models import Submission, SubmissionStep
from openforms.core.models import FormStep


class SubmissionSerializer(serializers.HyperlinkedModelSerializer):
    steps = NestedHyperlinkedRelatedField(
        source="submissionstep_set",
        many=True,
        read_only=True,
        view_name='api:submission-steps-detail',
        lookup_field="uuid",
        parent_lookup_kwargs={'submission_uuid': 'submission__uuid'}
    )

    class Meta:
        model = Submission
        fields = ('uuid', 'url', 'form', 'steps', 'created_on')
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:submission-detail",
                "lookup_field": "uuid",
            },
            "form": {
                "view_name": "api:form-detail",
                "lookup_field": "slug",
            },
        }


class SubmissionStepSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        "submission_uuid": "submission__uuid",
    }
    
    form_step = NestedHyperlinkedRelatedField(
        # many=True,
        # read_only=True,   # Or add a queryset
        queryset=FormStep.objects,
        view_name='api:form-steps-detail',
        lookup_field="order",
        parent_lookup_kwargs={'form_slug': 'form__slug'}
    )

    class Meta:
        model = SubmissionStep
        fields = ('uuid', 'url', 'submission', 'form_step', 'data', 'created_on')
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:submission-steps-detail",
                "lookup_field": "uuid",
                "parent_lookup_kwargs": {
                    'submission_uuid': 'submission__uuid'
                }
            },
            "submission": {
                "view_name": "api:submission-detail",
                "lookup_field": "uuid",
                "read_only": True,
            },
        }

    def save(self, *args, **kwargs):
        # TODO: I forgot how to nicely do this.
        kwargs.update({
            "submission": Submission.objects.get(
                uuid=self.context['request'].parser_context['view'].kwargs['submission_uuid']
            )
        })
        return super().save(*args, **kwargs)