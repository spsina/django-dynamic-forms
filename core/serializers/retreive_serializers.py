from rest_framework import serializers

from core.element_types import INPUT, DATETIME, SELECT
from core.models import Input, SelectElement, DateTimeElement, SubForm, Field
from core.serializers.common_serializers import DataSerializer
from core.serializers.serializers_headers import base_fields, base_field_fields
from core.sub_form_fields import get_related_elements


class InputRetrieveUpdateSerializer(serializers.ModelSerializer):
    """simple input RUD serializer"""

    class Meta:
        model = Input
        fields = base_fields


class SelectElementRetrieveUpdateSerializer(serializers.ModelSerializer):
    """Select element RUD serializer"""
    data = DataSerializer(many=True)

    class Meta:
        model = SelectElement
        fields = base_fields + ['data', ]


class DateTimeRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateTimeElement
        fields = base_fields


# map of element types to their retrieve serializer
retrieve_serializers = {
    INPUT: InputRetrieveUpdateSerializer,
    DATETIME: DateTimeRetrieveSerializer,
    SELECT: SelectElementRetrieveUpdateSerializer
}


class FieldRetrieveSerializer(serializers.ModelSerializer):
    """Retrieve a field with it's elements"""
    elements = serializers.SerializerMethodField()

    class Meta:
        model = Field
        fields = base_field_fields

    @staticmethod
    def get_elements(instance):
        _fields = get_related_elements(instance)
        _fields_data = []

        for field in _fields:
            _Serializer = retrieve_serializers.get(type(field).type)
            _field_data = _Serializer(instance=field).data
            _fields_data.append(_field_data)

        return _fields_data


class SubFormRetrieveSerializer(serializers.ModelSerializer):
    """Retrieve Sub Form data with is's inputs and input elements"""
    fields = FieldRetrieveSerializer(many=True, read_only=True)

    class Meta:
        model = SubForm
        fields = ['pk', 'title', 'description', 'fields']

