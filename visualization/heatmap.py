import numpy as np
import matplotlib.pyplot as plt


def create_heatmap(
    grid,
    illuminance,
    output_path,
    decimal_places=2,
):
    """
    Создаёт карту распределения освещённости.

    Parameters
    ----------
    grid : GridData
        Расчётная сетка.

    illuminance : np.ndarray
        Массив освещённости формы grid.shape.

    output_path : str
        Путь сохранения изображения.

    decimal_places : int
        Количество знаков после запятой.
    """

    illuminance = np.asarray(
        illuminance,
        dtype=float,
    )

    if illuminance.shape != grid.shape:
        raise ValueError(
            "Размер массива освещённости "
            "не соответствует размеру сетки."
        )

    fig, ax = plt.subplots(
        figsize=(10, 7)
    )

    image = ax.imshow(
        illuminance,
        origin="lower",
        aspect="auto",
        extent=[
            grid.column_axis[0],
            grid.column_axis[-1],
            grid.row_axis[0],
            grid.row_axis[-1],
        ],
        cmap="turbo",
    )

    colorbar = fig.colorbar(
        image,
        ax=ax,
    )

    colorbar.set_label(
        "Освещённость, лк"
    )

    # Подписи осей
    axis_labels = {
        "X": ("Y, м", "Z, м"),
        "Y": ("X, м", "Z, м"),
        "Z": ("X, м", "Y, м"),
    }

    xlabel, ylabel = axis_labels[grid.plane]

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_title(
        f"Карта освещённости: "
        f"{grid.plane} = {grid.coordinate:.{decimal_places}f} м"
    )

    # Показываем значения в узлах сетки,
    # если количество точек не слишком большое.
    rows, cols = illuminance.shape

    if rows * cols <= 400:
        for i in range(rows):
            for j in range(cols):
                value = illuminance[i, j]

                ax.text(
                    grid.column_axis[j],
                    grid.row_axis[i],
                    f"{value:.{decimal_places}f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)