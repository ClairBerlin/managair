import pandas as pd
from .preprocessing import sliceby_day


class Day_Metrics:
    """
    Class to store summary statistics for a given day and to compute derived values.
    """

    MAX_DAY_GAP_S = 3600  # Maximum accumulated gap duration for metrics to be valid
    max_co2_ppm = None
    mean_co2_ppm = None
    excess_duration_s = None
    mean_excess_co2_ppm = None

    def __init__(self, day, day_duration_s, gap_duration_s):
        self.day = (
            day  # Date of the day described by the present instance of the class.
        )
        self.day_duration_s = day_duration_s  # Duration of the day in s (for leap days)
        self.gap_duration_s = gap_duration_s  # Total duration missing samples.

    @property
    def is_valid(self):
        return self.gap_duration_s <= self.MAX_DAY_GAP_S

    @property
    def has_samples(self):
        return self.gap_duration_s < self.day_duration_s

    @property
    def excess_rate(self):
        if self.has_samples:
            return self.excess_duration_s / (self.day_duration_s - self.gap_duration_s)
        else:
            return None

    @property
    def excess_score(self):
        if self.has_samples:
            return self.mean_excess_co2_ppm * self.excess_rate
        else:
            return None

    def gap_rate(self):
        return 1 - self.gap_duration_s / self.day_duration_s

    def has_data(self):
        return (
            (self.max_co2_ppm is not None)
            and (self.mean_co2_ppm is not None)
            and (self.excess_duration_s is not None)
            and (self.mean_excess_co2_ppm is not None)
            and (self.excess_rate is not None)
            and (self.excess_score is not None)
        )


def prepare_daily_metrics(samples, sampling_rate_s, concentration_threshold_ppm):
    """
    Compute daily metrics for a month's samples; convert metrics into a new data frame.

    TODO: Streamline conversion without the need for the interim Day_Metrics object
    """
    daily_samples = sliceby_day(samples)
    # Use dict comprehension to create a metrics object for each day of the incoming
    # month-samples.
    day_metrics_dict = {
        day: daily_key_metrics(
            day=day,
            samples=samples,
            sampling_rate_s=sampling_rate_s,
            concentration_threshold_ppm=concentration_threshold_ppm,
        )
        for (day, samples) in daily_samples.items()
    }
    # As further processing is simpler when using a data frame, convert the dict of
    # Day_Metrics objects into a new data frame. Construct the data frame from a list.
    daily_metrics_list = [
        {
            "day": m.day,
            "is_valid": m.is_valid,
            "day_duration_s": m.day_duration_s,
            "gap_duration_s": m.gap_duration_s,
            "max_co2_ppm": m.max_co2_ppm,
            "mean_co2_ppm": m.mean_co2_ppm,
            "excess_duration_s": m.excess_duration_s,
            "mean_excess_co2": m.mean_excess_co2_ppm,
            "excess_rate": m.excess_rate,
            "excess_score": m.excess_score,
        }
        for (day, m) in day_metrics_dict.items()
    ]
    month_metrics = pd.DataFrame(daily_metrics_list)
    month_metrics.set_index("day", inplace=True)
    return month_metrics


def daily_key_metrics(day, samples, sampling_rate_s, concentration_threshold_ppm):
    """
        Compute key statistics from the samples of a given day

    Args:
        day (Pandas DateTime): The day for which to compute the metrics
        samples (Pandas data frame): datetime index, co2_ppm value column
        sampling_rate_s (Integer): Uniform sampling rate used
        concentration_threshold_ppm (Integer): Threshold for good air quality (e.g., Pettenkofer number)

    Returns:
        Day_Metrics
    """
    day_duration_s = 86400
    actual_duration_s = samples.size * sampling_rate_s  # For incomplete days
    gap_samples = samples[
        samples["co2_ppm"].isna()
    ]  # Exclude samples marked as missing
    gap_duration_s = gap_samples.size * sampling_rate_s + max(
        (day_duration_s - actual_duration_s), 0
    )

    metrics = Day_Metrics(
        day=day, day_duration_s=day_duration_s, gap_duration_s=gap_duration_s
    )

    if gap_duration_s < day_duration_s:
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
