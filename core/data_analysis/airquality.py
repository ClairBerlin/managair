import pandas as pd
from .preprocessing import (
    find_gaps,
    mark_gaps,
    resample_to_uniform_grid,
    sliceby_month,
    sliceby_weekday,
)
from .daymetrics import prepare_daily_metrics
from .hourmetrics import prepare_hourly_metrics

CLEAN_AIR_THRESHOLD_PPM = 1000
BAD_AIR_THRESHOLD_PPM = 2000
EXCESS_SCORE_THRESHOLD = 150
EXCESS_RATE = 0.3  # Admissible fraction of days above threshold
VALID_DAY_RATE = 0.6  # Required rate of days with sufficient data quality.

MAX_GAP = "30min"  # maximum gap between successive samples to tolerate
TARGET_RATE = "10min"  # uniform sampling frequency to transform the data to
TARGET_RATE_S = 600
TIMEZONE = "Europe/Berlin"

def prepare_samples(samples):
    """Most samples are nonuniformly spaced because of transmission delays and clock skew. To simplify processing, resample these samples on a uniform grid at the target_rate. This might lead to some noise amplification for stretches of sparse original samples. If the gaps between subsequent samples are too large, resampling will yield mostly noise; therefore, we exclude these stretches and insert NaN-values instead."""

    gaps = find_gaps(samples, MAX_GAP, TIMEZONE)

    samples.index = samples.index.tz_localize("UTC").tz_convert(TIMEZONE)

    uniform_samples = resample_to_uniform_grid(samples, TARGET_RATE)
    return mark_gaps(uniform_samples, gaps)


def compute_metrics_for_month(samples, month):

    # Take a single month for all day-based analyses, as this is the time slice
    # returned via the API
    monthly_samples = sliceby_month(samples)
    month = pd.Timestamp(month).tz_localize(TIMEZONE)
    month_samples = monthly_samples[month]

    # Pandas data frame of daily metrics for the given month; i.e. summary statistics
    # for each day of the selected month. With 10min sampling rate, the statistics are
    # computed over 24*6 = 144 samples a day, except for leap days.
    daily_metrics = prepare_daily_metrics(
        samples=month_samples,
        sampling_rate_s=TARGET_RATE_S,
        concentration_threshold_ppm=CLEAN_AIR_THRESHOLD_PPM,
    )

    # Pandas data frame of hourly metrics for the given month; i.e., summary statistics
    # for each hour of the selected month. With 10 min sampling rate, the statistics
    # are computed over 6 samples per hour (which is not that much).
    hourly_metrics = prepare_hourly_metrics(
        samples=month_samples,
        sampling_rate_s=TARGET_RATE_S,
        concentration_threshold_ppm=CLEAN_AIR_THRESHOLD_PPM,
    )
    return (daily_metrics, hourly_metrics)


def weekday_histogram(hourly_metrics):
    """
        Compute a histogram across weekdays of the provided input

    Args:
        hourly_metrics (Pandas data frame): date-time index with hour resolution, metrics columns

    Returns:
        Weekday-Dict: hourly sumary statistics. Weekdays are indexed starting at 0, with 0 = Sunday
    """
    purged_hourly_metrics = hourly_metrics[hourly_metrics["is_valid"] == True]
    weekday_metrics = sliceby_weekday(purged_hourly_metrics)
    return {
        weekday: m.groupby(m.index.hour).mean()
        for (weekday, m) in weekday_metrics.items()
    }


def clean_air_medal(daily_metrics):
    """
    Determines from the daily summary statistics if the clean-air-medal should be awarded for the given month.

    Args:
        daily_metrics (Pandas data frame): Data frame with daily metrics for a given month, for which

    Returns:
        Boolean: If the clean-air-medal is awarded for the given month or not. None for missing data.
    """

    # Wenn alle Maximalwerte unter 2000 ppm waren, nie eine rote Ampel auftrat (d.h. der Wert lag
    # auch nicht an einem Tag über 30% der Zeit über dem Referenzwert) und weniger als 30% Gelbe-Ampel-Tagesbewertungen, wird die Frischluft-Medaille vergeben
    days_count = daily_metrics["is_valid"].count()
    valid_days = daily_metrics[daily_metrics["is_valid"]]
    valid_days_count = valid_days["is_valid"].count()

    if valid_days_count / days_count < VALID_DAY_RATE:
        # There are too many samples missing for the given day, so that the metrics
        # loose their meaning.
        return False
    elif (
        valid_days[
            valid_days["max_co2_ppm"] >= BAD_AIR_THRESHOLD_PPM
        ].max_co2_ppm.count()
        > 0
    ):
        # If the CO2 concentration exceeds the BAD_AIR_THRESHOLD even once during the
        # entire month, the clean air medal cannot be awarded.
        return False
    elif (
        valid_days[
            valid_days["excess_score"] >= EXCESS_SCORE_THRESHOLD
        ].excess_score.count()
        > 0
    ):
        # If CO2-concentration exceeds the clean-air threshold on average by more than
        # EXCESS_SCORE_THRESHOLD, the clean air medal cannot be awarded.
        return False
    elif valid_days[
        valid_days["excess_score"] >= 0
    ].excess_score.count() >= EXCESS_RATE * len(valid_days):
        # If the CO2-concentration exceeds the clean air threshold on more than 30% of the days of the given month, the clean air medal cannot be awarded.
        return False
    else:
        return True
