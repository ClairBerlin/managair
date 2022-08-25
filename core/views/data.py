import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework_json_api.views import ReadOnlyModelViewSet
import pandas as pd

from core.data_viewmodels import (
    NodeTimeseriesListViewModel,
    NodeTimeseriesViewModel,
    InstallationTimeseriesListViewModel,
    InstallationTimeseriesViewModel,
    RoomAirQualityViewModel,
)
from core.models import Node, RoomNodeInstallation
from core.serializers import (
    NodeTimeseriesListSerializer,
    NodeTimeseriesSerializer,
    InstallationTimeseriesListSerializer,
    InstallationTimeSeriesSerializer,
    RoomAirQualitySerializer,
)
from core.data_analysis import (
    prepare_samples,
    compute_metrics_for_month,
    weekday_histogram,
    clean_air_medal,
)

logger = logging.getLogger(__name__)


class NodeTimeSeriesViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Node.objects.all()
    # Use different serializers for different actions.
    # See https://stackoverflow.com/questions/22616973/django-rest-framework-use-different-serializers-in-the-same-modelviewset
    serializer_classes = {
        "list": NodeTimeseriesListSerializer,
        "retrieve": NodeTimeseriesSerializer,
    }
    serializer_class = NodeTimeseriesListSerializer  # fallback

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()
        # Restrict to samples from nodes commanded by the currently authenticated user.
        authorized_nodes = queryset.filter(owner__users=self.request.user)

        if self.action == "retrieve":
            # Restrict the samples to a node, if one is given.
            if "node_pk" in self.kwargs:
                # If the view is accessed via the `node-samples-list` route, it will
                # have been passed the node_pk as lookup_field.
                node_id = self.kwargs["node_pk"]
            elif "pk" in self.kwargs:
                # If the view is accessed via the `timeseries-details` route, it will
                # have been passed the pk as lookup_field.
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
            NodeTimeseriesListViewModel(
                pk=node.pk, node_alias=node.alias, sample_count=node.samples.count()
            )
            for node in queryset
        ]
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(ts_info, many=True, context={"request": request})
        return Response(serializer.data)

    def get_object(self):
        node = self.get_queryset()
        queryset = node.samples
        from_limit = int(self.request.query_params.get("filter[from]", 0))
        to_limit = int(
            self.request.query_params.get(
                "filter[to]", round(datetime.now().timestamp())
            )
        )
        logger.debug(
            "Limiting the time series to the time slice from %s to %s",
            from_limit,
            to_limit,
        )
        samples = queryset.filter(
            timestamp_s__gte=from_limit, timestamp_s__lte=to_limit
        )
        return NodeTimeseriesViewModel(
            pk=node.pk,
            node_alias=node.alias,
            from_timestamp_s=from_limit,
            to_timestamp_s=to_limit,
            samples=samples,
        )


class InstallationTimeSeriesViewSet(ReadOnlyModelViewSet):
    """A view for time series accessed by installation. Each installation has its own time series, constrained by the time slice of the installation."""

    queryset = RoomNodeInstallation.objects.all()
    # Use different serializers for different actions.
    # See https://stackoverflow.com/questions/22616973/django-rest-framework-use-different-serializers-in-the-same-modelviewset
    serializer_classes = {
        "list": InstallationTimeseriesListSerializer,
        "retrieve": InstallationTimeSeriesSerializer,
    }
    serializer_class = InstallationTimeseriesListSerializer  # fallback

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()

        is_public = Q(is_public=True)
        accessible_if_authenticated = Q(node__owner__users=self.request.user)

        if not self.request.user.is_authenticated:
            # Public API access. Restrict the listed installations to those that are
            # publicly visible.
            authorized_installations = queryset.filter(is_public)
        else:
            # Otherwise, Restrict to samples from installations commanded by the
            # currently logged-in user.
            authorized_installations = queryset.filter(
                is_public | accessible_if_authenticated
            )

        if self.action == "retrieve":
            # Restrict the samples to a specific installation, if one is given.
            if "installation_pk" in self.kwargs:
                # If the view is accessed via the `installations-samples-list` route,
                # it will have been passed the installation_pk as lookup_field.
                installation_id = self.kwargs["installation_pk"]
            elif "pk" in self.kwargs:
                # If the view is accessed via the `installation-timeseries-details`
                # route, it will have been passed the pk as lookup_field.
                installation_id = self.kwargs["pk"]
            else:
                raise MethodNotAllowed

            logger.debug(
                "Retrieve time series for individual node installation %s",
                installation_id,
            )
            return get_object_or_404(authorized_installations, pk=installation_id)

        elif self.action == "list":
            logger.debug(
                "Retrieve time series overview of all accessible node installations."
            )
            return authorized_installations
        else:
            raise MethodNotAllowed

    def get_serializer_class(self):
        # TODO: Does not work for related fields because of this upstream bug:
        # https://github.com/django-json-api/django-rest-framework-json-api/issues/859
        return self.serializer_classes.get(self.action, self.serializer_class)

    def list(self, request):
        queryset = self.get_queryset()
        ts_info = [
            InstallationTimeseriesListViewModel(
                pk=installation.pk,
                node_id=installation.node.id,
                node_alias=installation.node.alias,
                from_timestamp_s=installation.from_timestamp_s,
                to_timestamp_s=installation.to_timestamp_s,
                sample_count=installation.node.samples.filter(
                    timestamp_s__gte=installation.from_timestamp_s,
                    timestamp_s__lte=installation.to_timestamp_s,
                ).count(),
            )
            for installation in queryset
        ]
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(ts_info, many=True, context={"request": request})
        return Response(serializer.data)

    def get_object(self):
        installation = self.get_queryset()
        queryset = installation.node.samples.all()
        # Limit time-slice to node installation and query.
        install_from_s = installation.from_timestamp_s
        install_to_s = installation.to_timestamp_s
        filter_from_s = int(self.request.query_params.get("filter[from]", 0))
        filter_to_s = int(
            self.request.query_params.get(
                "filter[to]", round(datetime.now().timestamp())
            )
        )
        from_max_s = max(install_from_s, filter_from_s)
        to_min_s = min(install_to_s, filter_to_s)
        logger.debug(
            "Limiting the time series to the time slice from %s to %s",
            from_max_s,
            to_min_s,
        )
        samples = queryset.filter(
            timestamp_s__gte=from_max_s, timestamp_s__lte=to_min_s
        ).distinct()

        return InstallationTimeseriesViewModel(
            pk=installation.pk,
            node_id=installation.node.id,
            node_alias=installation.node.alias,
            from_timestamp_s=from_max_s,
            to_timestamp_s=to_min_s,
            samples=samples,
        )


class RoomAirQualityViewSet(ReadOnlyModelViewSet):
    """A read-only view for air quality information of a given room, computed on the fly from the room's installed sensor. Currently, only a single sensor per room is supported."""

    queryset = RoomNodeInstallation.objects.all()
    serializer_class = RoomAirQualitySerializer

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()

        is_public = Q(is_public=True)
        accessible_if_authenticated = Q(node__owner__users=self.request.user)

        if not self.request.user.is_authenticated:
            # Public API access. Restrict the listed installations to those that are
            # publicly visible.
            authorized_installations = queryset.filter(is_public)
        else:
            # Otherwise, Restrict to samples from installations commanded by the
            # currently logged-in user.
            authorized_installations = queryset.filter(
                is_public | accessible_if_authenticated
            )

        if self.action == "retrieve" and "pk" in self.kwargs:
            pk = self.kwargs["pk"]
            return (
                authorized_installations.filter(room=pk)
                .distinct()
                .order_by("from_timestamp_s")
            )
        else:
            raise MethodNotAllowed

    def get_object(self):
        installations_queryset = self.get_queryset()
        date_str = self.kwargs.get("month", datetime.today().strftime("%Y-%m"))
        month = datetime.strptime(date_str, "%Y-%m")
        start_of_month = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = start_of_month  + relativedelta(months=+1)
        from_s = start_of_month.timestamp()
        to_s = end_of_month.timestamp()
        installations_in_slice = installations_queryset.filter(
            to_timestamp_s__gte=from_s, from_timestamp_s__lte=to_s
        )
        sample_set = []
        if installations_in_slice.count() == 0:
            raise Http404(
                f"In the requested time slice, the selected room has no accessible installations to draw measurement samples from."
            )
        elif installations_in_slice.count() > 1:
            for index in range(1, installations_in_slice.count() - 1):
                # Ensure that there is a single active installation in the room at any
                # point in time.
                prev_installation_to = installations_in_slice[index - 1].to_timestamp_s
                succ_installation_from = installations_in_slice[index].from_timestamp_s
                if succ_installation_from <= prev_installation_to:
                    raise Http404(
                        f"The room has multiple installations active at the same time, which we cannot analyze yet."
                    )
            sample_querysets = [
                installation.node.samples.filter(
                    timestamp_s__gte=from_s, timestamp_s__lte=to_s
                )
                for installation in installations_in_slice
            ]
            sample_set = (
                sample_querysets[0]
                .union(*sample_querysets[1:])
                .order_by("timestamp_s")
            )
        else:
            sample_set = installations_in_slice[0].node.samples.filter(
                timestamp_s__gte=from_s, timestamp_s__lte=to_s
            ).order_by("timestamp_s")

        values = sample_set.values("timestamp_s", "co2_ppm")
        samples = pd.DataFrame.from_records(values)
        samples["timestamp_s"] = pd.to_datetime(samples["timestamp_s"], unit="s")
        samples.set_index("timestamp_s", inplace=True)
        prepared_samples = prepare_samples(samples)
        (daily_metrics, hourly_metrics) = compute_metrics_for_month(prepared_samples, date_str)
        hist = weekday_histogram(hourly_metrics)
        print(hist)
        medal = clean_air_medal(daily_metrics)
        print(medal)