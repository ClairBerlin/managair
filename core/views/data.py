from datetime import datetime
from uuid import UUID

from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework_json_api.views import viewsets
from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework import permissions, generics, views, filters
from rest_framework.response import Response
from rest_framework.request import Request

from core.models import Sample, Node
from core.data_viewmodels import TimeseriesViewModel, SamplePageViewModel
from core.serializers import SampleSerializer, TimeseriesSerializer, SimpleSampleSerializer, SampleListSerializer

class PagesizeLimitedPagination(JsonApiPageNumberPagination):
    """Enforce pagination with a given page size. Can be override in a query."""
    page_size = 100
    

class SampleViewSet(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
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
        # Restrict to nodes commanded by the currently logged-in user.
        nodes = Node.get_user_nodes(self.request.user)
        # Further restrict to node given as query parameter
        node_id = self.request.query_params.get('filter[node_ref]', None)
        if node_id is not None:
            query_node = Node.objects.get(pk=node_id)
            nodes = nodes.union(query_node)
        # Time-slicing query parameter
        from_limit = self.request.query_params.get('filter[from]', 0)
        to_limit = self.request.query_params.get(
                'filter[to]', round(datetime.now().timestamp()))

        queryset = super(SampleViewSet, self).get_queryset()
        queryset = queryset.filter(node_ref__in=nodes)
        queryset = queryset.filter(
                timestamp_s__gte=from_limit,
                timestamp_s__lte=to_limit)
        return queryset


class TimeseriesViewSet(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
    """
    Provides optimized time-series resources.

    The overview resource lists the sample count for each node.
    The detail resource contains a list of samples for a given node. This list can be restricted via `filter[from]` and `filter[to]` query parameters, and it can be paged.
    WARNING: There is no default page size. A query without any paramter may, therefore, return a very large resource.
    TODO: Provide some query limit to prevent DOS attacks.
    """
    queryset = Sample.objects.all() # Not used but necessary to get links right.
    serializer_class = SimpleSampleSerializer # TODO: Cleanup

    class JSONAPIMeta:
        resource_name = "node-timeseries"

    def get_queryset(self):
        """Restrict to logged-in user"""
        return Node.objects.filter(node_installations__site__responsible=self.request.user)

    def list(self, request):
        queryset = self.get_queryset()
        ts_info = [ TimeseriesViewModel(
                        pk=node.pk,
                        alias=node.alias,
                        sample_count=node.samples.count())
                    for node in queryset]
        serializer = TimeseriesSerializer(ts_info, many=True)
        return Response(serializer.data)
    

    def retrieve(self, request, pk=None):
        """Return the time series of a given node."""

        queryset = self.get_queryset()

        # Prepare a sample-query and filter for the requested time slice.
        from_limit = self.request.query_params.get('filter[from]', 0)
        to_limit = self.request.query_params.get(
            'filter[to]', round(datetime.now().timestamp()))
        node = queryset.get(pk=pk)
        queryset = node.samples.filter(
            timestamp_s__gte=from_limit,
            timestamp_s__lte=to_limit)

        # Retrieve a single page. This is where we actually hit the DB.
        page = self.paginate_queryset(queryset)

        # Serialize the sample list with additional header-infos.
        if page is not None:
            sp = SamplePageViewModel(
                    pk=pk, 
                    alias=node.alias,
                    samples=page,
                    from_timestamp=page[0].timestamp_s,
                    to_timestamp=page[-1].timestamp_s
                    )
            serializer = SampleListSerializer(sp)
            paginated_response = self.get_paginated_response(serializer.data)
            return paginated_response
        else:
            #TODO: Fix serializer or raise error.
            # This branch should never be taken.
            serializer = self.get_serializer(
                queryset, context=context, many=True)
            return Response(serializer.data)
