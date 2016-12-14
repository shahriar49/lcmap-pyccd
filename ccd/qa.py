"""Filters for pre-processing change model inputs.

# TODO finish fixing this
This module currently uses explicit values from the Landsat CFMask:

    - 0: clear
    - 1: water
    - 2: cloud_shadow
    - 3: snow
    - 4: cloud
    - 255: fill
"""
import numpy as np

from ccd.app import defaults


def mask_snow(quality, snow=defaults.QA_SNOW):
    """
    Filter all indices that are not snow

    Args:
        quality: 1-d ndarray of values representing the quality of the
            associated spectral observations
        snow: int value that denotes snow

    Returns:
        1-d boolean ndarray showing which values are snow
    """
    return quality == snow


def mask_clear(quality, clear=defaults.QA_CLEAR):
    """
    Filter all indices that are not clear

    Args:
        quality: 1-d ndarray of values representing the quality of the
            associated spectral observations
        clear: int value that denotes clear

    Returns:
        1-d boolean ndarray showing which values are clear
    """
    return quality == clear


def mask_water(quality, water=defaults.QA_WATER):
    """
    Filter all indices that are not water

    Args:
        quality: 1-d ndarray of values representing the quality of the
            associated spectral observations
        water: int value that denotes water

    Returns:
        1-d boolean ndarray showing which values are water
    """
    return quality == water


def mask_fill(quality, fill=defaults.QA_FILL):
    """
    Filter all indices that are not fill

    Args:
        quality: 1-d ndarray of values representing the quality of the
            associated spectral observations
        fill: int value that denotes fill

    Returns:
        1-d boolean ndarray showing which values are fill
    """
    return quality == fill


def mask_clear_or_water(quality):
    """
    Filter all indices that are not fill

    Args:
        quality: 1-d ndarray of values representing the quality of the
            associated spectral observations
        fill: int value that denotes fill

    Returns:
        1-d boolean ndarray showing which values are fill
    """
    return mask_clear(quality) | mask_water(quality)


def count_clear_or_water(quality):
    """Count clear or water data.

    Arguments:
        quality: quality band values.

    Returns:
        integer: number of clear or water observation implied by QA data.
    """
    return np.sum([mask_clear(quality), mask_water(quality)])


def count_fill(quality):
    """Count fill data.

    Arguments:
        quality: quality band values.

    Returns:
        integer: number of filled observation implied by QA data.
    """
    return np.sum(mask_fill(quality))


def count_snow(quality):
    """Count snow data.

    Useful for determining ratio of snow:clear pixels.

    Arguments:
        quality: quality band values.

    Returns:
        integer: number of snow pixels implied by QA data
    """
    return np.sum(mask_snow(quality))


def count_total(quality):
    """Count non-fill data.

    Useful for determining ratio of clear:total pixels.

    Arguments:
        quality: quality band values.

    Returns:
        integer: number of non-fill pixels implied by QA data.
    """
    return np.sum(~mask_fill(quality))


def ratio_clear(quality):
    """Calculate ratio of clear to non-clear pixels; exclude, fill data.

    Useful for determining ratio of clear:total pixels.

    Arguments:
        quality: quality band values.

    Returns:
        integer: number of non-fill pixels implied by QA data.
    """
    return count_clear_or_water(quality) / count_total(quality)


def ratio_snow(quality):
    """Calculate ratio of snow to clear pixels; exclude fill and non-clear data.

    Useful for determining ratio of snow:clear pixels.

    Arguments:
        quality: CFMask quality band values.

    Returns:
        float: Value between zero and one indicating amount of
            snow-observations.
    """
    snowy_count = count_snow(quality)
    clear_count = count_clear_or_water(quality)
    return count_snow(quality) / (clear_count + snowy_count + 0.01)


def enough_clear(quality, threshold=defaults.CLEAR_PCT_THREHOLD):
    """Determine if clear observations exceed threshold.

    Useful when selecting mathematical model for detection. More clear
    observations allow for models with more coefficients.

    Arguments:
        quality: quality band values.
        threshold: minimum ratio of clear/water to not-clear/water values.

    Returns:
        boolean: True if >= threshold
    """
    return ratio_clear(quality) >= threshold


def enough_snow(quality, threshold=defaults.SNOW_PCT_THRESHOLD):
    """Determine if snow observations exceed threshold.

    Useful when selecting detection algorithm.

    Arguments:
        quality: quality band values.
        threshold: minimum ratio of snow to clear/water values.

    Returns:
        boolean: True if >= threshold
    """
    return ratio_snow(quality) >= threshold


def filter_saturated(observations):
    """bool index for unsaturated obserervations between 0..10,000

    Useful for efficiently filtering noisy-data from arrays.

    Arguments:
        observations: time/spectra/qa major nd-array, assumed to be shaped as
            (9,n-moments) of unscaled data.

    """
    unsaturated = ((0 < observations[1, :]) & (observations[1, :] < 10000) &
                   (0 < observations[2, :]) & (observations[2, :] < 10000) &
                   (0 < observations[3, :]) & (observations[3, :] < 10000) &
                   (0 < observations[4, :]) & (observations[4, :] < 10000) &
                   (0 < observations[5, :]) & (observations[5, :] < 10000) &
                   (0 < observations[0, :]) & (observations[0, :] < 10000))
    return unsaturated


def filter_thermal(thermal, min_kelvin=179.95, max_kelvin=343.85):
    """Provide an index of observations within a brightness temperature range.

    Thermal min/max must be provided as an unscaled value in Kelvin, the same
    units as observed data.

    The range in degrees celsius is [-93.2C,70.7C]

    Arguments:
        thermal: 1-d array of thermal values
        min_kelvin: minimum temperature in degrees kelvin, by default 179.95K,
            -93.2C.
        max_kelvin: maximum temperature in degrees kelvin, by default 3438.5K,
            70.7C.
    """
    # threshold parameters are unscaled, observations are scaled so the former
    # needs to be scaled...
    min_kelvin *= 10
    max_kelvin *= 10
    return ((thermal > min_kelvin) &
            (thermal < max_kelvin))


def clear_index(quality, clear=defaults.QA_CLEAR, water=defaults.QA_WATER):
    """
    Return the array indices that are considered clear or water

    Args:
        quality:
        clear:
        water:

    Returns:
        ndarray: bool
    """
    return (quality == clear) & (quality == water)


def standard_filter(observations, quality, thermal_idx=defaults.THERMAL_IDX):
    """Filter matrix for clear pixels within temp/saturation range.

    Temperatures are expected to be in celsius
    """
    indices = (clear_index(quality)
               & filter_thermal(observations[thermal_idx])
               & filter_saturated(observations))
    return indices
