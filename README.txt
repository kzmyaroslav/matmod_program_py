НАСТРОЙКА INPUT.TXT
====================

input.txt состоит из секций [ROOM], [GRID], [SOURCES],
[SOURCE_1...SOURCE_3] и [CALCULATION].

1. ПОМЕЩЕНИЕ

[ROOM]
UNIT = M
X = 10.0
Y = 8.0
Z = 3.0

UNIT: M — метры, CM — сантиметры, MM — миллиметры.
X, Y — размеры помещения, Z — высота.

Начало координат: (0, 0, 0).

2. СЕТКА

[GRID]
STEP = 0.5

STEP — шаг расчётной сетки в метрах. Чем меньше STEP,
тем подробнее расчёт и тем больше расчётных точек.

3. КОЛИЧЕСТВО ИСТОЧНИКОВ

[SOURCES]
COUNT = 2

Допустимо от 1 до 3 источников.

4. ОБЩИЕ ПАРАМЕТРЫ ИСТОЧНИКА

Каждый источник находится в отдельной секции:

[SOURCE_1]
[SOURCE_2]
[SOURCE_3]

Общие параметры:

TYPE = SPHERE / DISK / CYLINDER / HEMISPHERE / HALF_SPHERE
X, Y, Z — координаты центра источника, м.
DIAMETER — диаметр, м.
PHOTOMETRY = INTENSITY или FLUX.

5. SPHERE

[SOURCE_1]
TYPE = SPHERE
X = 5.0
Y = 4.0
Z = 2.8
DIAMETER = 0.10
PHOTOMETRY = INTENSITY
INTENSITY = 1000

INTENSITY — сила света, кд.

Или:

PHOTOMETRY = FLUX
FLUX = 1500

FLUX — световой поток, лм.

6. DISK

[SOURCE_1]
TYPE = DISK
X = 5.0
Y = 4.0
Z = 2.8
DIAMETER = 0.10
SIDE = DOWN
PHOTOMETRY = INTENSITY
INTENSITY = 1000

SIDE:
UP — излучение в сторону +Z.
DOWN — излучение в сторону -Z.

INTENSITY задаёт силу света по нормали к диску.

При FLUX используется параметр FLUX.

7. CYLINDER

[SOURCE_1]
TYPE = CYLINDER
X = 5.0
Y = 4.0
Z = 2.8
DIAMETER = 0.10
HEIGHT = 0.10
PHOTOMETRY = INTENSITY
INTENSITY_45 = 500

HEIGHT — высота цилиндра, м.
Ось цилиндра вертикальна и совпадает с Z.
INTENSITY_45 — сила света при 45° относительно оси.

При FLUX используется FLUX.

8. HEMISPHERE

[SOURCE_1]
TYPE = HEMISPHERE
SURFACE = INNER
ORIENTATION = UP
X = 5.0
Y = 4.0
Z = 2.5
DIAMETER = 0.5
PHOTOMETRY = INTENSITY
INTENSITY_50 = 800

SURFACE:
INNER — внутренняя поверхность.
OUTER — внешняя поверхность.

ORIENTATION:
UP — выпуклая часть направлена вверх (+Z).
DOWN — выпуклая часть направлена вниз (-Z).

INTENSITY_50 — сила света при 50° относительно
направления максимальной силы света.

При FLUX используется FLUX.

9. HALF_SPHERE

[SOURCE_1]
TYPE = HALF_SPHERE
ORIENTATION = DOWN
X = 5.0
Y = 4.0
Z = 2.5
DIAMETER = 0.5
PHOTOMETRY = INTENSITY
INTENSITY_50 = 800

HALF_SPHERE — полностью светящийся полушар,
включая сферическую поверхность и плоское основание.

SURFACE для него НЕ используется.

ORIENTATION: UP или DOWN.

При FLUX используется FLUX.

10. ВЫБОР РАСЧЁТНОЙ ПЛОСКОСТИ

После запуска программа спрашивает:

X — плоскость X = const (YZ)
Y — плоскость Y = const (XZ)
Z — плоскость Z = const (XY)

Например, Z = 0 — расчёт освещённости пола.

11. НАСТРОЙКИ РАСЧЁТА

[CALCULATION]
DEBUG = FALSE
DECIMAL_PLACES = 2

DEBUG: TRUE или FALSE.
DECIMAL_PLACES — количество знаков после запятой.

12. ПОЛНЫЙ ПРИМЕР

[ROOM]
UNIT = M
X = 10.0
Y = 8.0
Z = 3.0

[GRID]
STEP = 0.5

[SOURCES]
COUNT = 2

[SOURCE_1]
TYPE = SPHERE
X = 5.0
Y = 4.0
Z = 2.8
DIAMETER = 0.10
PHOTOMETRY = INTENSITY
INTENSITY = 1000

[SOURCE_2]
TYPE = DISK
X = 2.0
Y = 2.0
Z = 2.7
DIAMETER = 0.10
SIDE = DOWN
PHOTOMETRY = FLUX
FLUX = 1500

[CALCULATION]
DEBUG = FALSE
DECIMAL_PLACES = 2

13. ВАЖНЫЕ ПРАВИЛА

- Десятичный разделитель — точка: 2.5, а не 2,5.
- COUNT должен быть от 1 до 3.
- STEP должен быть больше нуля.
- Диаметр и HEIGHT должны быть больше нуля.
- Координаты источников должны находиться внутри помещения.
- CYLINDER требует HEIGHT.
- DISK требует SIDE.
- HEMISPHERE требует SURFACE и ORIENTATION.
- HALF_SPHERE не использует SURFACE.
- Для INTENSITY и FLUX используются разные параметры,
  указанные выше.

14. РЕЗУЛЬТАТЫ

После расчёта в папке results создаются:

calculation.xlsx — подробный Excel.
illuminance_map.png — карта освещённости.
room_3d.png — 3D-визуализация помещения.

15. ЦВЕТОВАЯ КАРТА

На карте освещённости значения идут по стандартной
спектральной шкале:

тёмно-фиолетовый → синий → голубой → зелёный →
жёлтый → оранжевый → красный.

Тёмно-фиолетовый соответствует меньшим значениям,
красный — большим.

16. ФОРМУЛА РАСЧЁТА

Для каждой точки:

E = I(alpha) / r² × |cos(beta)|

где E — освещённость, лк;
I(alpha) — сила света в направлении точки, кд;
r — расстояние от источника до точки;
alpha — угол относительно направления максимальной силы света;
beta — угол падения света на расчётную плоскость.

При нескольких источниках:

E_total = E1 + E2 + E3

17. БЫСТРЫЙ ШАБЛОН

[ROOM]
UNIT = M
X = 10.0
Y = 10.0
Z = 3.0

[GRID]
STEP = 0.5

[SOURCES]
COUNT = 1

[SOURCE_1]
TYPE = SPHERE
X = 5.0
Y = 5.0
Z = 2.8
DIAMETER = 0.10
PHOTOMETRY = INTENSITY
INTENSITY = 1000

[CALCULATION]
DEBUG = FALSE
DECIMAL_PLACES = 2

После запуска для расчёта пола выбрать Z и координату 0.
