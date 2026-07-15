"""Small dependency-free numerical helpers for portfolio analytics."""

from __future__ import annotations

from math import sqrt
from statistics import fmean


def mean_vector(rows: list[list[float]]) -> list[float]:
    return [fmean(column) for column in zip(*rows, strict=True)]


def covariance_matrix(rows: list[list[float]]) -> list[list[float]]:
    if len(rows) < 2:
        raise ValueError("at least two return observations are required")
    means = mean_vector(rows)
    columns = list(zip(*rows, strict=True))
    size = len(columns)
    return [
        [
            sum(
                (x - means[i]) * (y - means[j]) for x, y in zip(columns[i], columns[j], strict=True)
            )
            / (len(rows) - 1)
            for j in range(size)
        ]
        for i in range(size)
    ]


def correlation_matrix(covariance: list[list[float]]) -> list[list[float]]:
    vol = [sqrt(max(covariance[i][i], 0.0)) for i in range(len(covariance))]
    return [
        [
            covariance[i][j] / (vol[i] * vol[j]) if vol[i] and vol[j] else 0.0
            for j in range(len(covariance))
        ]
        for i in range(len(covariance))
    ]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [
        sum(value * weight for value, weight in zip(row, vector, strict=True)) for row in matrix
    ]


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def portfolio_variance(weights: list[float], covariance: list[list[float]]) -> float:
    return dot(weights, matvec(covariance, weights))


def project_weights(weights: list[float], minimum: float, maximum: float) -> list[float]:
    clipped = [min(max(value, minimum), maximum) for value in weights]
    for _ in range(20):
        total = sum(clipped)
        if abs(total - 1.0) < 1e-10:
            break
        free = [i for i, value in enumerate(clipped) if minimum < value < maximum]
        if not free:
            clipped = [value / total for value in clipped]
            break
        adjustment = (1.0 - total) / len(free)
        for index in free:
            clipped[index] = min(max(clipped[index] + adjustment, minimum), maximum)
    total = sum(clipped)
    return [value / total for value in clipped]
