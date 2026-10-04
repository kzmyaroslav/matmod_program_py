from dataclasses import dataclass

import numpy as np


@dataclass
class GridConfig:
    """Параметры расчётной сетки."""

    step: float


@dataclass
class GridData:
    """
    Данные сформированной расчётной плоскости.

    values:
        координаты точек по первой оси.

    columns:
        координаты точек по второй оси.

    points:
        массив координат всех точек.
    """

    plane: str
    coordinate: float

    row_axis: np.ndarray
    column_axis: np.ndarray

    points: np.ndarray

    shape: tuple


def _axis_values(length: float, step: float) -> np.ndarray:
    """
    Создаёт координаты сетки от 0 до размера помещения.

    Последняя точка всегда не выходит за границы помещения.
    """

    if step <= 0:
        raise ValueError("Шаг сетки должен быть больше нуля.")

    values = np.arange(0.0, length + step * 0.001, step)

    # Защита от выхода за границу из-за погрешности float
    values = values[values <= length + 1e-9]

    # Если размер помещения не кратен шагу,
    # добавляем саму границу помещения.
    if len(values) == 0 or abs(values[-1] - length) > 1e-9:
        values = np.append(values, length)

    return values


def create_grid(
    room,
    grid_config: GridConfig,
    plane: str,
    coordinate: float
) -> GridData:
    """
    Создаёт расчётную сетку.

    plane:
        X -> плоскость YZ
        Y -> плоскость XZ
        Z -> плоскость XY

    coordinate:
        фиксированная координата расчётной плоскости.
    """

    plane = plane.upper().strip()

    if plane not in {"X", "Y", "Z"}:
        raise ValueError(
            "Плоскость должна быть X, Y или Z."
        )

    limits = {
        "X": room.x,
        "Y": room.y,
        "Z": room.z,
    }

    if coordinate < 0 or coordinate > limits[plane]:
        raise ValueError(
            f"Координата {coordinate} выходит "
            f"за границы помещения по оси {plane}."
        )

    if plane == "Z":
        # XY
        x = _axis_values(room.x, grid_config.step)
        y = _axis_values(room.y, grid_config.step)

        xx, yy = np.meshgrid(x, y)

        points = np.stack(
            [
                xx.ravel(),
                yy.ravel(),
                np.full(xx.size, coordinate),
            ],
            axis=1,
        )

        return GridData(
            plane="Z",
            coordinate=coordinate,
            row_axis=y,
            column_axis=x,
            points=points,
            shape=xx.shape,
        )

    if plane == "X":
        # YZ
        y = _axis_values(room.y, grid_config.step)
        z = _axis_values(room.z, grid_config.step)

        yy, zz = np.meshgrid(y, z)

        points = np.stack(
            [
                np.full(yy.size, coordinate),
                yy.ravel(),
                zz.ravel(),
            ],
            axis=1,
        )

        return GridData(
            plane="X",
            coordinate=coordinate,
            row_axis=z,
            column_axis=y,
            points=points,
            shape=yy.shape,
        )

    # plane == "Y"
    # XZ
    x = _axis_values(room.x, grid_config.step)
    z = _axis_values(room.z, grid_config.step)

    xx, zz = np.meshgrid(x, z)

    points = np.stack(
        [
            xx.ravel(),
            np.full(xx.size, coordinate),
            zz.ravel(),
        ],
        axis=1,
    )

    return GridData(
        plane="Y",
        coordinate=coordinate,
        row_axis=z,
        column_axis=x,
        points=points,
        shape=xx.shape,
    )