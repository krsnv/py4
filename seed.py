import sys
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

def setup_database():
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('shop.db')

    if not db.open():
        sys.exit(1)

    query = QSqlQuery()

    query.exec_('''CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL)''')

    query.exec_('''CREATE TABLE IF NOT EXISTS statuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL UNIQUE)''')

    query.exec_('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    status_id INTEGER,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY(category_id) REFERENCES categories(id),
                    FOREIGN KEY(status_id) REFERENCES statuses(id))''')

    query.exec_("INSERT OR IGNORE INTO categories (name) VALUES ('Всякое')")
    query.exec_("INSERT OR IGNORE INTO categories (name) VALUES ('Разное')")
    query.exec_("INSERT OR IGNORE INTO categories (name) VALUES ('Иногда бесполезное')")

    query.exec_("INSERT OR IGNORE INTO statuses (status) VALUES ('В продаже')")
    query.exec_("INSERT OR IGNORE INTO statuses (status) VALUES ('Закончился')")
    query.exec_("INSERT OR IGNORE INTO statuses (status) VALUES ('Не в продаже')")

    query.exec_("INSERT OR IGNORE INTO products (category_id, status_id, name, price) VALUES (1, 1, 'Товар один', 1000.0)")
    query.exec_("INSERT OR IGNORE INTO products (category_id, status_id, name, price) VALUES (2, 2, 'Товар другой', 20.0)")
    query.exec_("INSERT OR IGNORE INTO products (category_id, status_id, name, price) VALUES (3, 1, 'Еще один крутой товар с длинным именем', 50.0)")
    query.exec_("INSERT OR IGNORE INTO products (category_id, status_id, name, price) VALUES (1, 2, 'Классный товар', 500.0)")

if __name__ == "__main__":
    setup_database()
