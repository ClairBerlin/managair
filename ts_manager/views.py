from datetime import datetime

from rest_framework_json_api.views import viewsets
from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework import permissions, generics, views, filters
from rest_framework.settings import api_settings
from rest_framework.response import Response
from rest_framework.request import Request
from datetime import datetime
from uuid import UUID

from ts_manager.models import Sample
from ts_manager.viewmodels import TimeseriesViewModel, SamplePageViewModel
from ts_manager.serializers import SampleSerializer, TimeseriesSerializer, SimpleSampleSerializer, SampleListSerializer
from device_manager.models import Node

class PagesizeLimitedPagination(JsonApiPageNumberPagination):
    """Enforce pagination with a given page size. Can be override in a query."""
    page_size = 100
    

class SampleViewSet(viewsets.ReadOnlyModelViewSet):
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
        queryset = Sample.objects.all()
        node_id = self.request.query_params.get('filter[node_ref]', None)
        from_limit = self.request.query_params.get('filter[from]', 0)
        to_limit = self.request.query_params.get(
                'filter[to]', round(datetime.now().timestamp()))
        if node_id is not None:
            queryset = queryset.filter(node_ref__exact=UUID(node_id))
        
        queryset = queryset.filter(
                timestamp_s__gte=from_limit,
                timestamp_s__lte=to_limit)
        return queryset


class TimeseriesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides optimized time-series resources.

    The overview resource lists the sample count for each node.
    The detail resource contains a list of samples for a given node. This list can be restricted via `filter[from]` and `filter[to]` query parameters, and it can be paged.
    WARNING: There is no default page size. A query without any paramter may, therefore, return a very large resource.
    TODO: Provide some query limit to prevent DOS attacks.
    """
    queryset = Node.objects.all()
    serializer_class = SimpleSampleSerializer # TODO: Cleanup

    def list(self, request):
        ts_info = [ TimeseriesViewModel(
                        pk=node.pk,
                        alias=node.alias,
                        sample_count=node.samples.count())
                    for node in Node.objects.all()]
        serializer = TimeseriesSerializer(ts_info, many=True)
        return Response(serializer.data)
    

    def retrieve(self, request, pk=None):
        """Return the time series of a given node."""

        # Prepare a sample-query and filter for the requested time slice.
        from_limit = self.request.query_params.get('filter[from]', 0)
        to_limit = self.request.query_params.get(
            'filter[to]', round(datetime.now().timestamp()))
        node = Node.objects.get(pk=pk)
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
    
