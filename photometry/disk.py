import numpy as np


def calculate_parameters(source):
    """
    Рассчитывает I0 для плоского дискового источника.
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

        # Для ламбертовского диска:
        # Phi = pi * I0
        source.I0 = source.flux / np.pi

    else:
        raise ValueError(
            f"Источник {source.index}: "
            f"неподдерживаемая фотометрия "
            f"{source.photometry}."
        )

    return source


def intensity(source, alpha):
    """
    Ламбертовский закон для диска:

        I(alpha) = I0 * cos(alpha)

    при alpha <= 90°.

    За обратной полусферой источник не излучает.
    """

    alpha = np.asarray(alpha, dtype=float)

    cos_alpha = np.cos(alpha)

    result = source.I0 * np.maximum(cos_alpha, 0.0)

    return result