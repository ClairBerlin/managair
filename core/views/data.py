from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
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
        queryset = super(SampleListView, self).get_queryset()
        # Restrict to samples from nodes commanded by the currently logged-in user.
        authorized_nodes = queryset.filter(owner__users=self.request.user)

        # Furthermore, restrict the samples to a node, if one is given.
        if self.lookup_field:
            # If the view is accessed via the `node-samples-list` route, it will have
            # been passed the node-pk as lookup_field.
            node_id = self.kwargs[self.lookup_field]
            node = get_object_or_404(authorized_nodes, pk=node_id)
            queryset = node.samples
        else:
            raise MethodNotAllowed
        # Time-slicing query parameter
        from_limit = self.request.query_params.get("filter[from]", 0)
        to_limit = self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
        )
        queryset = queryset.filter(
            timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
        )
        return queryset


class TimeSeriesListView(LoginRequiredMixin, generics.ListAPIView):
    queryset = Node.objects.all()
    serializer_class = TimeseriesSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        return Node.objects.filter(owner__users=self.request.user)

    def list(self, request):
        queryset = self.get_queryset()
        ts_info = [
            TimeseriesViewModel(
                pk=node.pk, alias=node.alias, sample_count=node.samples.count()
            )
            for node in queryset
        ]
        serializer = TimeseriesSerializer(ts_info, many=True)
        return Response(serializer.data)


class TimeseriesDetailView(LoginRequiredMixin, generics.RetrieveAPIView):
    queryset = Node.objects.all()
    serializer_class = SampleListSerializer

    def get_queryset(self):
        queryset = super(TimeseriesDetailView, self).get_queryset()
        # Restrict to samples from nodes commanded by the currently logged-in user.
        authorized_nodes = queryset.filter(owner__users=self.request.user)

        # Furthermore, restrict the samples to a node, if one is given.
        if self.lookup_field:
            # If the view is accessed via the `node-samples-list` route, it will have
            # been passed the node-pk as lookup_field.
            node_id = self.kwargs[self.lookup_field]
            return get_object_or_404(authorized_nodes, pk=node_id)
        else:
            raise MethodNotAllowed

    def get_object(self):
        node = self.get_queryset()
        queryset = node.samples
        from_limit = self.request.query_params.get("filter[from]", 0)
        to_limit = self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
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

    def get_queryset(self):
        """
        Optionally restricts the returned samples to a given time slice and node.
        """
        # Restrict to samples from nodes commanded by the currently logged-in user.
        nodes = Node.objects.filter(owner__users=self.request.user)
        # Further restrict to node given as query parameter
        node_id = self.request.query_params.get("filter[node]", None)
        if node_id is not None:
            query_node = Node.objects.get(pk=node_id)
            nodes = nodes.union(query_node)
        # Time-slicing query parameter
        from_limit = self.request.query_params.get("filter[from]", 0)
        to_limit = self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
        )

        queryset = super(SampleViewSet, self).get_queryset()
        queryset = queryset.filter(node__in=nodes)
        queryset = queryset.filter(
            timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
        )
        return queryset
