import numpy as np


SQRT_2 = np.sqrt(2.0)
COS_45 = 1.0 / SQRT_2
SIN_45 = 1.0 / SQRT_2


def calculate_parameters(source):
    """
    Рассчитывает параметр L цилиндрического источника.
    """

    d = source.diameter
    h = source.height

    if h is None:
        raise ValueError(
            f"Источник {source.index}: "
            "для CYLINDER требуется HEIGHT."
        )

    if d <= 0 or h <= 0:
        raise ValueError(
            f"Источник {source.index}: "
            "диаметр и высота должны быть > 0."
        )

    area_projection_45 = (
        (np.pi * d**2 / 4.0) * COS_45
        +
        d * h * SIN_45
    )

    if source.photometry == "INTENSITY":

        if source.intensity_45 is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для INTENSITY требуется INTENSITY_45."
            )

        source.L = (
            source.intensity_45
            / area_projection_45
        )

    elif source.photometry == "FLUX":

        if source.flux is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для FLUX требуется FLUX."
            )

        source.L = (
            source.flux
            /
            (
                np.pi**2
                *
                (d**2 / 2.0 + d * h)
            )
        )

    else:
        raise ValueError(
            f"Источник {source.index}: "
            f"неподдерживаемая фотометрия "
            f"{source.photometry}."
        )

    return source


def intensity(source, alpha):
    """
    Сила света цилиндрического источника:

    I(alpha) =
        L * [
            pi*d²/4 * |cos(alpha)|
            +
            d*h * sin(alpha)
        ]
    """

    alpha = np.asarray(alpha, dtype=float)

    d = source.diameter
    h = source.height

    cos_alpha = np.abs(np.cos(alpha))
    sin_alpha = np.sin(alpha)

    projected_area = (
        (np.pi * d**2 / 4.0) * cos_alpha
        +
        d * h * sin_alpha
    )

    return source.L * projected_area