import logging
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.views import ReadOnlyModelViewSet, generics

from core.data_viewmodels import SamplePageViewModel, TimeseriesViewModel
from core.models import Sample, Node
from core.serializers import (
    SampleSerializer,
    SimpleSampleSerializer,
    SampleListSerializer,
    TimeseriesSerializer,
)

logger = logging.getLogger(__name__)


class PagesizeLimitedPagination(JsonApiPageNumberPagination):
    """Enforce pagination with a given page size. Can be override in a query."""

    page_size = 100


class SampleListView(LoginRequiredMixin, generics.ListAPIView):
    """Samples reported by the node on the resource path.
    The currently logged-in user must have access to the given node. That is, the user must be part of the organization that owns the node.

    Samples will be returned in ascending order according to their time stamp.
    """

    serializer_class = SimpleSampleSerializer
    queryset = Node.objects.all()

    def get_queryset(self):
        """
        Optionally restricts the returned samples to a given time slice and node.
        """
        queryset = super().get_queryset()
        # Restrict to samples from nodes commanded by the currently logged-in user.
        authorized_nodes = queryset.filter(owner__users=self.request.user)

        # Furthermore, restrict the samples to a node, if one is given.
        if self.lookup_field:
            # If the view is accessed via the `node-samples-list` route, it will have
            # been passed the node-pk as lookup_field.
            node_id = self.kwargs[self.lookup_field]
            logger.debug("Building a sample-query for node %s.", node_id)
            node = get_object_or_404(authorized_nodes, pk=node_id)
            queryset = node.samples
        else:
            raise MethodNotAllowed
        # Time-slicing query parameter
        from_limit = self.request.query_params.get("filter[from]", 0)
        to_limit = self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
        )
        logger.debug("Time-slicing samples from %d to %d", from_limit, to_limit)
        queryset = queryset.filter(
            timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
        )
        return queryset


class TimeSeriesViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Node.objects.all()
    # Use different serializers for different actions.
    # See https://stackoverflow.com/questions/22616973/django-rest-framework-use-different-serializers-in-the-same-modelviewset
    serializer_classes = {
        "list": TimeseriesSerializer,
        "retrieve": SampleListSerializer,
    }
    serializer_class = TimeseriesSerializer  # fallback

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()
        # Restrict to samples from nodes commanded by the currently logged-in user.
        authorized_nodes = queryset.filter(owner__users=self.request.user)

        if self.action == "retrieve":
            # Restrict the samples to a node, if one is given.
            if "node_pk" in self.kwargs:
                # If the view is accessed via the `node-samples-list` route, it will
                # have been passed the node_pk as lookup_field.
                node_id = self.kwargs["node_pk"]
            elif "pk" in self.kwargs:
                # If the view is accessed via the `timeseries-details` route, it will have
                # been passed the pk as lookup_field.
                node_id = self.kwargs["pk"]
            else:
                raise MethodNotAllowed

            logger.debug("Retrieve time series for individual node %s", node_id)
            return get_object_or_404(authorized_nodes, pk=node_id)

        elif self.action == "list":
            logger.debug("Retrieve time series overview of all accessible nodes.")
            return authorized_nodes
        else:
            raise MethodNotAllowed

    def get_serializer_class(self):
        # TODO: Does not work for related fields because of this upstream bug:
        # https://github.com/django-json-api/django-rest-framework-json-api/issues/859
        return self.serializer_classes.get(self.action, self.serializer_class)

    def list(self, request):
        queryset = self.get_queryset()
        ts_info = [
            TimeseriesViewModel(
                pk=node.pk, alias=node.alias, sample_count=node.samples.count()
            )
            for node in queryset
        ]
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(ts_info, many=True, context={"request": request})
        return Response(serializer.data)

    def get_object(self):
        node = self.get_queryset()
        queryset = node.samples
        from_limit = self.request.query_params.get("filter[from]", 0)
        to_limit = self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
        )
        logger.debug(
            "Limiting the time series to the time slice from %d to %d",
            from_limit,
            to_limit,
        )
        samples = queryset.filter(
            timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
        )
        return SamplePageViewModel(
            pk=node.pk,
            alias=node.alias,
            from_timestamp=from_limit,
            to_timestamp=to_limit,
            samples=samples,
        )


class SampleViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    """
    Retrieve individual samples and lists of samples.

    Filtering is possible by time-slice and node-id.
    Samples are returned in a verbose JSON:API format, with a maximum page size of 100 entries by default.
    """

    serializer_class = SampleSerializer
    queryset = Sample.objects.all()
    pagination_class = PagesizeLimitedPagination

    def get_queryset(self, *args, **kwargs):
        """
        Optionally restricts the returned samples to a given time slice and node.
        """
        queryset = super().get_queryset()
        # Restrict to samples from nodes commanded by the currently logged-in user.
        nodes = Node.objects.filter(owner__users=self.request.user)
        queryset = queryset.filter(node__in=nodes)
        # Further restrict to node given as query parameter
        if self.action == "list":
            queryset = queryset.filter(node__in=nodes)
            node_id = self.request.query_params.get("filter[node]", None)
            if node_id is not None:
                logger.debug("Restrict samples to node %s.", node_id)
                get_object_or_404(nodes, pk=node_id)  # Check if node exists.
                queryset = queryset.filter(node=node_id)
            queryset = queryset.filter(node__in=nodes)
            # Time-slicing query parameter
            from_limit = self.request.query_params.get("filter[from]", 0)
            to_limit = self.request.query_params.get(
                "filter[to]", round(datetime.now().timestamp())
            )
            logger.debug(
                "Limiting the sample set to the time slice from %d to %d",
                from_limit,
                to_limit,
            )
            queryset = queryset.filter(
                timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
            )

        return queryset.distinct()
