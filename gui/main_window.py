from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from calculation.illuminance import calculate, calculate_statistics
from config.parser import CalculationConfig
from models.grid import GridConfig, create_grid
from models.room import Room
from output.excel import export_to_excel
from visualization.heatmap import create_heatmap
from visualization.room_3d import create_room_3d

from .source_widget import SourceWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.base_dir = Path(__file__).resolve().parent.parent
        self.results_dir = self.base_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.last_excel = None
        self.last_heatmap = None
        self.last_room3d = None

        self.setWindowTitle("МатМодРЗ • Расчёт освещённости")
        self.resize(1500, 930)
        self.setMinimumSize(1180, 760)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._create_header())

        body = QSplitter(Qt.Horizontal)
        body.setChildrenCollapsible(False)

        sidebar = self._create_sidebar()
        body.addWidget(sidebar)

        workspace = self._create_workspace()
        body.addWidget(workspace)

        body.setSizes([430, 1070])
        root.addWidget(body, 1)

        self.statusBar().showMessage("Готово к расчёту")

    def _create_header(self):
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)

        brand = QVBoxLayout()
        title = QLabel("МатМодРЗ")
        title.setObjectName("brand")
        subtitle = QLabel("РАСЧЁТ ОСВЕЩЁННОСТИ • ENGINEERING TOOL")
        subtitle.setObjectName("subtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)

        layout.addLayout(brand)
        layout.addStretch()

        self.header_status = QLabel("●  ГОТОВ")
        self.header_status.setObjectName("headerStatus")
        layout.addWidget(self.header_status)

        return header

    def _create_sidebar(self):
        container = QFrame()
        container.setObjectName("sidebar")

        outer = QVBoxLayout(container)
        outer.setContentsMargins(16, 16, 12, 16)
        outer.setSpacing(10)

        # Заголовок панели
        title = QLabel("ПАРАМЕТРЫ РАСЧЁТА")
        title.setObjectName("sectionTitle")
        outer.addWidget(title)

        # Область прокрутки.
        # ВАЖНО: здесь больше нет локальной тёмной таблицы стилей.
        # Весь внешний вид задаётся единым светлым стилем в _apply_style().
        scroll = QScrollArea()
        scroll.setObjectName("parametersScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Контейнер содержимого
        content = QWidget()
        content.setObjectName("scrollContent")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(12)

        # Помещение
        layout.addWidget(self._create_room_group())

        # Расчётная сетка
        layout.addWidget(self._create_grid_group())

        # Плоскость расчёта
        layout.addWidget(self._create_plane_group())

        # Источники
        layout.addWidget(self._create_sources_group())

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # Кнопка расчёта
        self.calculate_button = QPushButton("▶   РАССЧИТАТЬ")
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.setMinimumHeight(48)
        self.calculate_button.clicked.connect(self.run_calculation)

        outer.addWidget(self.calculate_button)

        return container

    def _create_room_group(self):
        group = QGroupBox("ПО МЕЩЕНИЮ")
        form = QFormLayout(group)

        self.room_x = self._spin(10.0, 10000.0)
        self.room_y = self._spin(8.0, 10000.0)
        self.room_z = self._spin(3.0, 10000.0)

        form.addRow("Длина X", self.room_x)
        form.addRow("Ширина Y", self.room_y)
        form.addRow("Высота Z", self.room_z)
        return group

    def _create_grid_group(self):
        group = QGroupBox("РАСЧЁТНАЯ СЕТКА")
        form = QFormLayout(group)

        self.grid_step = self._spin(0.5, 1000.0, 3)
        self.grid_step.setMinimum(0.0001)
        self.grid_step.setSingleStep(0.1)

        self.decimal_places = QDoubleSpinBox()
        self.decimal_places.setRange(0, 8)
        self.decimal_places.setDecimals(0)
        self.decimal_places.setValue(2)

        form.addRow("Шаг, м", self.grid_step)
        form.addRow("Знаков", self.decimal_places)
        return group

    def _create_plane_group(self):
        group = QGroupBox("ПЛОСКОСТЬ РАСЧЁТА")
        form = QFormLayout(group)

        self.plane_combo = QComboBox()
        self.plane_combo.addItem("XY  ·  Z = const", "Z")
        self.plane_combo.addItem("XZ  ·  Y = const", "Y")
        self.plane_combo.addItem("YZ  ·  X = const", "X")
        self.plane_combo.currentIndexChanged.connect(self._update_plane_coordinate)

        self.plane_coordinate = self._spin(0.0, 10000.0)
        form.addRow("Плоскость", self.plane_combo)
        form.addRow("Координата, м", self.plane_coordinate)

        self.room_x.valueChanged.connect(self._update_plane_coordinate)
        self.room_y.valueChanged.connect(self._update_plane_coordinate)
        self.room_z.valueChanged.connect(self._update_plane_coordinate)

        self._update_plane_coordinate()
        return group

    def _create_sources_group(self):
        group = QGroupBox("ИСТОЧНИКИ")
        layout = QVBoxLayout(group)

        top = QHBoxLayout()
        top.addWidget(QLabel("Количество"))
        self.source_count_combo = QComboBox()
        for count in (1, 2, 3):
            self.source_count_combo.addItem(str(count), count)
        self.source_count_combo.currentIndexChanged.connect(self._update_source_count)
        top.addWidget(self.source_count_combo)
        top.addStretch()
        layout.addLayout(top)

        self.sources_container = QWidget()
        self.sources_layout = QVBoxLayout(self.sources_container)
        self.sources_layout.setContentsMargins(0, 4, 0, 0)
        layout.addWidget(self.sources_container)

        self._update_source_count()
        return group

    def _create_workspace(self):
        workspace = QFrame()
        workspace.setObjectName("workspace")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(18, 18, 18, 18)

        self.results_tabs = QTabWidget()
        self.results_tabs.setDocumentMode(True)

        self.results_tabs.addTab(self._create_dashboard(), "ОБЗОР")
        self.results_tabs.addTab(self._create_image_page("КАРТА ОСВЕЩЁННОСТИ"), "КАРТА")
        self.results_tabs.addTab(self._create_image_page("3D МОДЕЛЬ"), "3D")

        layout.addWidget(self.results_tabs, 1)

        bottom = QHBoxLayout()

        self.result_path = QLabel("Результаты ещё не созданы")
        self.result_path.setObjectName("muted")

        self.open_excel_button = QPushButton("Открыть Excel")
        self.open_excel_button.setEnabled(False)
        self.open_excel_button.clicked.connect(self.open_excel)

        self.open_map_button = QPushButton("Открыть карту")
        self.open_map_button.setEnabled(False)
        self.open_map_button.clicked.connect(self.open_heatmap)

        bottom.addWidget(self.result_path)
        bottom.addStretch()
        bottom.addWidget(self.open_map_button)
        bottom.addWidget(self.open_excel_button)

        layout.addLayout(bottom)
        return workspace

    def _create_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        intro = QLabel("Результаты расчёта")
        intro.setObjectName("pageTitle")
        layout.addWidget(intro)

        hint = QLabel(
            "Запусти расчёт — здесь появятся основные показатели "
            "и краткая оценка равномерности."
        )
        hint.setObjectName("muted")
        layout.addWidget(hint)

        cards = QGridLayout()
        cards.setSpacing(12)

        self.stat_cards = {}
        card_data = [
            ("Emin", "Минимум", "лк"),
            ("Emax", "Максимум", "лк"),
            ("Eavg", "Среднее", "лк"),
            ("Emin/Emax", "Равномерность", ""),
        ]

        for i, (key, title, unit) in enumerate(card_data):
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)

            label = QLabel(title.upper())
            label.setObjectName("metricLabel")

            value = QLabel("—")
            value.setObjectName("metricValue")

            unit_label = QLabel(unit)
            unit_label.setObjectName("metricUnit")

            card_layout.addWidget(label)
            card_layout.addWidget(value)
            card_layout.addWidget(unit_label)

            cards.addWidget(card, 0, i)
            self.stat_cards[key] = value

        layout.addLayout(cards)

        info = QFrame()
        info.setObjectName("infoPanel")
        info_layout = QVBoxLayout(info)

        self.summary_label = QLabel(
            "Пока расчёт не выполнен."
        )
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("summary")
        info_layout.addWidget(self.summary_label)

        layout.addWidget(info)
        layout.addStretch()

        return page

    def _create_image_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        label = QLabel(f"{text}\n\nПосле расчёта здесь появится визуализация.")
        label.setObjectName("imageView")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, 1)

        if text == "КАРТА ОСВЕЩЁННОСТИ":
            self.map_label = label
        else:
            self.room_label = label

        return page

    def _spin(self, value=0.0, maximum=10000.0, decimals=3):
        box = QDoubleSpinBox()
        box.setRange(0.0, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(0.1)
        box.setValue(value)
        return box

    def _update_plane_coordinate(self):
        plane = self.plane_combo.currentData()
        limits = {
            "X": self.room_x.value(),
            "Y": self.room_y.value(),
            "Z": self.room_z.value(),
        }
        self.plane_coordinate.setMaximum(limits[plane])
        if self.plane_coordinate.value() > limits[plane]:
            self.plane_coordinate.setValue(limits[plane])

    def _update_source_count(self):
        while self.sources_layout.count():
            item = self.sources_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        count = int(self.source_count_combo.currentData())
        for index in range(1, count + 1):
            self.sources_layout.addWidget(SourceWidget(index))

    def _collect_sources(self):
        room = Room(
            self.room_x.value(),
            self.room_y.value(),
            self.room_z.value(),
        )

        sources = []
        for i in range(self.sources_layout.count()):
            widget = self.sources_layout.itemAt(i).widget()
            if isinstance(widget, SourceWidget):
                source = widget.build_source()
                if not room.contains_point(source.position):
                    raise ValueError(
                        f"Источник {source.index} находится за пределами помещения."
                    )
                sources.append(source)

        if not sources:
            raise ValueError("Не задан ни один источник.")

        return room, sources

    def run_calculation(self):
        self.calculate_button.setEnabled(False)
        self.header_status.setText("●  РАСЧЁТ...")
        self.header_status.setObjectName("headerStatusBusy")
        self.header_status.style().unpolish(self.header_status)
        self.header_status.style().polish(self.header_status)
        self.statusBar().showMessage("Выполняется расчёт...")
        QApplication.processEvents()

        try:
            room, sources = self._collect_sources()
            grid_config = GridConfig(step=self.grid_step.value())

            grid = create_grid(
                room=room,
                grid_config=grid_config,
                plane=self.plane_combo.currentData(),
                coordinate=self.plane_coordinate.value(),
            )

            illuminance, contributions = calculate(
                grid=grid,
                sources=sources,
            )
            statistics = calculate_statistics(illuminance)

            calculation_config = CalculationConfig(
                debug=False,
                decimal_places=int(self.decimal_places.value()),
            )

            excel_path = self.results_dir / "calculation.xlsx"
            heatmap_path = self.results_dir / "illuminance_map.png"
            room_path = self.results_dir / "room_3d.png"

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

            create_heatmap(
                grid=grid,
                illuminance=illuminance,
                output_path=heatmap_path,
                decimal_places=calculation_config.decimal_places,
            )

            create_room_3d(
                room=room,
                grid=grid,
                sources=sources,
                output_path=room_path,
            )

            self.last_excel = excel_path
            self.last_heatmap = heatmap_path
            self.last_room3d = room_path

            self._show_statistics(statistics)
            self._show_image(self.map_label, heatmap_path)
            self._show_image(self.room_label, room_path)

            self.open_excel_button.setEnabled(True)
            self.open_map_button.setEnabled(True)
            self.result_path.setText(
                f"Результаты сохранены в  results/"
            )

            self.results_tabs.setCurrentIndex(0)
            self.header_status.setText("●  ГОТОВО")
            self.header_status.setObjectName("headerStatus")
            self.header_status.style().unpolish(self.header_status)
            self.header_status.style().polish(self.header_status)

            self.summary_label.setText(
                f"Расчёт выполнен для {len(grid.points)} точек. "
                f"Плоскость: {grid.plane} = {grid.coordinate:g} м. "
                f"Источников: {len(sources)}. "
                f"Максимальная освещённость — {statistics['Emax']:.2f} лк."
            )
            self.statusBar().showMessage("Расчёт завершён")

        except Exception as exc:
            self.header_status.setText("●  ОШИБКА")
            self.header_status.setObjectName("headerStatusError")
            self.header_status.style().unpolish(self.header_status)
            self.header_status.style().polish(self.header_status)

            QMessageBox.critical(self, "Ошибка расчёта", str(exc))
            self.statusBar().showMessage("Расчёт завершился с ошибкой")
        finally:
            self.calculate_button.setEnabled(True)

    def _show_statistics(self, stats):
        for key in ("Emin", "Emax", "Eavg"):
            self.stat_cards[key].setText(f"{stats[key]:.2f}")
        self.stat_cards["Emin/Emax"].setText(f"{stats['Emin/Emax']:.3f}")

    def _show_image(self, label, path):
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            label.setText(f"Не удалось загрузить:\n{path}")
            return

        scaled = pixmap.scaled(
            label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.last_heatmap:
            self._show_image(self.map_label, self.last_heatmap)
        if self.last_room3d:
            self._show_image(self.room_label, self.last_room3d)

    def _open_path(self, path):
        if not path or not Path(path).exists():
            return

        path = Path(path)
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)

    def open_excel(self):
        self._open_path(self.last_excel)

    def open_heatmap(self):
        self._open_path(self.last_heatmap)

    def _apply_style(self):
        self.setStyleSheet("""
            * {
                font-family: "Segoe UI", "Arial";
                font-size: 13px;
            }

            QMainWindow {
                background: #f3f5f8;
            }

            QFrame#header {
                background: #ffffff;
                border-bottom: 1px solid #d9dee7;
            }

            QLabel {
                color: #26313f;
            }

            QLabel#brand {
                color: #18202b;
                font-size: 25px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#subtitle {
                color: #7a8494;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.5px;
            }

            QLabel#headerStatus {
                color: #16834b;
                font-weight: 700;
            }

            QLabel#headerStatusBusy {
                color: #a66a00;
                font-weight: 700;
            }

            QLabel#headerStatusError {
                color: #c83b3b;
                font-weight: 700;
            }

            QFrame#sidebar {
                background: #f7f8fa;
                border-right: 1px solid #d9dee7;
            }

            QFrame#workspace {
                background: #f3f5f8;
            }

            QLabel#sectionTitle {
                color: #667085;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.3px;
                padding: 2px 4px 8px;
            }

            /* ===== КАРТОЧКИ ПАРАМЕТРОВ ===== */

            QGroupBox {
                color: #253041;
                font-weight: 700;
                border: 1px solid #d4dae3;
                border-radius: 9px;
                margin-top: 10px;
                padding: 14px 10px 10px;
                background: #ffffff;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 11px;
                padding: 0 6px;
                color: #536174;
                background: #ffffff;
            }

            /* ===== ОБЛАСТЬ ПРОКРУТКИ ===== */

            QScrollArea#parametersScroll {
                background: #f7f8fa;
                border: none;
            }

            QScrollArea#parametersScroll > QWidget {
                background: #f7f8fa;
                border: none;
            }

            QWidget#scrollContent {
                background: #f7f8fa;
            }

            /* ===== ПОЛЯ ВВОДА ===== */

            QDoubleSpinBox {
                min-height: 34px;
                min-width: 150px;
                color: #202936;
                background: #ffffff;
                border: 1px solid #aeb8c6;
                border-radius: 7px;
                padding: 2px 28px 2px 9px;
                selection-background-color: #536df0;
                selection-color: #ffffff;
            }

            QDoubleSpinBox:hover {
                border: 1px solid #7f8b9d;
                background: #ffffff;
            }

            QDoubleSpinBox:focus {
                border: 2px solid #536df0;
                background: #ffffff;
            }

            QDoubleSpinBox::up-button,
            QDoubleSpinBox::down-button {
                width: 22px;
                background: #f1f3f6;
                border-left: 1px solid #d0d6df;
            }

            QDoubleSpinBox::up-button {
                border-bottom: 1px solid #d0d6df;
            }

            QDoubleSpinBox::up-button:hover,
            QDoubleSpinBox::down-button:hover {
                background: #e3e8ef;
            }

            /* ===== ВЫПАДАЮЩИЕ СПИСКИ ===== */

            QComboBox {
                min-height: 34px;
                min-width: 150px;
                color: #202936;
                background: #ffffff;
                border: 1px solid #aeb8c6;
                border-radius: 7px;
                padding: 2px 32px 2px 9px;
            }

            QComboBox:hover {
                border: 1px solid #7f8b9d;
                background: #ffffff;
            }

            QComboBox:focus {
                border: 2px solid #536df0;
                background: #ffffff;
            }

            QComboBox::drop-down {
                width: 27px;
                background: #f1f3f6;
                border-left: 1px solid #d0d6df;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }

            QComboBox::drop-down:hover {
                background: #e3e8ef;
            }

            QComboBox QAbstractItemView {
                color: #202936;
                background: #ffffff;
                border: 1px solid #aeb8c6;
                selection-color: #ffffff;
                selection-background-color: #536df0;
                padding: 4px;
            }

            /* ===== КНОПКИ ===== */

            QPushButton {
                color: #344054;
                background: #ffffff;
                border: 1px solid #c7ced9;
                border-radius: 7px;
                padding: 7px 14px;
                min-height: 31px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #f1f4f8;
                border-color: #9aa6b6;
            }

            QPushButton:pressed {
                background: #e8ecf2;
            }

            QPushButton#primaryButton {
                color: #ffffff;
                background: #5367e8;
                border: none;
                font-weight: 800;
                letter-spacing: 0.5px;
            }

            QPushButton#primaryButton:hover {
                background: #465bd8;
            }

            QPushButton#primaryButton:disabled {
                background: #aab3d8;
                color: #eef0f8;
            }

            /* ===== ВКЛАДКИ ===== */

            QTabWidget::pane {
                background: #ffffff;
                border: 1px solid #d7dde6;
                border-radius: 8px;
            }

            QTabBar::tab {
                color: #667085;
                background: #e9edf3;
                padding: 10px 18px;
                border: none;
            }

            QTabBar::tab:hover {
                color: #344054;
                background: #dde3eb;
            }

            QTabBar::tab:selected {
                color: #253041;
                background: #ffffff;
                font-weight: 700;
                border-bottom: 2px solid #5367e8;
            }

            /* ===== РЕЗУЛЬТАТЫ ===== */

            QLabel#pageTitle {
                color: #18202b;
                font-size: 24px;
                font-weight: 800;
            }

            QLabel#muted {
                color: #7a8494;
            }

            QFrame#metricCard {
                background: #ffffff;
                border: 1px solid #d7dde6;
                border-radius: 10px;
            }

            QLabel#metricLabel {
                color: #7a8494;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#metricValue {
                color: #18202b;
                font-size: 27px;
                font-weight: 800;
            }

            QLabel#metricUnit {
                color: #8a94a4;
                font-size: 11px;
            }

            QFrame#infoPanel {
                background: #f8fafc;
                border: 1px solid #d7dde6;
                border-radius: 10px;
            }

            QLabel#summary {
                color: #536174;
                padding: 10px;
            }

            QLabel#imageView {
                color: #7a8494;
                background: #f8fafc;
                border-radius: 8px;
                border: 1px solid #d7dde6;
            }

            /* ===== SCROLLBAR ===== */

            QScrollBar:vertical {
                background: #edf0f4;
                width: 9px;
                margin: 2px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #c1c8d3;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #a9b2c0;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QStatusBar {
                background: #ffffff;
                color: #7a8494;
                border-top: 1px solid #d9dee7;
            }
        """)

