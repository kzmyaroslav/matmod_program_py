from configparser import ConfigParser
from pathlib import Path

import numpy as np

from models.room import Room
from models.grid import GridConfig
from models.sources import LightSource

from photometry import sphere
from photometry import disk
from photometry import cylinder
from photometry import hemisphere


class CalculationConfig:
    """
    Дополнительные настройки расчёта.
    """

    def __init__(
        self,
        debug: bool = False,
        decimal_places: int = 2,
    ):
        self.debug = debug
        self.decimal_places = decimal_places


def _read_config(path: str | Path) -> ConfigParser:
    """
    Читает конфигурационный файл.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Файл конфигурации не найден:\n{path}"
        )

    parser = ConfigParser(
        interpolation=None,
        comment_prefixes=("#", ";"),
        inline_comment_prefixes=("#", ";"),
    )

    # Сохраняем регистр имён параметров.
    # Но ниже сами параметры будем приводить к upper-case.
    parser.optionxform = str

    try:
        with path.open("r", encoding="utf-8") as file:
            parser.read_file(file)
    except Exception as exc:
        raise ValueError(
            f"Ошибка чтения файла конфигурации: {exc}"
        ) from exc

    return parser


def _get_required(
    section,
    key: str,
    section_name: str,
) -> str:
    """
    Получает обязательный параметр.
    """

    if key not in section:
        raise ValueError(
            f"В секции [{section_name}] "
            f"отсутствует обязательный параметр {key}."
        )

    value = section[key].strip()

    if not value:
        raise ValueError(
            f"Параметр {key} в секции "
            f"[{section_name}] не может быть пустым."
        )

    return value


def _get_float(
    section,
    key: str,
    section_name: str,
) -> float:
    """
    Получает обязательный параметр типа float.
    """

    value = _get_required(
        section,
        key,
        section_name,
    )

    try:
        return float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(
            f"Параметр {key} в секции "
            f"[{section_name}] должен быть числом. "
            f"Получено: {value}"
        ) from exc


def _get_optional_float(
    section,
    key: str,
):
    """
    Получает необязательный float.
    """

    if key not in section:
        return None

    value = section[key].strip()

    if not value:
        return None

    try:
        return float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(
            f"Параметр {key} должен быть числом. "
            f"Получено: {value}"
        ) from exc


def _get_int(
    section,
    key: str,
    section_name: str,
) -> int:
    """
    Получает обязательный параметр типа int.
    """

    value = _get_required(
        section,
        key,
        section_name,
    )

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Параметр {key} в секции "
            f"[{section_name}] должен быть целым числом. "
            f"Получено: {value}"
        ) from exc


def _get_optional(
    section,
    key: str,
    default=None,
):
    """
    Получает необязательный строковый параметр.
    """

    if key not in section:
        return default

    value = section[key].strip()

    if not value:
        return default

    return value


def _parse_room(parser: ConfigParser) -> Room:
    """
    Читает секцию [ROOM].
    """

    if "ROOM" not in parser:
        raise ValueError(
            "В файле отсутствует секция [ROOM]."
        )

    section = parser["ROOM"]

    unit = _get_optional(
        section,
        "UNIT",
        "M",
    ).upper()

    x = _get_float(section, "X", "ROOM")
    y = _get_float(section, "Y", "ROOM")
    z = _get_float(section, "Z", "ROOM")

    if x <= 0 or y <= 0 or z <= 0:
        raise ValueError(
            "Размеры помещения должны быть больше нуля."
        )

    if unit == "MM":
        x /= 1000.0
        y /= 1000.0
        z /= 1000.0

    elif unit == "CM":
        x /= 100.0
        y /= 100.0
        z /= 100.0

    elif unit != "M":
        raise ValueError(
            f"Неподдерживаемая единица ROOM.UNIT: {unit}. "
            "Используйте M, CM или MM."
        )

    return Room(
        x=x,
        y=y,
        z=z,
    )


def _parse_grid(parser: ConfigParser) -> GridConfig:
    """
    Читает секцию [GRID].
    """

    if "GRID" not in parser:
        raise ValueError(
            "В файле отсутствует секция [GRID]."
        )

    section = parser["GRID"]

    step = _get_float(
        section,
        "STEP",
        "GRID",
    )

    if step <= 0:
        raise ValueError(
            "GRID.STEP должен быть больше нуля."
        )

    return GridConfig(step=step)


def _parse_calculation(
    parser: ConfigParser,
) -> CalculationConfig:
    """
    Читает секцию [CALCULATION].
    """

    if "CALCULATION" not in parser:
        return CalculationConfig()

    section = parser["CALCULATION"]

    debug_value = _get_optional(
        section,
        "DEBUG",
        "FALSE",
    ).upper()

    if debug_value in {"TRUE", "1", "YES"}:
        debug = True
    elif debug_value in {"FALSE", "0", "NO"}:
        debug = False
    else:
        raise ValueError(
            "CALCULATION.DEBUG должен быть "
            "TRUE или FALSE."
        )

    decimal_places = _get_int(
        section,
        "DECIMAL_PLACES",
        "CALCULATION",
    )

    if decimal_places < 0:
        raise ValueError(
            "CALCULATION.DECIMAL_PLACES "
            "не может быть отрицательным."
        )

    return CalculationConfig(
        debug=debug,
        decimal_places=decimal_places,
    )


def _get_source_direction(
    source_type: str,
    orientation: str | None,
    side: str | None,
    surface: str | None,
):
    """
    Определяет направление максимальной силы света.
    """

    source_type = source_type.upper()

    if source_type == "SPHERE":
        return np.array([0.0, 0.0, 1.0])

    if source_type == "CYLINDER":
        return np.array([0.0, 0.0, 1.0])

    if source_type == "DISK":

        if side == "UP":
            return np.array([0.0, 0.0, 1.0])

        if side == "DOWN":
            return np.array([0.0, 0.0, -1.0])

        raise ValueError(
            "Для DISK параметр SIDE должен быть "
            "UP или DOWN."
        )

    if source_type in {"HEMISPHERE", "HALF_SPHERE"}:

        if orientation not in {"UP", "DOWN"}:
            raise ValueError(
                f"Для {source_type} параметр "
                "ORIENTATION должен быть UP или DOWN."
            )

        if orientation == "UP":
            convex = np.array([0.0, 0.0, 1.0])
        else:
            convex = np.array([0.0, 0.0, -1.0])

        if source_type == "HALF_SPHERE":
            return convex

        if surface == "INNER":
            return -convex

        if surface == "OUTER":
            return convex

        raise ValueError(
            "Для HEMISPHERE параметр SURFACE "
            "должен быть INNER или OUTER."
        )

    raise ValueError(
        f"Неизвестный тип источника: {source_type}"
    )


def _parse_source(
    parser: ConfigParser,
    index: int,
    room: Room,
) -> LightSource:
    """
    Читает одну секцию SOURCE_N.
    """

    section_name = f"SOURCE_{index}"

    if section_name not in parser:
        raise ValueError(
            f"В файле отсутствует секция "
            f"[{section_name}]."
        )

    section = parser[section_name]

    source_type = _get_required(
        section,
        "TYPE",
        section_name,
    ).upper()

    allowed_types = {
        "SPHERE",
        "DISK",
        "CYLINDER",
        "HEMISPHERE",
        "HALF_SPHERE",
    }

    if source_type not in allowed_types:
        raise ValueError(
            f"{section_name}: неизвестный TYPE "
            f"{source_type}."
        )

    x = _get_float(section, "X", section_name)
    y = _get_float(section, "Y", section_name)
    z = _get_float(section, "Z", section_name)

    position = np.array(
        [x, y, z],
        dtype=float,
    )

    if not room.contains_point(position):
        raise ValueError(
            f"{section_name}: источник находится "
            f"за пределами помещения: "
            f"({x}, {y}, {z})."
        )

    diameter = _get_float(
        section,
        "DIAMETER",
        section_name,
    )

    if diameter <= 0:
        raise ValueError(
            f"{section_name}: DIAMETER должен быть > 0."
        )

    photometry = _get_required(
        section,
        "PHOTOMETRY",
        section_name,
    ).upper()

    allowed_photometry = {
        "INTENSITY",
        "FLUX",
    }

    if photometry not in allowed_photometry:
        raise ValueError(
            f"{section_name}: PHOTOMETRY должен быть "
            f"INTENSITY или FLUX."
        )

    orientation = _get_optional(
        section,
        "ORIENTATION",
    )

    side = _get_optional(
        section,
        "SIDE",
    )

    surface = _get_optional(
        section,
        "SURFACE",
    )

    height = _get_optional_float(
        section,
        "HEIGHT",
    )

    flux = _get_optional_float(
        section,
        "FLUX",
    )

    intensity_value = _get_optional_float(
        section,
        "INTENSITY",
    )

    intensity_45 = _get_optional_float(
        section,
        "INTENSITY_45",
    )

    intensity_50 = _get_optional_float(
        section,
        "INTENSITY_50",
    )

    # Проверяем фотометрические параметры.
    if photometry == "FLUX":

        if flux is None:
            raise ValueError(
                f"{section_name}: для PHOTOMETRY=FLUX "
                "требуется параметр FLUX."
            )

        if flux <= 0:
            raise ValueError(
                f"{section_name}: FLUX должен быть > 0."
            )

    if photometry == "INTENSITY":

        if source_type in {"SPHERE", "DISK"}:

            if intensity_value is None:
                raise ValueError(
                    f"{section_name}: требуется INTENSITY."
                )

            if intensity_value <= 0:
                raise ValueError(
                    f"{section_name}: INTENSITY должен быть > 0."
                )

        elif source_type == "CYLINDER":

            if intensity_45 is None:
                raise ValueError(
                    f"{section_name}: требуется INTENSITY_45."
                )

            if intensity_45 <= 0:
                raise ValueError(
                    f"{section_name}: "
                    "INTENSITY_45 должен быть > 0."
                )

        elif source_type in {
            "HEMISPHERE",
            "HALF_SPHERE",
        }:

            if intensity_50 is None:
                raise ValueError(
                    f"{section_name}: требуется INTENSITY_50."
                )

            if intensity_50 <= 0:
                raise ValueError(
                    f"{section_name}: "
                    "INTENSITY_50 должен быть > 0."
                )

    if source_type == "CYLINDER":

        if height is None:
            raise ValueError(
                f"{section_name}: "
                "для CYLINDER требуется HEIGHT."
            )

        if height <= 0:
            raise ValueError(
                f"{section_name}: HEIGHT должен быть > 0."
            )

    if source_type == "DISK":

        if side is None:
            raise ValueError(
                f"{section_name}: "
                "для DISK требуется SIDE."
            )

        side = side.upper()

        if side not in {"UP", "DOWN"}:
            raise ValueError(
                f"{section_name}: SIDE должен быть "
                "UP или DOWN."
            )

    if source_type == "HEMISPHERE":

        if surface is None:
            raise ValueError(
                f"{section_name}: "
                "для HEMISPHERE требуется SURFACE."
            )

        surface = surface.upper()

        if surface not in {"INNER", "OUTER"}:
            raise ValueError(
                f"{section_name}: SURFACE должен быть "
                "INNER или OUTER."
            )

        if orientation is None:
            raise ValueError(
                f"{section_name}: "
                "для HEMISPHERE требуется ORIENTATION."
            )

    if source_type == "HALF_SPHERE":

        if orientation is None:
            raise ValueError(
                f"{section_name}: "
                "для HALF_SPHERE требуется ORIENTATION."
            )

        if surface is not None:
            raise ValueError(
                f"{section_name}: "
                "HALF_SPHERE не использует SURFACE."
            )

    if orientation is not None:
        orientation = orientation.upper()

        if orientation not in {"UP", "DOWN"}:
            raise ValueError(
                f"{section_name}: ORIENTATION должен быть "
                "UP или DOWN."
            )

    direction = _get_source_direction(
        source_type=source_type,
        orientation=orientation,
        side=side,
        surface=surface,
    )

    source = LightSource(
        index=index,
        source_type=source_type,
        position=position,
        diameter=diameter,
        photometry=photometry,
        orientation=orientation,
        side=side,
        surface=surface,
        height=height,
        flux=flux,
        intensity=intensity_value,
        intensity_45=intensity_45,
        intensity_50=intensity_50,
        direction=direction,
    )

    # Рассчитываем фотометрические параметры.
    if source_type == "SPHERE":
        sphere.calculate_parameters(source)

    elif source_type == "DISK":
        disk.calculate_parameters(source)

    elif source_type == "CYLINDER":
        cylinder.calculate_parameters(source)

    elif source_type == "HEMISPHERE":
        hemisphere.calculate_hemisphere_parameters(source)

    elif source_type == "HALF_SPHERE":
        hemisphere.calculate_half_sphere_parameters(source)

    return source


def load_configuration(path: str | Path):
    """
    Главная функция загрузки конфигурации.

    Возвращает:

        room
        grid_config
        sources
        calculation_config
    """

    parser = _read_config(path)

    room = _parse_room(parser)

    grid_config = _parse_grid(parser)

    calculation_config = _parse_calculation(parser)

    if "SOURCES" not in parser:
        raise ValueError(
            "В файле отсутствует секция [SOURCES]."
        )

    sources_section = parser["SOURCES"]

    count = _get_int(
        sources_section,
        "COUNT",
        "SOURCES",
    )

    if count < 1 or count > 3:
        raise ValueError(
            "SOURCES.COUNT должен быть от 1 до 3."
        )

    sources = []

    for index in range(1, count + 1):
        source = _parse_source(
            parser,
            index,
            room,
        )

        sources.append(source)

    return (
        room,
        grid_config,
        sources,
        calculation_config,
    )