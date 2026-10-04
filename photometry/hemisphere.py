import numpy as np


COS_50 = np.cos(np.deg2rad(50.0))


def calculate_hemisphere_parameters(source):
    """
    Расчёт параметра L для HEMISPHERE.
    """

    d = source.diameter

    if d <= 0:
        raise ValueError(
            f"Источник {source.index}: "
            "диаметр должен быть > 0."
        )

    if source.surface not in {"INNER", "OUTER"}:
        raise ValueError(
            f"Источник {source.index}: "
            "SURFACE должен быть INNER или OUTER."
        )

    if source.photometry == "INTENSITY":

        if source.intensity_50 is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для INTENSITY требуется INTENSITY_50."
            )

        if source.surface == "INNER":

            source.L = (
                4.0 * source.intensity_50
                /
                (
                    np.pi
                    * d**2
                    * COS_50
                )
            )

        else:

            source.L = (
                8.0 * source.intensity_50
                /
                (
                    np.pi
                    * d**2
                    * (1.0 + COS_50)
                )
            )

    elif source.photometry == "FLUX":

        if source.flux is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для FLUX требуется FLUX."
            )

        if source.surface == "INNER":

            source.L = (
                4.0 * source.flux
                /
                (np.pi**2 * d**2)
            )

        else:

            source.L = (
                2.0 * source.flux
                /
                (np.pi**2 * d**2)
            )

    else:
        raise ValueError(
            f"Источник {source.index}: "
            f"неподдерживаемая фотометрия "
            f"{source.photometry}."
        )

    return source


def hemisphere_intensity(source, alpha):
    """
    Сила света HEMISPHERE.
    """

    alpha = np.asarray(alpha, dtype=float)

    d = source.diameter

    cos_alpha = np.cos(alpha)

    if source.surface == "INNER":

        result = (
            source.L
            *
            (np.pi * d**2 / 4.0)
            *
            np.maximum(cos_alpha, 0.0)
        )

        return result

    # OUTER
    return (
        source.L
        *
        (np.pi * d**2 / 8.0)
        *
        (1.0 + cos_alpha)
    )


def calculate_half_sphere_parameters(source):
    """
    Расчёт параметра L для HALF_SPHERE.

    HALF_SPHERE состоит из:
    - сферической поверхности;
    - плоской круглой основы.

    Ориентация не влияет на формулу силы света,
    поскольку используется abs(cos(alpha)).
    """

    d = source.diameter

    if d <= 0:
        raise ValueError(
            f"Источник {source.index}: "
            "диаметр должен быть > 0."
        )

    if source.photometry == "INTENSITY":

        if source.intensity_50 is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для INTENSITY требуется INTENSITY_50."
            )

        source.L = (
            8.0 * source.intensity_50
            /
            (
                np.pi
                * d**2
                * (1.0 + COS_50)
            )
        )

    elif source.photometry == "FLUX":

        if source.flux is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для FLUX требуется FLUX."
            )

        source.L = (
            4.0 * source.flux
            /
            (3.0 * np.pi**2 * d**2)
        )

    else:
        raise ValueError(
            f"Источник {source.index}: "
            f"неподдерживаемая фотометрия "
            f"{source.photometry}."
        )

    return source


def half_sphere_intensity(source, alpha):
    """
    Сила света HALF_SPHERE.
    """

    alpha = np.asarray(alpha, dtype=float)

    d = source.diameter

    return (
        source.L
        *
        (np.pi * d**2 / 8.0)
        *
        (1.0 + np.abs(np.cos(alpha)))
    )