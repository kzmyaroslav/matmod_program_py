from pathlib import Path

from config.parser import load_configuration
from models.grid import create_grid
from calculation.illuminance import (
    calculate,
    calculate_statistics,
)
from visualization.heatmap import create_heatmap
from visualization.room_3d import create_room_3d
from output.excel import export_to_excel


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "input.txt"
RESULTS_DIR = BASE_DIR / "results"


def print_header():
    print()
    print("=" * 60)
    print("       ПРОГРАММА РАСЧЁТА ОСВЕЩЁННОСТИ")
    print("=" * 60)
    print()


def choose_plane(room):
    """
    Запрашивает у пользователя расчётную плоскость
    и координату этой плоскости.
    """

    print("Выберите расчётную плоскость:")
    print()
    print("  X — плоскость X = const (YZ)")
    print("  Y — плоскость Y = const (XZ)")
    print("  Z — плоскость Z = const (XY)")
    print()

    while True:

        plane = input(
            "Плоскость [X/Y/Z]: "
        ).strip().upper()

        if plane not in {"X", "Y", "Z"}:
            print(
                "Ошибка: необходимо выбрать X, Y или Z."
            )
            continue

        limits = {
            "X": room.x,
            "Y": room.y,
            "Z": room.z,
        }

        print(
            f"Допустимый диапазон координаты: "
            f"0 ... {limits[plane]:g} м"
        )

        while True:

            value = input(
                f"Введите координату {plane}, м: "
            ).strip()

            try:
                coordinate = float(value)
            except ValueError:
                print(
                    "Ошибка: необходимо ввести число."
                )
                continue

            if not 0.0 <= coordinate <= limits[plane]:
                print(
                    f"Ошибка: координата должна быть "
                    f"от 0 до {limits[plane]:g} м."
                )
                continue

            return plane, coordinate


def print_sources(sources):
    """Выводит краткую информацию об источниках."""

    print()
    print("Источники:")

    for source in sources:

        print(
            f"  S{source.index}: "
            f"{source.source_type}, "
            f"позиция "
            f"({source.x:g}, "
            f"{source.y:g}, "
            f"{source.z:g}) м"
        )

    print()


def print_statistics(statistics):
    """Выводит результаты расчёта."""

    print()
    print("-" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("-" * 60)

    print(
        f"Emin   = {statistics['Emin']:.2f} лк"
    )

    print(
        f"Emax   = {statistics['Emax']:.2f} лк"
    )

    print(
        f"Eavg   = {statistics['Eavg']:.2f} лк"
    )

    print(
        f"Emin/Emax = "
        f"{statistics['Emin/Emax']:.4f}"
    )

    print(
        f"Eavg/Emax = "
        f"{statistics['Eavg/Emax']:.4f}"
    )

    print("-" * 60)
    print()


def main():

    print_header()

    # -------------------------------------------------
    # 1. Загрузка конфигурации
    # -------------------------------------------------

    print("Загрузка конфигурации...")

    try:
        (
            room,
            grid_config,
            sources,
            calculation_config,
        ) = load_configuration(
            INPUT_FILE
        )

    except Exception as error:

        print()
        print("ОШИБКА КОНФИГУРАЦИИ:")
        print(error)
        print()

        return 1

    print("Конфигурация успешно загружена.")

    print()
    print(
        f"Размер помещения: "
        f"{room.x:g} × "
        f"{room.y:g} × "
        f"{room.z:g} м"
    )

    print(
        f"Шаг сетки: "
        f"{grid_config.step:g} м"
    )

    print(
        f"Количество источников: "
        f"{len(sources)}"
    )

    print_sources(sources)

    # -------------------------------------------------
    # 2. Выбор расчётной плоскости
    # -------------------------------------------------

    plane, coordinate = choose_plane(room)

    print()
    print(
        f"Расчётная плоскость: "
        f"{plane} = {coordinate:g} м"
    )

    # -------------------------------------------------
    # 3. Создание расчётной сетки
    # -------------------------------------------------

    print()
    print("Создание расчётной сетки...")

    try:

        grid = create_grid(
            room=room,
            grid_config=grid_config,
            plane=plane,
            coordinate=coordinate,
        )

    except Exception as error:

        print()
        print("ОШИБКА СОЗДАНИЯ СЕТКИ:")
        print(error)
        print()

        return 1

    print(
        f"Размер сетки: "
        f"{grid.shape[1]} × "
        f"{grid.shape[0]}"
    )

    print(
        f"Количество расчётных точек: "
        f"{len(grid.points)}"
    )

    # -------------------------------------------------
    # 4. Расчёт освещённости
    # -------------------------------------------------

    print()
    print("Расчёт освещённости...")

    try:

        illuminance, contributions = calculate(
            grid=grid,
            sources=sources,
        )

    except Exception as error:

        print()
        print("ОШИБКА РАСЧЁТА:")
        print(error)
        print()

        return 1

    print("Расчёт завершён.")

    # -------------------------------------------------
    # 5. Статистика
    # -------------------------------------------------

    statistics = calculate_statistics(
        illuminance
    )

    print_statistics(
        statistics
    )

    # -------------------------------------------------
    # 6. Создание папки результатов
    # -------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    excel_path = (
        RESULTS_DIR /
        "calculation.xlsx"
    )

    heatmap_path = (
        RESULTS_DIR /
        "illuminance_map.png"
    )

    room_path = (
        RESULTS_DIR /
        "room_3d.png"
    )

    # -------------------------------------------------
    # 7. Excel
    # -------------------------------------------------

    print("Создание Excel-файла...")

    try:

        export_to_excel(
            output_path=excel_path,
            room=room,
            grid_config=grid_config,
            grid=grid,
            sources=sources,
            illuminance=illuminance,
            contributions=contributions,
            statistics=statistics,
            calculation_config=calculation_config,
        )

    except Exception as error:

        print()
        print("ОШИБКА СОЗДАНИЯ EXCEL:")
        print(error)
        print()

        return 1

    print(
        f"Excel сохранён: "
        f"{excel_path}"
    )

    # -------------------------------------------------
    # 8. Карта освещённости
    # -------------------------------------------------

    print("Создание карты освещённости...")

    try:

        create_heatmap(
            grid=grid,
            illuminance=illuminance,
            output_path=heatmap_path,
            decimal_places=(
                calculation_config.decimal_places
            ),
        )

    except Exception as error:

        print()
        print("ОШИБКА СОЗДАНИЯ КАРТЫ:")
        print(error)
        print()

        return 1

    print(
        f"Карта сохранена: "
        f"{heatmap_path}"
    )

    # -------------------------------------------------
    # 9. 3D-визуализация помещения
    # -------------------------------------------------

    print("Создание 3D-визуализации...")

    try:

        create_room_3d(
            room=room,
            grid=grid,
            sources=sources,
            output_path=room_path,
        )

    except Exception as error:

        print()
        print(
            "ОШИБКА СОЗДАНИЯ 3D-ВИЗУАЛИЗАЦИИ:"
        )
        print(error)
        print()

        return 1

    print(
        f"3D-визуализация сохранена: "
        f"{room_path}"
    )

    # -------------------------------------------------
    # 10. Завершение
    # -------------------------------------------------

    print()
    print("=" * 60)
    print("РАСЧЁТ УСПЕШНО ЗАВЕРШЁН")
    print("=" * 60)

    print()
    print("Файлы результатов:")

    print(
        f"  Excel: "
        f"{excel_path}"
    )

    print(
        f"  Карта: "
        f"{heatmap_path}"
    )

    print(
        f"  3D:    "
        f"{room_path}"
    )

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )