from sklearn import linear_model, metrics
import numpy as np
from cachetools import cached, LRUCache

from ccd.models import FittedModel
from ccd.math_utils import calc_rmse
from ccd.app import defaults

cache = LRUCache(maxsize=1000)


def __coefficient_cache_key(observation_dates):
    return tuple(observation_dates)


@cached(cache=cache, key=__coefficient_cache_key)
def coefficient_matrix(observation_dates, num_coeffs=4,
                       avg_days_yr=defaults.AVG_DAYS_YR):
    """
    Args:
        observation_dates: list of ordinal dates
        num_coeffs: how many coefficients to use to build the matrix

    Returns:
        Populated numpy array with coefficient values
    """
    w = 2 * np.pi / avg_days_yr

    matrix = np.zeros(shape=(len(observation_dates), 8), order='F')

    matrix[:, 0] = [t for t in observation_dates]
    matrix[:, 1] = [np.cos(w*t) for t in observation_dates]
    matrix[:, 2] = [np.sin(w*t) for t in observation_dates]

    if num_coeffs == 6:
        matrix[:, 3] = [np.cos(2 * w * t) for t in observation_dates]
        matrix[:, 4] = [np.sin(2 * w * t) for t in observation_dates]

    if num_coeffs == 8:
        matrix[:, 5] = [np.cos(3 * w * t) for t in observation_dates]
        matrix[:, 6] = [np.sin(3 * w * t) for t in observation_dates]

    return matrix


def fitted_model(dates, observations, df=4):
    """Create a fully fitted lasso model.

    Args:
        dates: list or ordinal observation dates
        observations: list of values corresponding to observation_dates
        df: degrees of freedom, how many coefficients to use

    Returns:
        sklearn.linear_model.Lasso().fit(observation_dates, observations)

    Example:
        fitted_model(dates, obs).predict(...)
    """
    coef_matrix = coefficient_matrix(dates, df)

    # pmodel = partial_model(observation_dates)
    lasso = linear_model.Lasso(alpha=0.1)
    model = lasso.fit(coef_matrix, observations)

    predictions = model.predict(coefficient_matrix)
    rmse, residuals = calc_rmse(observations, predictions)

    return FittedModel(model=model, rmse=rmse, residual=residuals)
