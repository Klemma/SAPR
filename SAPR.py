import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QMessageBox, QTableWidget, QFileDialog, \
    QGraphicsScene, QGraphicsRectItem, QGraphicsItemGroup, QGraphicsLineItem

from BarConstruction import BarConstruction
from Colors import Color
from ConstructionItems import ConstructionItems
from gui import Ui_MainWindow


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


def take_piece(value: float, percent: float):
    return value * percent / 100


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.bar_construction = BarConstruction()
        self.opening_project_file = False
        self.force_deleted_by_btn = False
        self.changed_table_item_style = False
        self.forces_table_data = {}
        self.canvas = QGraphicsScene()
        self.figure_view.setScene(self.canvas)
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

    def redraw_nodal_forces(self):
        drawn_nodal_forces = [force for force in self.canvas.items()
                              if force.data(ConstructionItems.NODAL_FORCE.value) is not None]

        for drawn_force in drawn_nodal_forces:
            self.canvas.removeItem(drawn_force)

        bars = [bar for bar in self.canvas.items() if type(bar) is QGraphicsRectItem]
        if len(bars) == 0:
            return

        nodal_forces = [(i, force) for i, force in enumerate(self.bar_construction.forces) if force != 0]
        if len(nodal_forces) == 0:
            return

        nodal_force_pen = QPen(QColor("red"), 3.5)
        bars.reverse()
        offset_x = 4.5
        for i, force in nodal_forces:
            if len(bars) == i:
                bar = bars[i - 1]
            else:
                bar = bars[i]
            bar_width = bar.boundingRect().width() - 3
            bar_height = bar.boundingRect().height() - 3
            nodal_force = QGraphicsItemGroup()
            nodal_force.setData(ConstructionItems.NODAL_FORCE.value, i)
            nodal_force.setToolTip(f"{force} [Н]")

            y1 = bar.boundingRect().center().y()
            y2 = y1
            if len(bars) != i:
                x1 = bar.boundingRect().left() + offset_x
                x2 = x1 + take_piece(bar_width, 100/3)
                body = QGraphicsLineItem(x1, y1, x2, y2)
                body.setPen(nodal_force_pen)
                nodal_force.addToGroup(body)
                y2 = {"top": y1 - take_piece(bar_height, 15),
                      "bottom": y1 + take_piece(bar_height, 15)}
                if force > 0:
                    x1 = x2
                    x2 = x1 - take_piece(bar_width, 7.5)
                else:
                    x2 = x1 + take_piece(bar_width, 7.5)
            else:
                x1 = bar.boundingRect().right() - offset_x
                x2 = x1 - take_piece(bar_width, 100/3)
                body = QGraphicsLineItem(x1, y1, x2, y2)
                body.setPen(nodal_force_pen)
                nodal_force.addToGroup(body)
                y2 = {"top": y1 - take_piece(bar_height, 15),
                      "bottom": y1 + take_piece(bar_height, 15)}
                if force > 0:
                    x2 = x1 - take_piece(bar_width, 7.5)
                else:
                    x1 = x2
                    x2 = x1 + take_piece(bar_width, 7.5)

            top_part = QGraphicsLineItem(x1, y1, x2, y2["top"])
            top_part.setPen(nodal_force_pen)
            nodal_force.addToGroup(top_part)
            bottom_part = QGraphicsLineItem(x1, y1, x2, y2["bottom"])
            bottom_part.setPen(nodal_force_pen)
            nodal_force.addToGroup(bottom_part)

            self.canvas.addItem(nodal_force)

    def redraw_bar_forces(self):
        drawn_bar_forces = [force for force in self.canvas.items()
                            if force.data(ConstructionItems.BAR_FORCE.value) is not None]

        for drawn_force in drawn_bar_forces:
            self.canvas.removeItem(drawn_force)

        bars = [bar for bar in self.canvas.items() if type(bar) is QGraphicsRectItem]
        if len(bars) == 0:
            return

        bar_forces = [(i, param['q']) for i, param in enumerate(self.bar_construction.bars) if param['q'] != 0]
        if len(bar_forces) == 0:
            return

        bar_force_pen = QPen(QColor(*Color.cyan), 3)
        heads_count = 4
        bars.reverse()
        offset_x = 4.5
        for i, force in bar_forces:
            bar = bars[i]
            bar_width = bar.boundingRect().width() - 3
            bar_height = bar.boundingRect().height() - 3
            bar_force = QGraphicsItemGroup()
            bar_force.setData(ConstructionItems.BAR_FORCE.value, i)
            bar_force.setToolTip(f"{force} [Н/м]")

            x1 = bar.boundingRect().left() + offset_x
            y1 = bar.boundingRect().center().y()
            x2 = bar.boundingRect().right() - offset_x
            y2 = y1
            body = QGraphicsLineItem(x1, y1, x2, y2)
            body.setPen(bar_force_pen)
            bar_force.addToGroup(body)

            x_diff = bar_width / heads_count
            y2 = {"top": y1 - take_piece(bar_height, 10),
                  "bottom": y1 + take_piece(bar_height, 10)}
            x1 = bar.boundingRect().left() if force > 0 else bar.boundingRect().right()
            for j in range(1, heads_count + 1):
                if force > 0:
                    x1 += x_diff
                    x2 = x1 - take_piece(bar_width, 5)
                else:
                    x1 -= x_diff
                    x2 = x1 + take_piece(bar_width, 5)
                top_part = QGraphicsLineItem(x1, y1, x2, y2["top"])
                top_part.setPen(bar_force_pen)
                bar_force.addToGroup(top_part)
                bottom_part = QGraphicsLineItem(x1, y1, x2, y2["bottom"])
                bottom_part.setPen(bar_force_pen)
                bar_force.addToGroup(bottom_part)

            self.canvas.addItem(bar_force)

    def redraw_terminations(self):
        terminations = [termination for termination in self.canvas.items()
                        if termination.data(ConstructionItems.LEFT_TERMINATION.value) is True
                        or termination.data(ConstructionItems.RIGHT_TERMINATION.value) is True]
        if len(terminations) > 0:
            for termination in terminations:
                self.canvas.removeItem(termination)

        bars = [bar for bar in self.canvas.items() if type(bar) is QGraphicsRectItem]
        if len(bars) == 0:
            return

        diag_lines_count = 6
        line_pen = QPen(QColor("black"), 3)

        def draw_left():
            left_bar = bars[-1]
            bar_width = left_bar.boundingRect().width()
            bar_height = left_bar.boundingRect().height()
            left_termination = QGraphicsItemGroup()
            left_termination.setData(ConstructionItems.LEFT_TERMINATION.value, True)
            pos1 = left_bar.boundingRect().topLeft()
            pos2 = left_bar.boundingRect().bottomLeft()
            v_line = QGraphicsLineItem(pos1.x() + 1.5, pos1.y() - take_piece(bar_height, 5),
                                       pos2.x() + 1.5, pos2.y() + take_piece(bar_height, 5))
            v_line.setPen(line_pen)
            left_termination.addToGroup(v_line)

            x1 = v_line.boundingRect().topLeft().x() + 1.5
            x2 = v_line.boundingRect().topLeft().x() - take_piece(bar_height, 10) + 1.5
            for i in range(diag_lines_count + 1):
                y_diff = v_line.boundingRect().height() / diag_lines_count
                y1 = v_line.boundingRect().topLeft().y() + i * y_diff
                y2 = y1 + take_piece(bar_width, 5)
                diag_line = QGraphicsLineItem(x1, y1, x2, y2)
                diag_line.setPen(line_pen)
                left_termination.addToGroup(diag_line)
            self.canvas.addItem(left_termination)

        def draw_right():
            right_bar = bars[0]
            bar_width = right_bar.boundingRect().width()
            bar_height = right_bar.boundingRect().height()
            right_termination = QGraphicsItemGroup()
            right_termination.setData(ConstructionItems.RIGHT_TERMINATION.value, True)
            pos1 = right_bar.boundingRect().topRight()
            pos2 = right_bar.boundingRect().bottomRight()
            v_line = QGraphicsLineItem(pos1.x() - 1.5, pos1.y() - take_piece(bar_height, 5),
                                       pos2.x() - 1.5, pos2.y() + take_piece(bar_height, 5))
            v_line.setPen(line_pen)
            right_termination.addToGroup(v_line)

            x1 = v_line.boundingRect().topRight().x()
            x2 = v_line.boundingRect().topRight().x() + take_piece(bar_height, 10)
            for i in range(diag_lines_count + 1):
                y_diff = v_line.boundingRect().height() / diag_lines_count
                y1 = v_line.boundingRect().topRight().y() + i * y_diff
                y2 = y1 - take_piece(bar_width, 5)
                diag_line = QGraphicsLineItem(x1, y1, x2, y2)
                diag_line.setPen(line_pen)
                right_termination.addToGroup(diag_line)
            self.canvas.addItem(right_termination)

        if self.left_termination.isChecked():
            draw_left()

        if self.right_termination.isChecked():
            draw_right()

        if self.both_terminations.isChecked():
            draw_left()
            draw_right()

    def draw_bar(self, n_bar=-1):
        bars = [bar for bar in self.canvas.items() if type(bar) is QGraphicsRectItem]
        bar_pen = QPen(QColor("black"), 3)
        bar_len = 200
        bar_height = 100
        bars_properties = [(i + 1, properties) for i, properties in enumerate(self.bar_construction.bars)]
        if len(bars) == 0:
            bar = QGraphicsRectItem(0, 0, bar_len, bar_height)
            bar.setPen(bar_pen)
            bar.setToolTip(f"Номер стержня: 1\n"
                           f"E = {bars_properties[0][1]['E']} [Па]\n"
                           f"L = {bars_properties[0][1]['L']} [м]\n"
                           f"A = {bars_properties[0][1]['A']} [м^2]\n"
                           f"S = {bars_properties[0][1]['S']} [Па]")
            self.canvas.addItem(bar)
        else:
            x = len(bars) * bar_len
            bar = QGraphicsRectItem(x, 0, bar_len, bar_height)
            bar.setPen(bar_pen)
            bar.setToolTip(f"Номер стержня: {bars_properties[n_bar][0]}\n"
                           f"E = {bars_properties[n_bar][1]['E']} [Па]\n"
                           f"L = {bars_properties[n_bar][1]['L']} [м]\n"
                           f"A = {bars_properties[n_bar][1]['A']} [м^2]\n"
                           f"S = {bars_properties[n_bar][1]['S']} [Па]")
            self.canvas.addItem(bar)

        if not self.opening_project_file:
            self.redraw_bar_forces()
            self.redraw_nodal_forces()
            self.redraw_terminations()

    def erase_bar(self):
        bars = [bar for bar in self.canvas.items() if type(bar) is QGraphicsRectItem]
        if len(bars) > 0:
            self.canvas.removeItem(bars[0])
        self.redraw_bar_forces()
        self.redraw_nodal_forces()
        self.redraw_terminations()

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

        self.canvas.clear()
        for i in range(len(self.bar_construction.bars)):
            self.draw_bar(i)
        self.redraw_bar_forces()
        self.redraw_nodal_forces()
        self.redraw_terminations()

        self.opening_project_file = False

    def terminations_btn_clicked(self):
        checked = self.terminations_btn_group.checkedButton().objectName()
        terminations_state = {
            "left_termination": {"left": True, "right": False},
            "both_terminations": {"left": True, "right": True},
            "right_termination": {"left": False, "right": True}
        }.get(checked)
        self.bar_construction.change_terminations(terminations_state)
        self.redraw_terminations()

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
                self.redraw_nodal_forces()

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
        self.redraw_nodal_forces()
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
            self.redraw_bar_forces()
            self.redraw_nodal_forces()

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
            self.draw_bar()

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

        self.erase_bar()

    def add_force_btn_clicked(self):
        if self.forces_correct():
            last_row = self.forces_table.rowCount() - 1
            node = int(self.forces_table.item(last_row, 0).text())
            force_value = float(self.forces_table.item(last_row, 1).text())
            self.bar_construction.change_force(node, force_value)
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
            self.redraw_nodal_forces()

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
