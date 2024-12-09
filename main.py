import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QLabel,
    QTabWidget,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QDialogButtonBox,
)
from PyQt5.QtSql import (
    QSqlDatabase,
    QSqlRelationalTableModel,
    QSqlRelation,
    QSqlQuery,
    QSqlRelationalDelegate,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Мини-даркстор")
        self.setGeometry(100, 100, 1000, 600)

        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("shop.db")

        if not self.db.open():
            sys.exit(1)

        self.setupDatabase()

        self.model = QSqlRelationalTableModel(self)
        self.model.setTable("products")
        self.model.setEditStrategy(QSqlRelationalTableModel.OnFieldChange)
        self.model.setRelation(1, QSqlRelation("categories", "id", "name"))
        self.model.setRelation(2, QSqlRelation("statuses", "id", "status"))
        self.model.select()

        self.product_tab = QWidget()
        self.product_layout = QVBoxLayout()
        self.product_tab.setLayout(self.product_layout)

        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(QSqlRelationalDelegate(self.model))
        self.product_layout.addWidget(self.table_view)

        self.in_stock_label = QLabel("Продажа: 0")
        self.out_of_stock_label = QLabel("Закончилось: 0")
        self.product_layout.addWidget(self.in_stock_label)
        self.product_layout.addWidget(self.out_of_stock_label)

        self.tabs.addTab(self.product_tab, "Товары")

        self.status_tab = QWidget()
        self.status_layout = QVBoxLayout()
        self.status_tab.setLayout(self.status_layout)

        self.status_table = QTableWidget()
        self.status_table.setColumnCount(2)
        self.status_table.setHorizontalHeaderLabels(["Status ID", "Status"])
        self.status_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.status_table.setSelectionMode(QTableWidget.SingleSelection)
        self.status_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.status_table.cellDoubleClicked.connect(self.editStatus)
        self.status_layout.addWidget(self.status_table)

        self.crud_layout = QHBoxLayout()
        self.add_status_button = QPushButton("Добавить статус")
        self.add_status_button.clicked.connect(self.addStatus)
        self.edit_status_button = QPushButton("Редактировать")
        self.edit_status_button.clicked.connect(self.editStatus)
        self.delete_status_button = QPushButton("Удалить")
        self.delete_status_button.clicked.connect(self.deleteStatus)

        self.crud_layout.addWidget(self.add_status_button)
        self.crud_layout.addWidget(self.edit_status_button)
        self.crud_layout.addWidget(self.delete_status_button)

        self.status_layout.addLayout(self.crud_layout)

        self.tabs.addTab(self.status_tab, "Управление статусами товаров")

        self.updateSelectors()
        self.updateCounters()

        self.refreshStatusTable()

        self.model.dataChanged.connect(self.autoSaveProduct)
        self.model.dataChanged.connect(self.onProductStatusChanged)

    def setupDatabase(self):
        query = QSqlQuery()

        query.exec_(
            """CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL)"""
        )

        query.exec_(
            """CREATE TABLE IF NOT EXISTS statuses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        status TEXT NOT NULL UNIQUE)"""
        )

        query.exec_(
            """CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category_id INTEGER,
                        status_id INTEGER,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        FOREIGN KEY(category_id) REFERENCES categories(id),
                        FOREIGN KEY(status_id) REFERENCES statuses(id))"""
        )

    def addStatus(self):
        status_name, ok = self.showInputDialog("Добавить статус")
        if ok and status_name:
            query = QSqlQuery()
            query.prepare("INSERT INTO statuses (status) VALUES (:status)")
            query.bindValue(":status", status_name)
            if query.exec_():
                self.refreshStatusTable()
                self.updateSelectors()
                self.updateCounters()
            else:
                print("Упс, не удалось статус добавить")

    def editStatus(self, row=None):
        if row is None:
            row = self.status_table.currentRow()
        if row >= 0:
            status_id = int(self.status_table.item(row, 0).text())
            current_status = self.status_table.item(row, 1).text()
            new_status, ok = self.showInputDialog(
                "Редактирование статуса", initial_text=current_status
            )
            if ok and new_status:
                query = QSqlQuery()
                query.prepare("UPDATE statuses SET status = :status WHERE id = :id")
                query.bindValue(":status", new_status)
                query.bindValue(":id", status_id)
                if query.exec_():
                    self.refreshStatusTable()
                    self.updateSelectors()

                    self.model = QSqlRelationalTableModel(self)
                    self.model.setTable("products")
                    self.model.setEditStrategy(QSqlRelationalTableModel.OnFieldChange)
                    self.model.setRelation(1, QSqlRelation("categories", "id", "name"))
                    self.model.setRelation(2, QSqlRelation("statuses", "id", "status"))
                    self.model.select()
                    self.table_view.setModel(self.model)

                    self.updateCounters()
                else:
                    print("Упс!")

    def updateProductStatuses(self, old_status_id, new_status_name):
        query = QSqlQuery()
        query.prepare(
            "UPDATE products SET status_id = (SELECT id FROM statuses WHERE status = :new_status) WHERE status_id = :old_status"
        )
        query.bindValue(":new_status", new_status_name)
        query.bindValue(":old_status", old_status_id)
        if query.exec_():
            self.model.select()
            self.updateCounters()
        else:
            print("Не получилось обновить статусы у товаров")

    def deleteStatus(self):
        row = self.status_table.currentRow()
        if row >= 0:
            status_id = int(self.status_table.item(row, 0).text())
            query = QSqlQuery()
            query.prepare("DELETE FROM statuses WHERE id = :id")
            query.bindValue(":id", status_id)
            if query.exec_():
                self.refreshStatusTable()
                self.updateSelectors()
                self.updateCounters()
                self.updateProductStatusesOnDeletion(status_id)
            else:
                print("Не удается удалить статус")

    def updateProductStatusesOnDeletion(self, status_id):
        query = QSqlQuery()
        query.prepare(
            "UPDATE products SET status_id = (SELECT id FROM statuses WHERE status = 'Не в продаже') WHERE status_id = :status_id"
        )
        query.bindValue(":status_id", status_id)
        if query.exec_():
            self.model.select()
            self.updateCounters()
        else:
            print("Ошибка обновления статусов при удалении")

    def autoSaveProduct(self, index):
        if index.isValid():
            self.model.submitAll()
            self.updateCounters()

    def showInputDialog(self, title, initial_text=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        input_field = QLineEdit(dialog)
        input_field.setText(initial_text)
        layout.addWidget(input_field)
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog
        )
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            return input_field.text(), True
        return None, False

    def refreshStatusTable(self):
        query = QSqlQuery("SELECT * FROM statuses")
        self.status_table.setRowCount(0)
        row = 0
        while query.next():
            self.status_table.insertRow(row)
            self.status_table.setItem(row, 0, QTableWidgetItem(str(query.value(0))))
            self.status_table.setItem(row, 1, QTableWidgetItem(query.value(1)))
            row += 1

    def updateSelectors(self):
        self.model.setRelation(2, QSqlRelation("statuses", "id", "status"))
        self.model.select()

    def updateCounters(self):
        query = QSqlQuery(
            "SELECT COUNT(*) FROM products WHERE status_id = (SELECT id FROM statuses WHERE status = 'В продаже')"
        )
        if query.next():
            self.in_stock_label.setText(f"В продаже: {query.value(0)}")

        query = QSqlQuery(
            "SELECT COUNT(*) FROM products WHERE status_id = (SELECT id FROM statuses WHERE status = 'Не в продаже')"
        )
        if query.next():
            self.out_of_stock_label.setText(f"Не в продаже: {query.value(0)}")

    def onProductStatusChanged(self, topLeft, bottomRight):
        if topLeft.column() == 2:
            self.updateCounters()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
