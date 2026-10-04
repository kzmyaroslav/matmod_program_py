import numpy as np

from .geometry import (
    vectors_from_source,
    plane_normal,
    source_angle,
    incidence_cosine,
)

from photometry import (
    sphere,
    disk,
    cylinder,
    hemisphere,
)


EPS = 1e-12


def source_intensity(source, alpha):
    """
    Возвращает силу света источника I(alpha)
    для заданного угла alpha.
    """

    source_type = source.source_type.upper()

    if source_type == "SPHERE":
        return sphere.intensity(source, alpha)

    if source_type == "DISK":
        return disk.intensity(source, alpha)

    if source_type == "CYLINDER":
        return cylinder.intensity(source, alpha)

    if source_type == "HEMISPHERE":
        return hemisphere.hemisphere_intensity(
            source,
            alpha,
        )

    if source_type == "HALF_SPHERE":
        return hemisphere.half_sphere_intensity(
            source,
            alpha,
        )

    raise ValueError(
        f"Источник {source.index}: "
        f"неподдерживаемый тип {source_type}."
    )


def calculate_source(source, points, plane):
    """
    Рассчитывает освещённость от одного источника
    во всех точках.

    Формула:

        E = I(alpha) / r² * |cos(beta)|

    где:

        I(alpha) — сила света в направлении точки,
        r        — расстояние от источника,
        beta     — угол между лучом и нормалью плоскости.
    """

    _, distances, unit_vectors = vectors_from_source(
        source,
        points,
    )

    normal = plane_normal(plane)

    alpha = source_angle(
        source,
        unit_vectors,
    )

    intensity = source_intensity(
        source,
        alpha,
    )

    cos_beta = incidence_cosine(
        unit_vectors,
        normal,
    )

    illuminance = (
        intensity
        / distances**2
        * cos_beta
    )

    return illuminance


def calculate(grid, sources):
    """
    Рассчитывает освещённость от всех источников.

    Returns
    -------
    total : np.ndarray
        Суммарная освещённость.

    contributions : dict
        Вклад каждого источника.
        Например:

        {
            1: array(...),
            2: array(...),
        }
    """

    total = np.zeros(
        grid.points.shape[0],
        dtype=float,
    )

    contributions = {}

    for source in sources:

        contribution = calculate_source(
            source=source,
            points=grid.points,
            plane=grid.plane,
        )

        contributions[source.index] = (
            contribution.reshape(grid.shape)
        )

        total += contribution

    total = total.reshape(grid.shape)

    return total, contributions


def calculate_statistics(illuminance):
    """
    Рассчитывает основные статистические показатели.

    Returns
    -------
    dict
        Emin
        Emax
        Eavg
        Emin/Emax
        Eavg/Emax
    """

    illuminance = np.asarray(
        illuminance,
        dtype=float,
    )

    if illuminance.size == 0:
        raise ValueError(
            "Массив освещённости пуст."
        )

    if not np.all(np.isfinite(illuminance)):
        raise ValueError(
            "Массив освещённости содержит "
            "некорректные значения."
        )

    emin = float(np.min(illuminance))
    emax = float(np.max(illuminance))
    eavg = float(np.mean(illuminance))

    if abs(emax) <= EPS:
        emin_emax = 0.0
        eavg_emax = 0.0
    else:
        emin_emax = emin / emax
        eavg_emax = eavg / emax

    return {
        "Emin": emin,
        "Emax": emax,
        "Eavg": eavg,
        "Emin/Emax": emin_emax,
        "Eavg/Emax": eavg_emax,
    }