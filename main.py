import sys
import os
import hashlib
import sqlite3
import random
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QComboBox,
    QLineEdit, QMessageBox, QDialog, QFormLayout, QSpinBox, QFileDialog,
    QHeaderView
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QPolygon, QPixmap


# ==================== ЗАДАНИЕ 1: Результаты олимпиады = = = = = = = = = = = = = = = = = = = =
class OlympicWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №1: Результаты олимпиады")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        self.school_combo = QComboBox()
        self.class_combo = QComboBox()

        filter_layout.addWidget(QLabel("Школа:"))
        filter_layout.addWidget(self.school_combo)
        filter_layout.addWidget(QLabel("Класс:"))
        filter_layout.addWidget(self.class_combo)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.load_data()

        self.school_combo.currentIndexChanged.connect(self.apply_filter)
        self.class_combo.currentIndexChanged.connect(self.apply_filter)

    def load_data(self):
        try:
            self.df = pd.read_csv('rez.csv')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить rez.csv: {e}")
            return

        schools = set()
        classes = set()
        parsed_schools = []
        parsed_classes = []

        for login in self.df['login']:
            parts = str(login).split('-')
            if len(parts) >= 5:
                sch = parts[2]
                cl = parts[3]
                parsed_schools.append(sch)
                parsed_classes.append(cl)
                schools.add(sch)
                classes.add(cl)
            else:
                parsed_schools.append("")
                parsed_classes.append("")

        self.df['school'] = parsed_schools
        self.df['class_num'] = parsed_classes

        self.school_combo.clear()
        self.school_combo.addItem("Все школы", "")
        for s in sorted(list(schools)):
            self.school_combo.addItem(s, s)

        self.class_combo.clear()
        self.class_combo.addItem("Все классы", "")
        for c in sorted(list(classes)):
            self.class_combo.addItem(c, c)

        self.apply_filter()

    def apply_filter(self):
        sch_filter = self.school_combo.currentData()
        cl_filter = self.class_combo.currentData()

        filtered = self.df.copy()
        if sch_filter:
            filtered = filtered[filtered['school'] == sch_filter]
        if cl_filter:
            filtered = filtered[filtered['class_num'] == cl_filter]

        display_df = filtered[['login', 'user_name', 'Score']].copy()
        display_df['Score'] = pd.to_numeric(display_df['Score'], errors='coerce').fillna(0)
        display_df = display_df.sort_values(by='Score', ascending=False).reset_index(drop=True)

        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Логин", "ФИО", "Суммарный балл"])

        scores = display_df['Score'].tolist()
        unique_scores = sorted(list(set(scores)), reverse=True)
        score_to_place = {score: idx + 1 for idx, score in enumerate(unique_scores)}
        places = [score_to_place[s] for s in scores]

        for row_idx, row in display_df.iterrows():
            place = places[row_idx]
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['login'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['user_name'])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row['Score'])))

            color = None
            if place == 1:
                color = QColor(255, 215, 0, 100)
            elif place == 2:
                color = QColor(192, 192, 192, 100)
            elif place == 3:
                color = QColor(205, 127, 50, 100)

            if color:
                for col in range(3):
                    self.table.item(row_idx, col).setBackground(color)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


# ==================== ЗАДАНИЕ 2: Фильмы (SQLite) = = = = = = = = = = = = = = = = = = = =
class FilmEditDialog(QDialog):
    def __init__(self, parent=None, film_data=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование фильма" if film_data else "Добавление фильма")
        self.resize(300, 200)

        layout = QFormLayout(self)

        self.title_input = QLineEdit()
        self.year_input = QSpinBox()
        self.year_input.setRange(1800, 2100)
        self.genre_combo = QComboBox()
        self.duration_input = QSpinBox()
        self.duration_input.setRange(-1000, 1000)

        conn = sqlite3.connect('films_db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM genres")
        self.genres = cursor.fetchall()
        conn.close()

        for g_id, g_title in self.genres:
            self.genre_combo.addItem(g_title, g_id)

        layout.addRow("Название:", self.title_input)
        layout.addRow("Год:", self.year_input)
        layout.addRow("Жанр:", self.genre_combo)
        layout.addRow("Длительность (мин):", self.duration_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)

        if film_data:
            self.film_id = film_data[0]
            self.title_input.setText(str(film_data[1]))
            self.year_input.setValue(int(film_data[2]) if film_data[2] else 2000)
            for i in range(self.genre_combo.count()):
                if self.genre_combo.itemData(i) == film_data[3]:
                    self.genre_combo.setCurrentIndex(i)
            self.duration_input.setValue(int(film_data[4]) if film_data[4] else 90)
        else:
            self.film_id = None
            self.year_input.setValue(2023)
            self.duration_input.setValue(90)

    def validate_and_accept(self):
        title = self.title_input.text().strip()
        year = self.year_input.value()
        duration = self.duration_input.value()

        if not title:
            QMessageBox.warning(self, "Ошибка ввода", "Название фильма не может быть пустым!")
            return
        if year > 2026:
            QMessageBox.warning(self, "Ошибка ввода",
                                f"Год выпуска ({year}) не может быть в будущем (больше 2026 года)!")
            return
        if duration <= 0:
            QMessageBox.warning(self, "Ошибка ввода",
                                f"Длительность фильма должна быть положительным числом (указано: {duration})!")
            return

        self.accept()

    def get_data(self):
        return (
            self.title_input.text().strip(),
            self.year_input.value(),
            self.genre_combo.currentData(),
            self.duration_input.value()
        )


class FilmsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №2: Каталог фильмов (SQLite)")
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        edit_btn = QPushButton("Изменить")
        del_btn = QPushButton("Удалить")
        refresh_btn = QPushButton("Обновить")

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        add_btn.clicked.connect(self.add_film)
        edit_btn.clicked.connect(self.edit_film)
        del_btn.clicked.connect(self.delete_film)
        refresh_btn.clicked.connect(self.load_data)

        self.load_data()

    def load_data(self):
        try:
            self.conn = sqlite3.connect('films_db.sqlite')
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT f.id, f.title, f.year, g.title as genre_title, f.duration, f.genre 
                FROM films f 
                LEFT JOIN genres g ON f.genre = g.id
            """)
            rows = cursor.fetchall()

            header_labels = ["ID", "Название", "Год", "Жанр", "Длительность (мин)", "genre_id"]

            self.table.setColumnCount(len(header_labels))
            self.table.setHorizontalHeaderLabels(header_labels)
            self.table.setColumnHidden(5, True)

            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, val in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val if val is not None else '')))

            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))

    def add_film(self):
        dlg = FilmEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                conn = sqlite3.connect('films_db.sqlite')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO films (title, year, genre, duration) VALUES (?, ?, ?, ?)", data)
                conn.commit()
                conn.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))

    def edit_film(self):
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Внимание",
                                "Не выбрана запись для редактирования! Пожалуйста, выделите строку в таблице.")
            return

        selected = self.table.currentRow()
        film_id = int(self.table.item(selected, 0).text())
        title = self.table.item(selected, 1).text()
        year = self.table.item(selected, 2).text()
        duration = self.table.item(selected, 4).text()
        genre_id = int(self.table.item(selected, 5).text() or 1)

        film_data = (film_id, title, int(year) if year else 2000, genre_id, int(duration) if duration else 90)

        dlg = FilmEditDialog(self, film_data)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                conn = sqlite3.connect('films_db.sqlite')
                cursor = conn.cursor()
                cursor.execute("UPDATE films SET title=?, year=?, genre=?, duration=? WHERE id=?",
                               (data[0], data[1], data[2], data[3], film_id))
                conn.commit()
                conn.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))

    def delete_film(self):
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Внимание",
                                "Не выбрана запись для удаления! Пожалуйста, выделите строку в таблице.")
            return

        selected = self.table.currentRow()
        film_id = int(self.table.item(selected, 0).text())
        reply = QMessageBox.question(self, "Подтверждение", "Вы действительно хотите удалить выбранный фильм?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect('films_db.sqlite')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM films WHERE id=?", (film_id,))
                conn.commit()
                conn.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))


# ==================== ЗАДАНИЕ 3: Рисование фигур = = = = = = = = = = = = = = = = = = = =
class ShapesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №3: Рисование фигур")
        self.resize(700, 500)
        self.shapes = []
        self.last_mouse_pos = QPoint(100, 100)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def mouseMoveEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mousePressEvent(self, event):
        pos = event.pos()
        size = random.randint(30, 80)
        color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if event.button() == Qt.LeftButton:
            self.shapes.append(('circle', pos.x(), pos.y(), size, color))
            self.update()
        elif event.button() == Qt.RightButton:
            self.shapes.append(('square', pos.x(), pos.y(), size, color))
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            size = random.randint(30, 80)
            color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            x = self.last_mouse_pos.x()
            y = self.last_mouse_pos.y()
            self.shapes.append(('triangle', x, y, size, color))
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        for shape_type, x, y, size, color in self.shapes:
            painter.setBrush(color)
            if shape_type == 'circle':
                painter.drawEllipse(x - size // 2, y - size // 2, size, size)
            elif shape_type == 'square':
                painter.drawRect(x - size // 2, y - size // 2, size, size)
            elif shape_type == 'triangle':
                poly = QPolygon([
                    QPoint(x, y - size // 2),
                    QPoint(x - size // 2, y + size // 2),
                    QPoint(x + size // 2, y + size // 2)
                ])
                painter.drawPolygon(poly)


# ==================== ЗАДАНИЕ 4: Убегающая кнопка = = = = = = = = = = = = = = = = = = = =
class EscapeButtonWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №4: Убегающая кнопка")
        self.resize(600, 400)

        self.btn = QPushButton("Нажми меня!", self)
        self.btn.setGeometry(250, 180, 100, 40)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        mouse_pos = event.pos()
        btn_rect = self.btn.geometry()

        if btn_rect.contains(mouse_pos) or (
                abs(mouse_pos.x() - (btn_rect.x() + btn_rect.width() / 2)) < 70 and
                abs(mouse_pos.y() - (btn_rect.y() + btn_rect.height() / 2)) < 70
        ):
            new_x = random.randint(10, max(10, self.width() - self.btn.width() - 10))
            new_y = random.randint(10, max(10, self.height() - self.btn.height() - 10))
            self.btn.move(new_x, new_y)


# ==================== ЗАДАНИЕ 5: Управление НЛО = = = = = = = = = = = = = = = = = = = =
class UFOWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №5: Управление НЛО")
        self.resize(700, 500)
        self.ufo_x = 320
        self.ufo_y = 220
        self.step = 20
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.ufo_x -= self.step
        elif event.key() == Qt.Key_Right:
            self.ufo_x += self.step
        elif event.key() == Qt.Key_Up:
            self.ufo_y -= self.step
        elif event.key() == Qt.Key_Down:
            self.ufo_y += self.step

        if self.ufo_x < -40:
            self.ufo_x = self.width()
        elif self.ufo_x > self.width():
            self.ufo_x = -40

        if self.ufo_y < -40:
            self.ufo_y = self.height()
        elif self.ufo_y > self.height():
            self.ufo_y = -40

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(100, 200, 255))
        painter.drawEllipse(self.ufo_x + 15, self.ufo_y, 30, 20)
        painter.setBrush(QColor(150, 150, 150))
        painter.drawEllipse(self.ufo_x, self.ufo_y + 10, 60, 20)
        painter.setBrush(QColor(255, 255, 0))
        painter.drawEllipse(self.ufo_x + 25, self.ufo_y + 15, 10, 10)


# ==================== ЗАДАНИЕ 6: Каталог библиотеки = = = = = = = = = = = = = = = = = = = =
class AuthWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация / Регистрация")
        self.resize(300, 200)

        self.init_db()

        layout = QFormLayout(self)
        self.login_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", self.pass_input)

        login_btn = QPushButton("Войти")
        register_btn = QPushButton("Зарегистрироваться")

        layout.addRow(login_btn, register_btn)

        login_btn.clicked.connect(self.handle_login)
        register_btn.clicked.connect(self.handle_register)

        self.authenticated = False

    def init_db(self):
        conn = sqlite3.connect('library.sqlite')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE,
                password_hash TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT,
                author TEXT,
                year INTEGER,
                genre TEXT,
                image_path TEXT
            )
        """)
        conn.commit()
        conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def handle_login(self):
        login = self.login_input.text().strip()
        password = self.pass_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        conn = sqlite3.connect('library.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE login=?", (login,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0] == self.hash_password(password):
            self.authenticated = True
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")

    def handle_register(self):
        login = self.login_input.text().strip()
        password = self.pass_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        try:
            conn = sqlite3.connect('library.sqlite')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (login, password_hash) VALUES (?, ?)",
                           (login, self.hash_password(password)))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно! Теперь вы можете войти.")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Такой логин уже существует.")


class BookEditDialog(QDialog):
    def __init__(self, parent=None, book_data=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование книги" if book_data else "Добавление книги")
        self.resize(350, 250)

        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.year_input = QSpinBox()
        self.year_input.setRange(1000, 2100)
        self.genre_input = QLineEdit()

        img_layout = QHBoxLayout()
        self.img_path_input = QLineEdit()
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_image)
        img_layout.addWidget(self.img_path_input)
        img_layout.addWidget(browse_btn)

        layout.addRow("Название:", self.title_input)
        layout.addRow("Автор:", self.author_input)
        layout.addRow("Год издания:", self.year_input)
        layout.addRow("Жанр:", self.genre_input)
        layout.addRow("Картинка:", img_layout)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        if book_data:
            self.title_input.setText(book_data[1])
            self.author_input.setText(book_data[2])
            self.year_input.setValue(book_data[3] if book_data[3] else 2000)
            self.genre_input.setText(book_data[4])
            self.img_path_input.setText(book_data[5] if book_data[5] else "")

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.img_path_input.setText(path)

    def get_data(self):
        return (
            self.title_input.text().strip(),
            self.author_input.text().strip(),
            self.year_input.value(),
            self.genre_input.text().strip(),
            self.img_path_input.text().strip()
        )


class BookDetailDialog(QDialog):
    def __init__(self, parent=None, book_data=None):
        super().__init__(parent)
        self.setWindowTitle("Информация о книге")
        self.resize(450, 400)

        layout = QHBoxLayout(self)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setFixedSize(180, 240)
        img_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")

        img_path = book_data[5] if book_data and len(book_data) > 5 else ""
        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            img_label.setPixmap(pixmap.scaled(180, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText("Нет изображения\n(заглушка)")

        layout.addWidget(img_label)

        info_layout = QVBoxLayout()

        title_text = f"<b>Название:</b> {book_data[1]}"
        author_text = f"<b>Автор:</b> {book_data[2]}"
        year_text = f"<b>Год издания:</b> {book_data[3]}"
        genre_text = f"<b>Жанр:</b> {book_data[4]}"

        lbl_title = QLabel(title_text)
        lbl_title.setWordWrap(True)
        lbl_author = QLabel(author_text)
        lbl_year = QLabel(year_text)
        lbl_genre = QLabel(genre_text)

        for lbl in [lbl_title, lbl_author, lbl_year, lbl_genre]:
            lbl.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
            info_layout.addWidget(lbl)

        info_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        info_layout.addWidget(close_btn)

        layout.addLayout(info_layout)


class LibraryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Задание №6: Каталог библиотеки")
        self.resize(950, 600)

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_author_input = QLineEdit()
        self.search_author_input.setPlaceholderText("Поиск по автору...")
        self.search_title_input = QLineEdit()
        self.search_title_input.setPlaceholderText("Поиск по названию...")
        search_btn = QPushButton("Искать")
        reset_btn = QPushButton("Сбросить")

        search_layout.addWidget(self.search_author_input)
        search_layout.addWidget(self.search_title_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(reset_btn)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self.show_book_details)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        view_btn = QPushButton("Просмотр (Описание и фото)")
        add_btn = QPushButton("Добавить книгу")
        edit_btn = QPushButton("Изменить")
        del_btn = QPushButton("Удалить")

        btn_layout.addWidget(view_btn)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)

        search_btn.clicked.connect(self.load_data)
        reset_btn.clicked.connect(self.reset_search)
        view_btn.clicked.connect(self.show_book_details)
        add_btn.clicked.connect(self.add_book)
        edit_btn.clicked.connect(self.edit_book)
        del_btn.clicked.connect(self.delete_book)

        self.load_data()

    def reset_search(self):
        self.search_author_input.clear()
        self.search_title_input.clear()
        self.load_data()

    def load_data(self):
        author_q = self.search_author_input.text().strip().lower()
        title_q = self.search_title_input.text().strip().lower()

        conn = sqlite3.connect('library.sqlite')
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, author, year, genre, image_path FROM books ORDER BY id ASC")
        all_rows = cursor.fetchall()
        conn.close()

        rows = []
        for row in all_rows:
            book_id, title, author, year, genre, image_path = row
            match_author = True
            match_title = True

            if author_q:
                if not author or not author.lower().startswith(author_q):
                    match_author = False
            if title_q:
                if not title or not title.lower().startswith(title_q):
                    match_title = False

            if match_author and match_title:
                rows.append(row)

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Автор", "Год", "Жанр", "Путь к картинке"])
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx, val in enumerate(row):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(val if val is not None else 'Нет картинки')))

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_book_details(self):
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Внимание", "Выберите книгу в таблице для просмотра!")
            return

        selected = self.table.currentRow()
        book_id = int(self.table.item(selected, 0).text())
        title = self.table.item(selected, 1).text()
        author = self.table.item(selected, 2).text()
        year = int(self.table.item(selected, 3).text() or 2000)
        genre = self.table.item(selected, 4).text()
        img_path = self.table.item(selected, 5).text()

        book_data = (book_id, title, author, year, genre, img_path)
        dlg = BookDetailDialog(self, book_data)
        dlg.exec_()

    def add_book(self):
        dlg = BookEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                conn = sqlite3.connect('library.sqlite')
                cursor = conn.cursor()

                # Находим минимальный свободный ID, начиная с 1
                cursor.execute("SELECT id FROM books ORDER BY id ASC")
                existing_ids = [row[0] for row in cursor.fetchall()]

                new_id = 1
                for i in existing_ids:
                    if i == new_id:
                        new_id += 1
                    else:
                        break

                cursor.execute(
                    "INSERT INTO books (id, title, author, year, genre, image_path) VALUES (?, ?, ?, ?, ?, ?)",
                    (new_id, data[0], data[1], data[2], data[3], data[4])
                )
                conn.commit()
                conn.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))

    def edit_book(self):
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Внимание", "Выберите книгу для редактирования.")
            return

        selected = self.table.currentRow()
        book_id = int(self.table.item(selected, 0).text())
        title = self.table.item(selected, 1).text()
        author = self.table.item(selected, 2).text()
        year = int(self.table.item(selected, 3).text() or 2000)
        genre = self.table.item(selected, 4).text()
        img_path = self.table.item(selected, 5).text()

        book_data = (book_id, title, author, year, genre, img_path)
        dlg = BookEditDialog(self, book_data)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            conn = sqlite3.connect('library.sqlite')
            cursor = conn.cursor()
            cursor.execute("UPDATE books SET title=?, author=?, year=?, genre=?, image_path=? WHERE id=?",
                           (data[0], data[1], data[2], data[3], data[4], book_id))
            conn.commit()
            conn.close()
            self.load_data()

    def delete_book(self):
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Внимание", "Выберите книгу для удаления.")
            return

        selected = self.table.currentRow()
        book_id = int(self.table.item(selected, 0).text())
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранную книгу?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect('library.sqlite')
                cursor = conn.cursor()

                # 1. Удаляем выбранную книгу
                cursor.execute("DELETE FROM books WHERE id=?", (book_id,))

                # 2. Безопасно сдвигаем ID всех оставшихся книг (у которых ID больше удаленного) на 1 назад через UPDATE
                cursor.execute("UPDATE books SET id = id - 1 WHERE id > ?", (book_id,))

                conn.commit()
                conn.close()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))


# ==================== ГЛАВНОЕ МЕНЮ ПРИЛОЖЕНИЯ = = = = = = = = = = = = = = = = = = = =
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №4 — Все задания")
        self.resize(400, 350)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel("Выберите лабораторное задание:")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        btn1 = QPushButton("Задание №1: Олимпиада (CSV)")
        btn2 = QPushButton("Задание №2: Каталог фильмов (SQLite)")
        btn3 = QPushButton("Задание №3: Рисование фигур")
        btn4 = QPushButton("Задание №4: Убегающая кнопка")
        btn5 = QPushButton("Задание №5: Управление НЛО")
        btn6 = QPushButton("Задание №6: Каталог библиотеки (Авторизация)")

        for btn in [btn1, btn2, btn3, btn4, btn5, btn6]:
            btn.setStyleSheet("padding: 8px; font-size: 12px;")
            layout.addWidget(btn)

        btn1.clicked.connect(self.open_task1)
        btn2.clicked.connect(self.open_task2)
        btn3.clicked.connect(self.open_task3)
        btn4.clicked.connect(self.open_task4)
        btn5.clicked.connect(self.open_task5)
        btn6.clicked.connect(self.open_task6)

    def open_task1(self):
        self.w1 = OlympicWindow()
        self.w1.show()

    def open_task2(self):
        self.w2 = FilmsWindow()
        self.w2.show()

    def open_task3(self):
        self.w3 = ShapesWindow()
        self.w3.show()

    def open_task4(self):
        self.w4 = EscapeButtonWindow()
        self.w4.show()

    def open_task5(self):
        self.w5 = UFOWindow()
        self.w5.show()

    def open_task6(self):
        auth = AuthWindow()
        if auth.exec_() == QDialog.Accepted and auth.authenticated:
            self.w6 = LibraryWindow()
            self.w6.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_menu = MainWindow()
    main_menu.show()
    sys.exit(app.exec_())