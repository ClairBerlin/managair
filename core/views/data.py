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
from core.data_analysis.airquality import TIMEZONE

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
    TARGET_RATE_S,
    CLEAN_AIR_THRESHOLD_PPM,
    compute_daily_metrics,
    compute_hourly_metrics,
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
    """A read-only view for air quality information of a given room, computed on the fly. Currently, only a single sensor per room is supported."""

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

    def __month_slice(self, year_month_str):
        """Determine start and end timestamps of the month under analysis."""
        month = datetime.strptime(year_month_str, "%Y-%m")
        start_of_month = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = start_of_month + relativedelta(months=+1)
        from_s = start_of_month.timestamp()
        to_s = end_of_month.timestamp()
        return (from_s, to_s)

    def __past_30_days(self, now):
        """Determine start and end timestamps for the past 30 days."""
        range_end = now.floor("D")  # Start of the day
        range_start = range_end - pd.Timedelta(30, "D")
        to_s = range_end.timestamp()
        from_s = range_start.timestamp()
        return (from_s, to_s)

    def __prepare_sample_query(self, installations_queryset, from_s, to_s):
        """Find all non-overlapping installations in the given room. Construct a query that concatenates the samples of these installations. Fail the request if none or more than one installations are active at the same time."""
        installations_in_slice = installations_queryset.filter(
            to_timestamp_s__gte=from_s, from_timestamp_s__lte=to_s
        )
        if installations_in_slice.count() == 0:
            raise Http404(
                "In the requested time slice, the selected room has no accessible installations to draw measurement samples from."
            )
        if installations_in_slice.count() > 1:
            for index in range(1, installations_in_slice.count() - 1):
                # Ensure that there is a single active installation in the room at any
                # point in time.
                prev_installation_to = installations_in_slice[index - 1].to_timestamp_s
                succ_installation_from = installations_in_slice[index].from_timestamp_s
                if succ_installation_from <= prev_installation_to:
                    raise Http404(
                        "The room has multiple installations active at the same time, which we cannot analyze yet."
                    )
            sample_querysets = [
                installation.node.samples.filter(
                    timestamp_s__gte=from_s, timestamp_s__lte=to_s
                )
                for installation in installations_in_slice
            ]
            sample_set = (
                sample_querysets[0].union(*sample_querysets[1:]).order_by("timestamp_s")
            )
        else:
            sample_set = (
                installations_in_slice[0]
                .node.samples.filter(timestamp_s__gte=from_s, timestamp_s__lte=to_s)
                .order_by("timestamp_s")
            )
        return sample_set

    def __load_samples(self, sample_set):
        """Trigger the DB query and convert the retrieved samples in a data frame with date/time index."""
        values = sample_set.values("timestamp_s", "co2_ppm")
        samples = pd.DataFrame.from_records(values)
        samples["timestamp_s"] = pd.to_datetime(samples["timestamp_s"], unit="s")
        samples.set_index("timestamp_s", inplace=True)
        return samples

    def get_object(self):
        now = pd.Timestamp.now().tz_localize(TIMEZONE)
        installations_queryset = self.get_queryset()
        if "year_month" in self.kwargs:
            year_month_str = self.kwargs.get("year_month")
            (from_s, to_s) = self.__month_slice(year_month_str)
            sample_set = self.__prepare_sample_query(
                installations_queryset, from_s, to_s
            )
        else:
            (from_s, to_s) = self.__past_30_days(now)
            sample_set = self.__prepare_sample_query(
                installations_queryset, from_s, to_s
            )
        samples = self.__load_samples(sample_set)
        working_samples = prepare_samples(samples)

        daily_metrics = compute_daily_metrics(
            samples=working_samples,
            sampling_rate_s=TARGET_RATE_S,
            concentration_threshold_ppm=CLEAN_AIR_THRESHOLD_PPM,
        )

        medal = clean_air_medal(daily_metrics)

        airquality = RoomAirQualityViewModel(
            pk=self.kwargs["pk"],
            clean_air_medal=medal,
            from_timestamp_s=from_s,
            to_timestamp_s=to_s,
            airq_hist=None,
        )

        include_histogram = self.request.query_params.get("include_histogram", "false")
        if include_histogram.lower() == "true":
            hourly_metrics = compute_hourly_metrics(
                samples=working_samples,
                sampling_rate_s=TARGET_RATE_S,
                concentration_threshold_ppm=CLEAN_AIR_THRESHOLD_PPM,
            )
            hist = weekday_histogram(hourly_metrics)
            airquality.airq_hist = {
                "Mo": hist[0]["excess_score"].values.tolist()
                if 0 in hist.keys() and len(hist[0]) == 24
                else [],
                "Tu": hist[1]["excess_score"].values.tolist()
                if 1 in hist.keys() and len(hist[1]) == 24
                else [],
                "We": hist[2]["excess_score"].values.tolist()
                if 2 in hist.keys() and len(hist[2]) == 24
                else [],
                "Th": hist[3]["excess_score"].values.tolist()
                if 3 in hist.keys() and len(hist[3]) == 24
                else [],
                "Fr": hist[4]["excess_score"].values.tolist()
                if 4 in hist.keys() and len(hist[4]) == 24
                else [],
                "Sa": hist[5]["excess_score"].values.tolist()
                if 5 in hist.keys() and len(hist[5]) == 24
                else [],
                "Su": hist[6]["excess_score"].values.tolist()
                if 6 in hist.keys() and len(hist[6]) == 24
                else [],
            }
        return airquality
