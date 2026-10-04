from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class LightSource:
    """
    Модель источника света.

    Все координаты и геометрические размеры — в метрах.

    direction:
        направление максимальной силы света.

    I0:
        нормированная сила света / параметр источника,
        рассчитывается после чтения конфигурации.

    L:
        яркость элементарной поверхности/линейного распределения
        для протяжённых моделей.
    """

    index: int

    source_type: str

    position: np.ndarray

    diameter: float

    photometry: str

    orientation: Optional[str] = None
    side: Optional[str] = None
    surface: Optional[str] = None

    height: Optional[float] = None

    flux: Optional[float] = None
    intensity: Optional[float] = None
    intensity_45: Optional[float] = None
    intensity_50: Optional[float] = None

    direction: Optional[np.ndarray] = None

    I0: Optional[float] = None
    L: Optional[float] = None

    @property
    def x(self):
        return float(self.position[0])

    @property
    def y(self):
        return float(self.position[1])

    @property
    def z(self):
        return float(self.position[2])

    @property
    def radius(self):
        return self.diameter / 2.0

    def __post_init__(self):
        self.source_type = self.source_type.upper()
        self.photometry = self.photometry.upper()

        if self.orientation:
            self.orientation = self.orientation.upper()

        if self.side:
            self.side = self.side.upper()

        if self.surface:
            self.surface = self.surface.upper()

        self.position = np.asarray(
            self.position,
            dtype=float
        )

        if self.direction is not None:
            self.direction = np.asarray(
                self.direction,
                dtype=float
            )

            norm = np.linalg.norm(self.direction)

            if norm > 0:
                self.direction = self.direction / norm

    def parameter_dict(self):
        """
        Возвращает параметры источника в удобном для Excel виде.
        """

        data = {
            "Номер": self.index,
            "Тип": self.source_type,
            "X, м": self.x,
            "Y, м": self.y,
            "Z, м": self.z,
            "Диаметр, м": self.diameter,
            "Фотометрия": self.photometry,
        }

        if self.height is not None:
            data["Высота, м"] = self.height

        if self.side is not None:
            data["Сторона"] = self.side

        if self.surface is not None:
            data["Поверхность"] = self.surface

        if self.orientation is not None:
            data["Ориентация"] = self.orientation

        if self.flux is not None:
            data["Световой поток, лм"] = self.flux

        if self.intensity is not None:
            data["Сила света, кд"] = self.intensity

        if self.intensity_45 is not None:
            data["I(45°), кд"] = self.intensity_45

        if self.intensity_50 is not None:
            data["I(50°), кд"] = self.intensity_50

        if self.I0 is not None:
            data["I0"] = self.I0

        if self.L is not None:
            data["L"] = self.L

        return data