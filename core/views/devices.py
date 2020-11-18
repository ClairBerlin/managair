import logging
import re
from datetime import datetime
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework_json_api.filters import QueryParameterValidationFilter
from rest_framework_json_api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
)

from core.permissions import IsOrganizationOwner
from core.models import (
    Quantity,
    NodeProtocol,
    NodeModel,
    Node,
    NodeFidelity,
)
from core.serializers import (
    QuantitySerializer,
    NodeProtocolSerializer,
    NodeModelSerializer,
    NodeSerializer,
    NodeFidelitySerializer,
)

logger = logging.getLogger(__name__)


class IncludeTimeseriesQPValidator(QueryParameterValidationFilter):
    """Query parameter validator that admits an extra `include_timeseries` parameter."""

    query_regex = re.compile(
        r"^(sort|include|include_timeseries)$|^(?P<type>filter|fields|page)(\[[\w\.\-]+\])?$"
    )


class QuantityViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Quantity.objects.all()
    serializer_class = QuantitySerializer


class NodeProtocolViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = NodeProtocol.objects.all()
    serializer_class = NodeProtocolSerializer


class NodeModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = NodeModel.objects.all()
    serializer_class = NodeModelSerializer


class NodeViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated & IsOrganizationOwner]
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    filter_backends = (IncludeTimeseriesQPValidator, SearchFilter)
    search_fields = ("alias", "eui64")

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user"""
        queryset = super().get_queryset()
        queryset = queryset.filter(owner__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id is not None:
                logger.debug("Restrict to nodes of organization #%s.", organization_id)
                queryset = queryset.filter(owner=organization_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        nodes = []
        for node in queryset:
            node.sample_count = node.samples.count()
            nodes.append(node)
        page = self.paginate_queryset(nodes)
        # TODO: Simplify to use the parent list method and simply inject the modified
        # queryset.
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        sample_queryset = instance.samples.all()
        from_limit = self.request.query_params.get("filter[from]", 0)
        to_limit = self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
        )
        logger.debug(
            "Limiting the time series to the time slice from %s to %s",
            from_limit,
            to_limit,
        )
        sample_queryset = sample_queryset.filter(
            timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
        )
        first_sample = sample_queryset.first()
        from_timestamp_s = (
            first_sample.timestamp_s if first_sample is not None else from_limit
        )
        last_sample = sample_queryset.last()
        to_simtestamp_s = (
            last_sample.timestamp_s if last_sample is not None else to_limit
        )
        instance.sample_count = sample_queryset.count()
        instance.from_timestamp_s = from_timestamp_s
        instance.to_timestamp_s = to_simtestamp_s
        instance.query_timestamp_s = round(datetime.now().timestamp())
        include_queryparam = self.request.query_params.get("include_timeseries", False)
        if include_queryparam:
            instance.timeseries = sample_queryset
            serializer = self.get_serializer(instance, include_timeseries=True)
        else:
            serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NodeFidelityViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = NodeFidelity.objects.all()
    serializer_class = NodeFidelitySerializer
