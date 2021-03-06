import operator
from functools import reduce

from django.db.models import Q
from rest_framework.generics import RetrieveAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404, \
    ListAPIView, RetrieveUpdateAPIView, UpdateAPIView, GenericAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.element_types import element_types
from core.permissions import IsLoggedIn, IsSuperuser
from core.serializers.FormSerializers.common_serializers import CharFieldSerializer, ElementsSetOrder, FieldsSetOrder
from core.serializers.FormSerializers.create_serializers import SubFormRawCreateSerializer, FieldRawCreateSerializer, \
    TemplateRawCreateSerializer, FormCreateSerializer, get_create_serializer, get_update_serializer, \
    get_set_value_serializer, get_raw_converter_serializer, get_condition_update_serializer
from core.serializers.FormSerializers.retreive_serializers import SubFormRetrieveSerializer, TemplateRetrieveSerializer, \
    FormRetrieveSerializer, get_retrieve_serializer, FormSimpleRetrieveSerializer, FormFilterSerializer, \
    TemplateSimpleRetrieveSerializer
from core.models import SubForm, Template, elements, Form, Field, DateElement
from django_filters.rest_framework import DjangoFilterBackend

from core.sub_form_fields import get_related_attrs

from django.utils import timezone


class RetrieveSubFormView(RetrieveUpdateDestroyAPIView):
    """Retrieve basic sub form info with fields data"""
    serializer_class = SubFormRetrieveSerializer
    queryset = SubForm.objects.all()

    lookup_field = 'pk'
    lookup_url_kwarg = 'sub_form_id'


class TemplateRetrieveView(RetrieveUpdateDestroyAPIView):
    """RUD template"""
    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = TemplateRetrieveSerializer
    queryset = Template.objects.all()

    lookup_field = 'pk'
    lookup_url_kwarg = 'template_id'


class TemplateElementListView(APIView):
    """RUD template"""
    permission_classes = [IsLoggedIn, ]

    def get(self, request, *args, **kwargs):
        elements_data = []
        template = get_object_or_404(Template, pk=self.kwargs.get('template_id'))

        for sub_form in template.sub_forms.all():
            for field in sub_form.fields.all():
                for element in get_related_attrs(field):
                    _Serializer = get_retrieve_serializer(element.type)
                    el_data = _Serializer(instance=element).data
                    elements_data.append(el_data)

        return Response(elements_data)


class FormRetrieveView(RetrieveUpdateDestroyAPIView):
    """RUD Form"""
    permission_classes = [IsLoggedIn, ]
    serializer_class = FormRetrieveSerializer
    queryset = Form.objects.all()

    lookup_field = 'pk'
    lookup_url_kwarg = 'form_id'


class CreateFormFromTemplate(CreateAPIView):
    """Create a new form from the given template form,
    and set the filler to the currently logged in user"""
    permission_classes = [IsLoggedIn, ]

    serializer_class = FormCreateSerializer

    def perform_create(self, serializer):
        serializer.save(filler=self.request.user.user_profile)


class AnswerElementOfForm(UpdateAPIView):
    """Create a new form from the given template form,
    and set the filler to the currently logged in user"""

    permission_classes = [IsLoggedIn, ]  # todo: add filler

    def get_serializer_class(self):
        """Get serializer based on filed type"""
        return get_set_value_serializer(self.kwargs.get('element_type'))

    def perform_update(self, serializer):
        serializer.save()
        form = get_object_or_404(Form, pk=self.kwargs.get('form_id'))
        form.fork_date = timezone.now()
        form.save()

    def get_object(self):
        kwargs = self.kwargs

        form = get_object_or_404(Form, pk=kwargs.get('form_id'))
        element_id = kwargs.get('element_id')
        element_type = kwargs.get('element_type')

        template = form.template

        # if the given element id refers to the template's element,
        # create an answer for it

        element = elements.get(element_type).objects.get(pk=element_id)

        if not element.answer_of:
            # it is the base base template field

            # element must belong to the same template as forms template
            if element.field.sub_form.template != template:
                return Response({'detail': ['invalid element id']}, status=400)

            # check if there is an answer for this element
            answer_element = elements.get(element_type).objects.filter(form=form, answer_of=element)
            if not answer_element.exists():
                return elements.get(element_type).objects.create(
                    answer_of=element,
                    form=form
                )
            else:
                return answer_element.first()
        else:
            # element itself is the answer
            return element


class CreateTemplateView(CreateAPIView):
    """Create Raw Form As Template"""

    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = TemplateRawCreateSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user.user_profile)


class ListTemplatesView(ListAPIView):
    """List All Template Forms"""
    permission_classes = [IsLoggedIn, ]
    serializer_class = TemplateSimpleRetrieveSerializer

    def get_queryset(self):
        return Template.objects.filter(access_level__lte=self.request.user.user_profile.access_level).order_by('-id')


class FormsOfTemplate(ListAPIView):
    """List All Forms from the given template"""
    permission_classes = [IsLoggedIn, ]
    serializer_class = FormSimpleRetrieveSerializer
    filter_backends = [DjangoFilterBackend, ]

    filterset_fields = ['filler', ]

    def get_queryset(self):
        return Form.objects.filter(template__pk=self.kwargs.get('template_id')).order_by('-fork_date')


class FormsOfUserProfile(ListAPIView):
    """List All Forms from the given template"""
    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = FormSimpleRetrieveSerializer
    filter_backends = [DjangoFilterBackend, ]

    filterset_fields = ['filler', ]

    def get_queryset(self):
        return Form.objects.filter(filler__pk=self.kwargs.get('user_profile_id'))


class FormsIFilled(ListAPIView):
    """List All Forms that the currently logged in user filled"""
    permission_classes = [IsLoggedIn, ]
    serializer_class = FormSimpleRetrieveSerializer
    filter_backends = [DjangoFilterBackend, ]

    filterset_fields = ['template', 'description']

    def get_queryset(self):
        return Form.objects.filter(filler=self.request.user.user_profile)


class FormsListView(ListAPIView):
    """List All Forms that the currently logged in user filled"""
    permission_classes = [IsLoggedIn, ]
    serializer_class = FormSimpleRetrieveSerializer
    filter_backends = [DjangoFilterBackend, ]

    filterset_fields = ['description', 'template', 'filler']

    def get_queryset(self):
        return Form.objects.filter(template__access_level__lte=self.request.user.user_profile.access_level).order_by(
            '-fork_date')


class CreateRawSubForm(CreateAPIView):
    """Create a new sub form with fields"""
    permission_classes = [IsLoggedIn, ]
    serializer_class = SubFormRawCreateSerializer


class AddFieldToSubForm(CreateAPIView):
    """ Add a field to sub form """
    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = FieldRawCreateSerializer


class UpdateField(RetrieveUpdateDestroyAPIView):
    """ Add a field to sub form """
    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = FieldRawCreateSerializer
    queryset = Field.objects.all()

    lookup_url_kwarg = 'field_id'
    lookup_field = 'pk'


class AddElementToField(CreateAPIView):
    """ Add a field to sub form """
    permission_classes = [IsLoggedIn, IsSuperuser]

    def get_serializer_class(self):
        """Get serializer based on filed type"""
        return get_create_serializer(self.kwargs.get('element_type'))


class UpdateElement(RetrieveUpdateDestroyAPIView):
    """ Add a field to sub form """
    permission_classes = [IsLoggedIn, IsSuperuser]

    def get_serializer_class(self):
        """Get serializer based on filed type"""
        return get_update_serializer(self.kwargs.get('element_type'))

    def get_object(self):
        return get_object_or_404(elements.get(self.kwargs.get('element_type')),
                                 pk=self.kwargs.get('element_id'))


class ConditionUpdateElement(RetrieveUpdateDestroyAPIView):
    """ Update element condition fields """
    permission_classes = [IsLoggedIn, IsSuperuser]

    def get_serializer_class(self):
        """Get serializer based on filed type"""
        return get_condition_update_serializer(self.kwargs.get('element_type'))

    def get_object(self):
        return get_object_or_404(elements.get(self.kwargs.get('element_type')),
                                 pk=self.kwargs.get('element_id'))


class AddDataView(CreateAPIView):
    """ Add a data to element"""
    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = CharFieldSerializer

    def perform_create(self, serializer):
        data = serializer.save()

        # add to element
        element = get_object_or_404(elements.get(self.kwargs.get('element_type')),
                                    pk=self.kwargs.get('element_id'))
        element.data.add(data)


class DataRUDView(RetrieveUpdateAPIView):
    """RUD data"""
    permission_classes = [IsLoggedIn, IsSuperuser]
    serializer_class = CharFieldSerializer


class FormFilterView(APIView):
    """FormFilterView based on the given query"""

    serializer_class = FormFilterSerializer

    operator_table = {
        'and': lambda a, b: a & b,
        'or': lambda a, b: a | b
    }

    @staticmethod
    def set_filter_on_field(field, filter_name):

        if filter_name == '':
            return field

        return "%s__%s" % (field, filter_name)

    def parse_group(self, group):
        if not group:
            return Q()

        matchType = group['matchType']

        val = Q()

        for rule in group['rules']:

            if rule['qtype'] == 'group':
                val = self.operator_table[matchType](val, self.parse_group(rule))
            else:

                # get element model
                _Element = elements.get(rule['type'])

                # get value field through related name of the element
                _related_field_name_value = "%s__%s" % (_Element.related_name_to_form(),
                                                        _Element.value_field)

                # to insure that the retrieved element answer corresponds to the queried element
                _relate_filed_name_pk = "%s__answer_of__pk" % _Element.related_name_to_form()

                # serialize the query element, this process converts query json to native types
                # that can be used in object filtering
                _Serializer = get_raw_converter_serializer(rule['type'])
                serializer = _Serializer(data=rule)
                serializer.is_valid(raise_exception=True)
                _converted_value = serializer.validated_data.get(_Element.value_field)

                if _Element.value_field == "values":
                    # clear the _converted_value
                    _converted_value = [v['value'] for v in _converted_value]
                    match_Q = reduce(operator.and_,
                                     (Q(
                                         **{
                                             self.set_filter_on_field(_related_field_name_value,
                                                                      rule['filter']): x
                                         }
                                     ) for x in _converted_value))
                else:
                    match_Q = Q(**{
                        self.set_filter_on_field(_related_field_name_value,
                                                 rule['filter']): _converted_value,
                    })

                _pk_filter = {
                    _relate_filed_name_pk: rule['pk']
                }
                val = self.operator_table[matchType](val, match_Q & Q(**_pk_filter))
        return val

    def get_queryset(self):
        # serialize request data
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        # get request attrs
        query = serializer.validated_data.get('query')
        _elements = serializer.validated_data.get('elements')

        # get the base template
        template = get_object_or_404(Template, pk=self.kwargs.get('template_id'))

        # generate a Q expression from the given query rules
        _q = self.parse_group(query)

        # get all the forms that match the given rules
        _forms = template.forms.filter(_q).distinct()

        # data of the individual elements of the filtered forms
        _elements_data = []

        # element data of a specific form (temp)
        _one_form_element_data = {}

        for form in _forms:

            # get all form answers
            answers = get_related_attrs(form, base_name="answers")

            for answer in answers:

                # todo: only serialize the answer object if it's requested
                answer_data = get_retrieve_serializer(answer.type, simple=True)(instance=answer).data
                _one_form_element_data['%s_%d' % (answer.type,
                                                  answer.answer_of.pk)] = \
                    answer_data[answer.value_field]

            # include the form description
            _one_form_element_data['description'] = form.description

            _elements_data.append(_one_form_element_data)
            _one_form_element_data = {}
        return _elements_data

    def post(self, request, *args, **kwargs):
        return Response(self.get_queryset())


class SetElementOrders(UpdateAPIView):
    """
        Receives a json array of elements and sets their orders

        structure of the elements_data

        elements_data = {
        "type":
        "pk":
        "order":
        }

        """

    serializer_class = ElementsSetOrder

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        elements_data = serializer.validated_data.get('elements_data')

        # set all orders
        for element_data in elements_data:
            element_data.get('element').order = element_data.get('order')
            element_data.get('element').save()

        return Response({'detail': "set"})


class SetFieldOrders(UpdateAPIView):
    """
        Receives a json array of elements and sets their orders

        structure of the elements_data

        elements_data = {
        "pk":
        "order":
        }

        """

    serializer_class = FieldsSetOrder

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        fields_data = serializer.validated_data.get('fields_data')
        print(fields_data)
        # set all orders
        for field_data in fields_data:
            field_data.get('field').order = field_data.get('order')
            field_data.get('field').save()

        return Response({'detail': "set"})


class ElementTypesList(APIView):

    @staticmethod
    def get(request, *args, **kwargs):
        return Response(element_types)
