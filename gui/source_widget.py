from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from models.sources import LightSource
from photometry import sphere, disk, cylinder, hemisphere


SOURCE_TYPES = {
    "SPHERE": "Сфера",
    "DISK": "Диск",
    "CYLINDER": "Цилиндр",
    "HEMISPHERE": "Полусфера",
    "HALF_SPHERE": "Полушар",
}


class SourceWidget(QGroupBox):
    changed = Signal()

    def __init__(self, index: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.index = index
        self.setTitle(f"Источник {index}")
        self._build_ui()
        self._connect_signals()
        self._update_dynamic_fields()

    def _spin(self, value=0.0, maximum=1_000_000.0, decimals=3):
        box = QDoubleSpinBox()
        box.setRange(-1_000_000.0, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(0.1)
        box.setValue(value)
        return box

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 20, 14, 14)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.type_combo = QComboBox()
        for key, label in SOURCE_TYPES.items():
            self.type_combo.addItem(label, key)
        top.addWidget(QLabel("Тип"))
        top.addWidget(self.type_combo, 1)
        root.addLayout(top)

        position = QGroupBox("Положение")
        form = QFormLayout(position)
        form.setContentsMargins(10, 10, 10, 10)

        self.x_spin = self._spin(5.0)
        self.y_spin = self._spin(4.0)
        self.z_spin = self._spin(2.8)
        self.diameter_spin = self._spin(0.1, 1000.0)

        form.addRow("X, м", self.x_spin)
        form.addRow("Y, м", self.y_spin)
        form.addRow("Z, м", self.z_spin)
        form.addRow("Диаметр, м", self.diameter_spin)

        self.height_label = QLabel("Высота, м")
        self.height_spin = self._spin(0.1, 1000.0)
        form.addRow(self.height_label, self.height_spin)

        root.addWidget(position)

        self.side_label = QLabel("Сторона")
        self.side_combo = QComboBox()
        self.side_combo.addItem("Вверх", "UP")
        self.side_combo.addItem("Вниз", "DOWN")

        self.surface_label = QLabel("Поверхность")
        self.surface_combo = QComboBox()
        self.surface_combo.addItem("Внутренняя", "INNER")
        self.surface_combo.addItem("Внешняя", "OUTER")

        self.orientation_label = QLabel("Ориентация")
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("Вверх", "UP")
        self.orientation_combo.addItem("Вниз", "DOWN")

        direction = QGroupBox("Направление")
        direction_form = QFormLayout(direction)
        direction_form.addRow(self.side_label, self.side_combo)
        direction_form.addRow(self.surface_label, self.surface_combo)
        direction_form.addRow(self.orientation_label, self.orientation_combo)
        root.addWidget(direction)

        photo = QGroupBox("Фотометрия")
        photo_layout = QVBoxLayout(photo)

        row = QHBoxLayout()
        self.intensity_radio = QRadioButton("Сила света")
        self.flux_radio = QRadioButton("Световой поток")
        self.intensity_radio.setChecked(True)
        row.addWidget(self.intensity_radio)
        row.addWidget(self.flux_radio)
        row.addStretch()
        photo_layout.addLayout(row)

        self.value_form = QFormLayout()
        self.intensity_spin = self._spin(1000.0, 1_000_000_000.0)
        self.intensity_45_spin = self._spin(500.0, 1_000_000_000.0)
        self.intensity_50_spin = self._spin(800.0, 1_000_000_000.0)
        self.flux_spin = self._spin(1500.0, 1_000_000_000.0)

        self.value_form.addRow("I, кд", self.intensity_spin)
        self.value_form.addRow("I(45°), кд", self.intensity_45_spin)
        self.value_form.addRow("I(50°), кд", self.intensity_50_spin)
        self.value_form.addRow("Φ, лм", self.flux_spin)
        photo_layout.addLayout(self.value_form)
        root.addWidget(photo)

    def _connect_signals(self):
        self.type_combo.currentIndexChanged.connect(self._update_dynamic_fields)
        self.intensity_radio.toggled.connect(self._update_dynamic_fields)

        widgets = [
            self.x_spin, self.y_spin, self.z_spin, self.diameter_spin,
            self.height_spin, self.side_combo, self.surface_combo,
            self.orientation_combo, self.intensity_spin,
            self.intensity_45_spin, self.intensity_50_spin, self.flux_spin,
        ]
        for widget in widgets:
            if isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self.changed)
            else:
                widget.currentIndexChanged.connect(self.changed)

    def _set_row_visible(self, form, field, visible):
        label = form.labelForField(field)
        if label:
            label.setVisible(visible)
        field.setVisible(visible)

    def _update_dynamic_fields(self):
        t = self.source_type
        intensity = self.intensity_radio.isChecked()

        cylinder = t == "CYLINDER"
        disk = t == "DISK"
        hemi = t == "HEMISPHERE"
        half = t == "HALF_SPHERE"

        self.height_label.setVisible(cylinder)
        self.height_spin.setVisible(cylinder)

        self.side_label.setVisible(disk)
        self.side_combo.setVisible(disk)

        self.surface_label.setVisible(hemi)
        self.surface_combo.setVisible(hemi)

        show_orientation = hemi or half
        self.orientation_label.setVisible(show_orientation)
        self.orientation_combo.setVisible(show_orientation)

        self._set_row_visible(
            self.value_form, self.intensity_spin,
            t in {"SPHERE", "DISK"} and intensity
        )
        self._set_row_visible(
            self.value_form, self.intensity_45_spin,
            cylinder and intensity
        )
        self._set_row_visible(
            self.value_form, self.intensity_50_spin,
            (hemi or half) and intensity
        )
        self._set_row_visible(
            self.value_form, self.flux_spin, not intensity
        )

        self.changed.emit()

    @property
    def source_type(self):
        return str(self.type_combo.currentData())

    @property
    def photometry(self):
        return "INTENSITY" if self.intensity_radio.isChecked() else "FLUX"

    def _direction(self, source_type, side, surface, orientation):
        if source_type in {"SPHERE", "CYLINDER"}:
            return np.array([0.0, 0.0, 1.0])
        if source_type == "DISK":
            return np.array([0.0, 0.0, 1.0 if side == "UP" else -1.0])

        convex = np.array(
            [0.0, 0.0, 1.0 if orientation == "UP" else -1.0]
        )
        if source_type == "HALF_SPHERE":
            return convex
        return -convex if surface == "INNER" else convex

    def build_source(self):
        t = self.source_type
        p = self.photometry

        side = self.side_combo.currentData() if t == "DISK" else None
        surface = self.surface_combo.currentData() if t == "HEMISPHERE" else None
        orientation = (
            self.orientation_combo.currentData()
            if t in {"HEMISPHERE", "HALF_SPHERE"} else None
        )

        intensity = None
        intensity_45 = None
        intensity_50 = None
        flux = None

        if p == "FLUX":
            flux = self.flux_spin.value()
        elif t in {"SPHERE", "DISK"}:
            intensity = self.intensity_spin.value()
        elif t == "CYLINDER":
            intensity_45 = self.intensity_45_spin.value()
        else:
            intensity_50 = self.intensity_50_spin.value()

        source = LightSource(
            index=self.index,
            source_type=t,
            position=np.array([
                self.x_spin.value(),
                self.y_spin.value(),
                self.z_spin.value(),
            ], dtype=float),
            diameter=self.diameter_spin.value(),
            photometry=p,
            orientation=orientation,
            side=side,
            surface=surface,
            height=self.height_spin.value() if t == "CYLINDER" else None,
            flux=flux,
            intensity=intensity,
            intensity_45=intensity_45,
            intensity_50=intensity_50,
            direction=self._direction(t, side, surface, orientation),
        )

        if t == "SPHERE":
            sphere.calculate_parameters(source)
        elif t == "DISK":
            disk.calculate_parameters(source)
        elif t == "CYLINDER":
            cylinder.calculate_parameters(source)
        elif t == "HEMISPHERE":
            hemisphere.calculate_hemisphere_parameters(source)
        elif t == "HALF_SPHERE":
            hemisphere.calculate_half_sphere_parameters(source)

        return source
