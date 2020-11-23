from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QMessageBox, QTableWidget, QFileDialog
from PyQt5.QtCore import Qt
from gui import Ui_MainWindow
from BarConstruction import BarConstruction
from Colors import Color
import sys


def is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except:
        return False


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except:
        return False


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.bar_construction = BarConstruction()
        self.opening_project_file = False
        self.force_deleted_by_btn = False
        self.changed_table_item_style = False
        self.forces_table_data = {}
        self.set_table_items_alignment(self.bars_table)
        self.set_table_items_alignment(self.forces_table)
        self.set_table_cell_color(self.bars_table, Color.light_yellow, 0)
        self.set_table_cell_color(self.forces_table, Color.light_yellow, 0)
        self.set_btn_slots()
        self.set_table_slots()
        self.save_action.triggered.connect(self.save_project_file)
        self.open_action.triggered.connect(self.open_project_file)
        self.terminations_btn_group.buttonClicked.connect(self.terminations_btn_clicked)
        self.tab_widget_main.setTabEnabled(1, False)

    def save_project_file(self):
        if not self.bar_construction.bars:
            return
        data = "bars (E, L, A, S, q):\n"
        for i, bar in enumerate(self.bar_construction.bars):
            data += f"{list(bar.values())}\n"

        data += "\nforces (F):\n"
        for i, force in enumerate(self.bar_construction.forces):
            data += f"{force}\n"

        data += "\nterminations\n"
        for termination, state in self.bar_construction.terminations.items():
            data += f"{termination}: {state}\n"

        data = data[:-1]

        filename, _ = QFileDialog.getSaveFileName(self, "Save File", filter="*.sapr")
        if filename:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(data)

    def open_project_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", filter="*.sapr")
        if not filename:
            return

        self.opening_project_file = True

        with open(filename, 'r', encoding='utf-8') as file:
            data = file.read()
        data = data.split('\n\n')

        str_bars = data[0].split('\n')[1:]
        str_bars = [bar.translate(str.maketrans({'[': None, ']': None})) for bar in str_bars]
        str_forces = data[1].split('\n')[1:]
        str_terminations = data[2].split('\n')[1:]

        property_names = {
            0: 'E',
            1: 'L',
            2: 'A',
            3: 'S',
            4: 'q'
        }
        self.bar_construction.bars.clear()
        for i, bar in enumerate(str_bars):
            bar = bar.split(',')
            properties = {property_names[j]: float(bar_property) for j, bar_property in enumerate(bar)}
            self.bar_construction.add_bar(properties)

        self.bars_table.setRowCount(0)
        rows = len(self.bar_construction.bars)
        cols = self.bars_table.columnCount()
        for row in range(rows):
            self.bars_table.insertRow(row)
            for col in range(cols):
                item = QTableWidgetItem(str(self.bar_construction.bars[row][property_names.get(col)]))
                self.bars_table.setItem(row, col, item)
        self.bars_table.insertRow(rows)
        for col in range(cols - 1):
            item = QTableWidgetItem('1')
            self.bars_table.setItem(rows, col, item)
        self.bars_table.setItem(rows, cols - 1, QTableWidgetItem('0'))
        self.set_table_cell_color(self.bars_table, Color.light_yellow, rows)
        self.set_table_items_alignment(self.bars_table)

        self.bar_construction.forces.clear()
        forces = [float(force) for force in str_forces]
        self.bar_construction.forces = forces

        self.forces_table.setRowCount(0)
        nonzero_forces = [(i + 1, force) for i, force in enumerate(self.bar_construction.forces) if force != 0]
        rows = len(nonzero_forces)
        cols = self.forces_table.columnCount()
        for row in range(rows):
            self.forces_table.insertRow(row)
            for col in range(cols):
                item = QTableWidgetItem(str(nonzero_forces[row][col]))
                self.forces_table.setItem(row, col, item)
                self.forces_table_data[(row, col)] = item.text()
        self.forces_table.insertRow(rows)
        for col in range(cols):
            self.forces_table.setItem(rows, col, QTableWidgetItem('-'))
        self.set_table_cell_color(self.forces_table, Color.light_yellow, rows)
        self.set_table_items_alignment(self.forces_table)

        terminations = {}
        str_to_bool = {
            "True": True,
            "False": False
        }
        for termination in str_terminations:
            termination, state = termination.split(':')
            terminations[termination] = str_to_bool.get(state.strip())
        self.bar_construction.change_terminations(terminations)

        termination_btn = {
            "['left: True', 'right: False']": self.left_termination,
            "['left: True', 'right: True']": self.both_terminations,
            "['left: False', 'right: True']": self.right_termination
        }.get(str(str_terminations))
        termination_btn.setChecked(True)
        self.opening_project_file = False

    def terminations_btn_clicked(self):
        checked = self.terminations_btn_group.checkedButton().objectName()
        terminations_state = {
            "left_termination": {"left": True, "right": False},
            "both_terminations": {"left": True, "right": True},
            "right_termination": {"left": False, "right": True}
        }.get(checked)
        self.bar_construction.change_terminations(terminations_state)

    def set_btn_slots(self):
        self.add_bar_btn.clicked.connect(self.add_bar_btn_clicked)
        self.del_bar_btn.clicked.connect(self.del_bar_btn_clicked)
        self.add_force_btn.clicked.connect(self.add_force_btn_clicked)

    def set_table_slots(self):
        self.bars_table.cellChanged.connect(self.bars_table_cell_changed)
        self.forces_table.currentCellChanged.connect(self.forces_table_current_cell_changed)
        self.forces_table.itemChanged.connect(self.forces_table_item_changed)

    def set_table_cell_color(self, table: QTableWidget, color: tuple, row: int):
        cols = table.columnCount()
        for col in range(cols):
            self.changed_table_item_style = True
            table.item(row, col).setBackground(QBrush(QColor(*color)))

    def set_table_items_alignment(self, table: QTableWidget):
        rows = table.rowCount()
        cols = table.columnCount()

        for row in range(rows):
            for col in range(cols):
                self.changed_table_item_style = True
                table.item(row, col).setTextAlignment(Qt.AlignCenter)

    def forces_table_item_changed(self):
        if self.changed_table_item_style:
            self.changed_table_item_style = False
            return
        current_item = self.forces_table.currentItem()
        if current_item is None:
            return
        if current_item.background() == QBrush(QColor(*Color.light_yellow)):
            return
        if self.force_deleted_by_btn:
            self.force_deleted_by_btn = False
            return
        row = current_item.row()
        col = current_item.column()

        if col == 0:
            try:
                item = QTableWidgetItem(self.forces_table_data[(row, col)])
                if self.forces_table.item(row, col).text() != item.text():
                    self.forces_table.setItem(row, col, item)
                    item.setTextAlignment(Qt.AlignCenter)
            except KeyError:
                return
        else:
            if not is_float(current_item.text()):
                if self.forces_table.item(row, col).text() != self.forces_table_data[(row, col)]:
                    msg_box = QMessageBox(QMessageBox.Critical, "Ошибка",
                                          "Значение нагрузки должно быть вещественным числом!")
                    msg_box.exec()
                    item = QTableWidgetItem(self.forces_table_data[(row, col)])
                    self.forces_table.setItem(row, col, item)
                    item.setTextAlignment(Qt.AlignCenter)
            else:
                node = int(self.forces_table.item(row, 0).text())
                force = float(current_item.text())
                self.bar_construction.change_force(node, force)

    def forces_table_current_cell_changed(self):
        if self.opening_project_file:
            return
        deleted_items = self.forces_table.deleted_items
        if deleted_items is None or deleted_items.__contains__(None):
            return
        try:
            node = int(deleted_items[0].text())
        except:
            return
        if self.force_deleted_by_btn:
            self.force_deleted_by_btn = False
            return
        self.bar_construction.change_force(node, 0)
        rows = self.forces_table.rowCount()
        cols = self.forces_table.columnCount()
        self.forces_table_data.clear()
        for row in range(rows - 1):
            for col in range(cols):
                self.forces_table_data[(row, col)] = self.forces_table.item(row, col).text()

    def bars_table_cell_changed(self):
        current_item = self.bars_table.currentItem()
        if current_item is None:
            return

        row = current_item.row()
        col = current_item.column()
        property_name = {
            0: 'E',
            1: 'L',
            2: 'A',
            3: 'S',
            4: 'q'
        }.get(col)

        if not is_float(current_item.text()):
            msg_box = QMessageBox(QMessageBox.Critical, "Ошибка",
                                  "Параметры стержня должны быть положительными вещественными числами!\n"
                                  "Распределенная нагрузка q должна быть вещественным числом!")
            msg_box.exec()

            if current_item.background() != QBrush(QColor(*Color.light_yellow)):
                old_value = self.bar_construction.bars[row][property_name]
                item = QTableWidgetItem(str(old_value))
                self.bars_table.setItem(row, col, item)
                item.setTextAlignment(Qt.AlignCenter)
            return

        if col != self.bars_table.columnCount() - 1 and float(current_item.text()) <= 0:
            msg_box = QMessageBox(QMessageBox.Critical, "Ошибка",
                                  "Параметры стержня должны быть положительными вещественными числами!\n"
                                  "Распределенная нагрузка q должна быть вещественным числом!")
            msg_box.exec()
            if current_item.background() != QBrush(QColor(*Color.light_yellow)):
                old_value = self.bar_construction.bars[row][property_name]
                item = QTableWidgetItem(str(old_value))
                self.bars_table.setItem(row, col, item)
                item.setTextAlignment(Qt.AlignCenter)
            return

        if current_item.background() != QBrush(QColor(*Color.light_yellow)):
            self.bar_construction.bars[row][property_name] = float(current_item.text())

    def add_bar_btn_clicked(self):
        if self.bar_properties_correct():
            last_row = self.bars_table.rowCount() - 1
            cols = self.bars_table.columnCount()
            properties = {
                self.bars_table.horizontalHeaderItem(col).text(): float(self.bars_table.item(last_row, col).text())
                for col in range(cols)}
            self.bar_construction.add_bar(properties)
            self.bars_table.insertRow(last_row + 1)
            for col in range(cols - 1):
                bar_property = QTableWidgetItem("1")
                self.bars_table.setItem(last_row + 1, col, bar_property)
            self.bars_table.setItem(last_row + 1, cols - 1, QTableWidgetItem("0"))
            self.set_table_items_alignment(self.bars_table)
            self.set_table_cell_color(self.bars_table, Color.white, last_row)
            self.set_table_cell_color(self.bars_table, Color.light_yellow, last_row + 1)

    def del_bar_btn_clicked(self):
        bar_n = len(self.bar_construction.bars)
        if self.bars_table.rowCount() >= 2:
            last_row = self.bars_table.rowCount()
            if last_row - 2 >= 0:
                self.bars_table.removeRow(last_row - 2)
                self.bar_construction.del_bar()

        rows = self.forces_table.rowCount()
        for row in range(rows - 1):
            item = self.forces_table.item(row, 0).text()
            if int(item) == bar_n + 1:
                self.force_deleted_by_btn = True
                self.forces_table.removeRow(row)
                break

        rows = self.forces_table.rowCount()
        cols = self.forces_table.columnCount()
        self.forces_table_data.clear()
        for row in range(rows - 1):
            for col in range(cols):
                self.forces_table_data[(row, col)] = self.forces_table.item(row, col).text()

        if bar_n - 1 == 0 and self.forces_table.item(0, 0).background() != QBrush(QColor(*Color.light_yellow)):
            self.forces_table.removeRow(0)

    def add_force_btn_clicked(self):
        if self.forces_correct():
            last_row = self.forces_table.rowCount() - 1
            node = int(self.forces_table.item(last_row, 0).text())
            force_value = float(self.forces_table.item(last_row, 1).text())
            self.bar_construction.change_force(node, force_value)
            print(self.bar_construction.forces)
            self.forces_table.insertRow(last_row + 1)
            for col in range(self.forces_table.columnCount()):
                item = QTableWidgetItem("-")
                self.forces_table.setItem(last_row + 1, col, item)
            self.set_table_items_alignment(self.forces_table)
            self.set_table_cell_color(self.forces_table, Color.white, last_row)
            self.set_table_cell_color(self.forces_table, Color.light_yellow, last_row + 1)

            rows = self.forces_table.rowCount()
            cols = self.forces_table.columnCount()
            self.forces_table_data.clear()
            for row in range(rows - 1):
                for col in range(cols):
                    self.forces_table_data[(row, col)] = self.forces_table.item(row, col).text()

    def bar_properties_correct(self) -> bool:
        rows = self.bars_table.rowCount()
        cols = self.bars_table.columnCount()
        try:
            for row in range(rows):
                for col in range(cols):
                    item = self.bars_table.item(row, col)
                    if not item:
                        raise ValueError
                    item = float(item.text())
                    if col != cols - 1 and item <= 0:
                        raise ValueError
            return True
        except ValueError:
            error = "Параметры стержня должны быть положительными вещественными числами!\n" \
                    "Распределенная нагрузка q должна быть вещественным числом!"
            msg_box = QMessageBox(QMessageBox.Critical, "Ошибка", error)
            msg_box.exec()
            return False

    def forces_correct(self) -> bool:
        if len(self.bar_construction.bars) == 0:
            msg_box = QMessageBox(QMessageBox.Critical, "Ошибка", "Сначала нужно добавить хотя бы один стержень!")
            msg_box.exec_()
            return False
        errors = {
            "invalid literal for int() with base 10": "Номер узла должен быть целым положительным числом!",
            "could not convert string to float": "Значение нагрузки должно быть вещественным числом!"
        }
        last_row = self.forces_table.rowCount() - 1
        try:
            node = int(self.forces_table.item(last_row, 0).text())
            if node > len(self.bar_construction.forces):
                raise ValueError("Введенный номер узла выходит за границы конструкции!")
            if node <= 0:
                raise ValueError("Номер узла должен быть целым положительным числом!")
            if self.bar_construction.forces[node - 1] != 0:
                raise ValueError(f"Нагрузка на узел №{node} уже была добавлена ранее!")
            _ = float(self.forces_table.item(last_row, 1).text())
            return True
        except ValueError as error:
            error = str(error).split(':')[0]
            if error in errors:
                msg_box = QMessageBox(QMessageBox.Critical, "Ошибка", errors[error])
            else:
                msg_box = QMessageBox(QMessageBox.Critical, "Ошибка", error)
            msg_box.exec()
            return False


if __name__ == '__main__':
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(application.exec_())
