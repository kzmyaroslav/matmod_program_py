import numpy as np


def calculate_parameters(source):
    """
    Рассчитывает фотометрические параметры сферического источника.
    """

    if source.photometry == "INTENSITY":

        if source.intensity is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для INTENSITY требуется INTENSITY."
            )

        source.I0 = source.intensity

    elif source.photometry == "FLUX":

        if source.flux is None:
            raise ValueError(
                f"Источник {source.index}: "
                "для FLUX требуется FLUX."
            )

        source.I0 = source.flux / (4.0 * np.pi)

    else:
        raise ValueError(
            f"Источник {source.index}: "
            f"неподдерживаемый тип фотометрии "
            f"{source.photometry}."
        )

    return source


def intensity(source, alpha):
    """
    Сила света сферического источника.

    Для идеализированного сферического источника
    сила света одинакова во всех направлениях.
    """

    if source.I0 is None:
        raise ValueError(
            f"Для источника {source.index} "
            "не рассчитан I0."
        )

    return np.full_like(
        np.asarray(alpha, dtype=float),
        source.I0,
        dtype=float
    )