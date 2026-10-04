import numpy as np


EPS = 1e-12


def vectors_from_source(source, points):
    """
    Вычисляет векторы от источника до всех точек расчётной сетки.

    Parameters
    ----------
    source : LightSource
        Источник света.

    points : np.ndarray
        Массив точек формы (N, 3).

    Returns
    -------
    R : np.ndarray
        Векторы от источника до точек, форма (N, 3).

    distances : np.ndarray
        Расстояния до точек, форма (N,).

    unit_vectors : np.ndarray
        Единичные векторы, форма (N, 3).
    """

    points = np.asarray(points, dtype=float)

    R = points - source.position

    distances = np.linalg.norm(R, axis=1)

    if np.any(distances <= EPS):
        point_index = np.where(distances <= EPS)[0][0]

        raise ValueError(
            f"Точка расчётной сетки №{point_index + 1} "
            f"совпадает с источником {source.index}. "
            f"Расчёт в этой точке невозможен."
        )

    unit_vectors = R / distances[:, None]

    return R, distances, unit_vectors


def plane_normal(plane):
    """
    Возвращает нормаль расчётной плоскости.

    X = const -> нормаль X
    Y = const -> нормаль Y
    Z = const -> нормаль Z
    """

    plane = plane.upper().strip()

    normals = {
        "X": np.array([1.0, 0.0, 0.0]),
        "Y": np.array([0.0, 1.0, 0.0]),
        "Z": np.array([0.0, 0.0, 1.0]),
    }

    if plane not in normals:
        raise ValueError(
            "Расчётная плоскость должна быть X, Y или Z."
        )

    return normals[plane]


def source_angle(source, unit_vectors):
    """
    Вычисляет угол между направлением на точку
    и направлением максимальной силы света источника.

    Результат — в радианах.
    """

    if source.direction is None:
        raise ValueError(
            f"Для источника {source.index} "
            f"не задано направление."
        )

    cos_alpha = unit_vectors @ source.direction

    cos_alpha = np.clip(
        cos_alpha,
        -1.0,
        1.0
    )

    return np.arccos(cos_alpha)


def incidence_cosine(unit_vectors, normal):
    """
    Косинус угла падения света на расчётную плоскость.

    Используется абсолютное значение, поскольку расчётная
    плоскость считается двусторонней.
    """

    cos_beta = unit_vectors @ normal

    cos_beta = np.clip(
        cos_beta,
        -1.0,
        1.0
    )

    return np.abs(cos_beta)