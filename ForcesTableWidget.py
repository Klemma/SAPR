from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from Colors import Color


class ForcesTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deleted_items = None

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key_Delete:
            item = self.currentItem()
            if item.background() == QBrush(QColor(*Color.light_yellow)):
                return
            row = item.row()
            self.removeRow(row)
            self.deleted_items = None
        else:
            super().keyPressEvent(e)

    def rowsAboutToBeRemoved(self, parent: QtCore.QModelIndex, start: int, end: int):
        row = self.currentRow()
        self.deleted_items = [self.item(row, col) for col in range(self.columnCount())]
