import pandas as pd
from pandas.tseries.frequencies import to_offset
import numpy as np

def find_gaps(samples, max_gap_s, timezone):
    """
    Determins gaps in the data frame of nonuniformly-spaced samples larger than max_gap

    Args:
        samples (Pandas data frame): date-time index and co2_ppm column
        max_gap_s (Int): Maximum admissible gap between subsequent samples (in seconds)
        timezone (String): Time zone in which to output the gap markers

    Returns:
        zip-list: list of start and stop times of identified successive gaps, in the provided time zone.
    """

    # exact start of the first day in range
    start = samples.index[0].tz_localize(timezone).floor("D").tz_convert("UTC").tz_localize(None) 
    # exact end of the last day in range
    end = samples.index[-1].tz_localize(timezone).ceil("D").tz_convert("UTC").tz_localize(None)
    indices = pd.DatetimeIndex([start, *samples.index, end])
    # compute time difference between subsequent samples
    sample_timediff = np.diff(indices) / np.timedelta64(1, "s")
    # identify intervals with gaps between subsequent samples larger than max_gap
    idx = np.where(
        np.greater(sample_timediff, to_offset(max_gap_s).delta.total_seconds())
    )[0]

    gap_start_indices = (
        indices[idx].tz_localize("UTC").tz_convert(timezone).tolist()
    )
    gap_stop_indices = (
        indices[idx + 1].tz_localize("UTC").tz_convert(timezone).tolist()
    )

    # Store start and stop indices of large intervals
    gaps = list(zip(gap_start_indices, gap_stop_indices))
    return gaps


def resample_to_uniform_grid(samples, target_rate):
    """
        Resamples the nonuniformly spaced samples to a uniform target_rate

    Args:
        samples (Pandas data frame): date-time index and co2_ppm column
        target_rate (String): Pandas time string.

    Returns:
        Pandas data frame: Resamples values at uniform rate, interpolated where necessary

    See https://towardsdatascience.com/preprocessing-iot-data-linear-resampling-dde750910531
    """
    # Fake a sample at the start and the end of the time range to get sensible
    # interpolated values. If enough samples are available, the data repetition won't 
    # disturb the following analysis. If not enough samples are available, the fake 
    # samples will be removed by the gap-finder algorithm.
    start = samples.index[0].floor("D")
    end = samples.index[-1].ceil("D")
    samples.loc[start] = samples.iloc[0][0]
    samples.loc[end] = samples.iloc[-1][0]
    samples.sort_index(inplace=True)

    # First upsample with linear interpolation
    upsampled_samples = samples.resample("1min").mean().interpolate()
    # Then downsample with forward fill.
    return upsampled_samples.resample(target_rate).ffill()


def mark_gaps(samples, gaps):
    """Mark resampled values as None where the original data has large gaps."""
    for start, stop in gaps:
        samples[start:stop] = None
    return samples


def sliceby(samples, freq):
    """Divied the incoming samples data frame into chunks of duration _freq_."""
    grouping = samples.groupby([pd.Grouper(level="timestamp_s", freq=freq)])
    return dict(list(grouping))


def sliceby_month(samples):
    """Divied the incoming samples data frame into month-sized chunks."""
    return sliceby(samples, freq="MS")


def sliceby_day(samples):
    """Divied the incoming samples data frame into day-sized chunks."""
    return sliceby(samples, freq="D")


def sliceby_hour(samples):
    """Divied the incoming samples data frame into hour-sized chunks."""
    return sliceby(samples, freq="H")


def sliceby_weekday(samples):
    """
    Divide the incoming sample data according to the weekday they belong to.

    The weekdays are indexed from 0 to 6, with 0 = Sunday.
    """
    grouping = samples.groupby(samples.index.weekday)
    return dict(list(grouping))
