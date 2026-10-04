import numpy as np
import matplotlib.pyplot as plt


def _draw_box(ax, room):
    """
    Рисует каркас помещения.
    """

    x = [0, room.x]
    y = [0, room.y]
    z = [0, room.z]

    vertices = np.array([
        [x[0], y[0], z[0]],
        [x[1], y[0], z[0]],
        [x[1], y[1], z[0]],
        [x[0], y[1], z[0]],

        [x[0], y[0], z[1]],
        [x[1], y[0], z[1]],
        [x[1], y[1], z[1]],
        [x[0], y[1], z[1]],
    ])

    edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),

        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),

        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]

    for start, end in edges:
        ax.plot3D(
            [vertices[start, 0], vertices[end, 0]],
            [vertices[start, 1], vertices[end, 1]],
            [vertices[start, 2], vertices[end, 2]],
        )


def _draw_calculation_plane(ax, room, grid):
    """
    Рисует расчётную плоскость.
    """

    if grid.plane == "Z":

        x, y = np.meshgrid(
            [0, room.x],
            [0, room.y],
        )

        z = np.full_like(
            x,
            grid.coordinate,
            dtype=float,
        )

        ax.plot_surface(
            x,
            y,
            z,
            alpha=0.15,
        )

    elif grid.plane == "X":

        y, z = np.meshgrid(
            [0, room.y],
            [0, room.z],
        )

        x = np.full_like(
            y,
            grid.coordinate,
            dtype=float,
        )

        ax.plot_surface(
            x,
            y,
            z,
            alpha=0.15,
        )

    elif grid.plane == "Y":

        x, z = np.meshgrid(
            [0, room.x],
            [0, room.z],
        )

        y = np.full_like(
            x,
            grid.coordinate,
            dtype=float,
        )

        ax.plot_surface(
            x,
            y,
            z,
            alpha=0.15,
        )


def create_room_3d(
    room,
    grid,
    sources,
    output_path,
):
    """
    Создаёт 3D-визуализацию помещения.

    Показывает:
    - помещение;
    - источники;
    - расчётную плоскость.
    """

    fig = plt.figure(
        figsize=(10, 8)
    )

    ax = fig.add_subplot(
        111,
        projection="3d",
    )

    # Помещение
    _draw_box(
        ax,
        room,
    )

    # Расчётная плоскость
    _draw_calculation_plane(
        ax,
        room,
        grid,
    )

    # Источники
    for source in sources:

        ax.scatter(
            source.x,
            source.y,
            source.z,
            s=80,
        )

        ax.text(
            source.x,
            source.y,
            source.z,
            f"  S{source.index}",
        )

    # Оси
    ax.set_xlabel("X, м")
    ax.set_ylabel("Y, м")
    ax.set_zlabel("Z, м")

    ax.set_xlim(
        0,
        room.x,
    )

    ax.set_ylim(
        0,
        room.y,
    )

    ax.set_zlim(
        0,
        room.z,
    )

    ax.set_title(
        f"Помещение и расчётная плоскость "
        f"({grid.plane} = {grid.coordinate:g} м)"
    )

    # Стараемся сохранить пропорции помещения
    try:
        ax.set_box_aspect(
            (
                room.x,
                room.y,
                room.z,
            )
        )
    except AttributeError:
        pass

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)