from dataclasses import dataclass


@dataclass
class Room:
    """
    Габариты помещения.

    Все размеры хранятся в метрах.
    Начало координат помещения: (0, 0, 0).
    """

    x: float
    y: float
    z: float

    @property
    def dimensions(self):
        return self.x, self.y, self.z

    def contains_point(self, point) -> bool:
        """
        Проверяет, находится ли точка внутри помещения.
        """

        px, py, pz = point

        return (
            0.0 <= px <= self.x
            and
            0.0 <= py <= self.y
            and
            0.0 <= pz <= self.z
        )