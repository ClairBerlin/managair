import pandas as pd
from .preprocessing import sliceby_hour


class Hour_Metrics:
    """
    Class to store summary statistics for a given hour and to compute derived values.
    """

    SECONDS_PER_HOUR = 3600
    MAX_GAP_S = 600  # For hour statistics, only one sample may be amiss.
    max_co2_ppm = None
    mean_co2_ppm = None
    excess_duration_s = None
    mean_excess_co2_ppm = None

    def __init__(self, hour, gap_duration_s):
        self.hour = hour  # Date-time of the hour of the present instance
        if gap_duration_s >= self.MAX_GAP_S:
            self.gap_duration_s = self.SECONDS_PER_HOUR - 1  # To make computations safe
        else:
            self.gap_duration_s = gap_duration_s

    @property
    def is_valid(self):
        return self.gap_duration_s < self.MAX_GAP_S

    @property
    def excess_rate(self):
        return (
            self.excess_duration_s / (self.SECONDS_PER_HOUR - self.gap_duration_s)
            if self.is_valid
            else None
        )

    @property
    def excess_score(self):
        if self.is_valid:
            return self.mean_excess_co2_ppm * self.excess_rate
        else:
            return None

    def gap_rate(self):
        return 1 - self.gap_duration_s / self.SECONDS_PER_HOUR if self.is_valid else 1

    def has_data(self):
        return (
            self.is_valid
            and (self.max_co2_ppm is not None)
            and (self.mean_co2_ppm is not None)
            and (self.excess_duration_s is not None)
            and (self.mean_excess_co2_ppm is not None)
            and (self.excess_rate is not None)
            and (self.excess_score is not None)
        )


def hourly_key_metrics(hour, samples, sampling_rate_s, concentration_threshold_ppm):
    """
        Compute key statistics from the samples of a given hour

    Args:
        hour (Pandas DateTime): The hour for which to compute the metrics
        samples (Pandas data frame): datetime index, co2_ppm value column
        sampling_rate_s (Integer): Uniform sampling rate used
        concentration_threshold_ppm (Integer): Threshold for good air quality (e.g., Pettenkofer number)

    Returns:
        Hour_Metrics
    """
    # Require full hours. Disregard incomplete hours at the start or end of a sampling
    # interval.
    if samples.size * sampling_rate_s != 3600:
        return None
    gap_samples = samples[samples["co2_ppm"].isna()]
    gap_duration_s = gap_samples.size * sampling_rate_s

    metrics = Hour_Metrics(hour=hour, gap_duration_s=gap_duration_s)
    # Tolerate a single missing sample only
    if gap_duration_s <= 600 and gap_samples.size <= 1:
        metrics.max_co2_ppm = samples["co2_ppm"].max()
        metrics.mean_co2_ppm = samples["co2_ppm"].mean()
        excess_co2_ppm = samples[
            samples["co2_ppm"] >= concentration_threshold_ppm
        ].copy()
        excess_co2_ppm["co2_ppm"] = excess_co2_ppm["co2_ppm"].subtract(
            concentration_threshold_ppm
        )
        metrics.excess_duration_s = excess_co2_ppm.size * sampling_rate_s
        if metrics.excess_duration_s == 0:
            metrics.mean_excess_co2_ppm = 0
        else:
            metrics.mean_excess_co2_ppm = excess_co2_ppm["co2_ppm"].mean()
    return metrics


def prepare_hourly_metrics(samples, sampling_rate_s, concentration_threshold_ppm):
    """
    Compute hourly metrics for a month's samples; convert metrics into a new data frame.

    TODO: Streamline conversion without the need for the interim Hour_Metrics object
    """
    hourly_samples = sliceby_hour(samples)
    # Use dict comprehension to create a metrics object for each hour of the incoming
    # month-samples.
    hourly_metrics_dict = {
        hour: hourly_key_metrics(
            hour=hour,
            samples=samples,
            sampling_rate_s=sampling_rate_s,
            concentration_threshold_ppm=concentration_threshold_ppm,
        )
        for (hour, samples) in hourly_samples.items()
    }
    # As further processing is simpler when using a data frame, convert the dict of
    # Hour_Metrics objects into a new data frame. Construct the data frame from a list.
    hourly_metrics_list = [
        {
            "hour": m.hour,
            "is_valid": m.is_valid,
            "gap_duration_s": m.gap_duration_s,
            "max_co2_ppm": m.max_co2_ppm,
            "mean_co2_ppm": m.mean_co2_ppm,
            "excess_duration_s": m.excess_duration_s,
            "mean_excess_co2": m.mean_excess_co2_ppm,
            "excess_rate": m.excess_rate,
            "excess_score": m.excess_score,
        }
        for (hour, m) in hourly_metrics_dict.items() if m is not None
    ]
    hourly_metrics = pd.DataFrame(hourly_metrics_list)
    hourly_metrics.set_index("hour", inplace=True)
    return hourly_metrics
