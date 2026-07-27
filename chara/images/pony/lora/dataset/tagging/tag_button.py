from typing import Callable
from PyQt6.QtWidgets import QPushButton, QMenu
from PyQt6.QtCore import Qt


class TagButton(QPushButton):
    def __init__(self, tag: str, state: bool, on_global_change: Callable[[str, bool], None]):
        super().__init__(tag)
        self.tag = tag
        self.state = state
        self.on_global_change = on_global_change
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._apply_style()

    def _apply_style(self):
        color = '#4caf50' if self.state else '#f44336'
        self.setStyleSheet(f'background-color: {color}; color: white; font-weight: bold;')

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.state = not self.state
            self._apply_style()
        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu()
            accept_action = menu.addAction('Global accept')
            reject_action = menu.addAction('Global reject')
            action = menu.exec(event.globalPosition().toPoint())
            if action == accept_action:
                self.on_global_change(self.tag, True)
            elif action == reject_action:
                self.on_global_change(self.tag, False)
        else:
            super().mousePressEvent(event)
