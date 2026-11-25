"""Run with: python pyqt/main.py (requires PyQt6)."""
import copy
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)
from store import TaskStore


class TodoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Everyday · To-do")
        self.resize(720, 640)
        self.setMinimumSize(480, 400)
        self.store = TaskStore()
        try:
            self.store.load()
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Cannot open saved tasks", f"{error}\n\nFile: {self.store.path}\nThe file has not been changed. The app will now close.")
            raise SystemExit(1)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(16)
        eyebrow = QLabel("MAKE ROOM FOR WHAT MATTERS")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("My tasks")
        title.setObjectName("heading")
        layout.addWidget(title)
        self.summary = QLabel()
        layout.addWidget(self.summary)

        add_row = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("What needs to get done?")
        self.entry.setAccessibleName("New task")
        self.entry.setMaxLength(1000)
        self.entry.returnPressed.connect(self.add_task)
        add_row.addWidget(self.entry, 1)
        add = QPushButton("+ Add task")
        add.setObjectName("primary")
        add.clicked.connect(self.add_task)
        add_row.addWidget(add)
        layout.addLayout(add_row)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search tasks…")
        self.search.setAccessibleName("Search tasks")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)
        self.filter = QComboBox()
        self.filter.addItems(["All tasks", "Active", "Completed"])
        self.filter.setAccessibleName("Task filter")
        self.filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.filter)
        layout.addLayout(filters)

        self.list = QListWidget()
        self.list.setSpacing(5)
        self.list.setWordWrap(True)
        self.list.setAccessibleName("Tasks; check a task to complete it")
        self.list.itemChanged.connect(self.toggle_task)
        self.list.itemDoubleClicked.connect(self.edit_task)
        layout.addWidget(self.list, 1)
        self.empty = QLabel()
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)

        actions = QHBoxLayout()
        self.edit = QPushButton("Edit")
        self.edit.clicked.connect(self.edit_task)
        actions.addWidget(self.edit)
        self.delete = QPushButton("Delete")
        self.delete.clicked.connect(self.delete_task)
        actions.addWidget(self.delete)
        actions.addStretch()
        self.clear = QPushButton("Clear completed")
        self.clear.clicked.connect(self.clear_completed)
        actions.addWidget(self.clear)
        layout.addLayout(actions)
        hint = QLabel("Enter to add · Double-click to edit · Check to complete")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        self.list.itemSelectionChanged.connect(self.update_actions)

        focus = QAction(self)
        focus.setShortcut(QKeySequence("Ctrl+N"))
        focus.triggered.connect(self.entry.setFocus)
        self.addAction(focus)
        self.setStyleSheet("""
            QWidget { background: #f5f6fa; color: #20283e; font-size: 14px; }
            QLabel#heading { font-size: 34px; font-weight: 700; }
            QLabel#eyebrow { color: #6555c7; font-size: 11px; font-weight: 700; }
            QLabel#hint { color: #6a7286; font-size: 12px; }
            QLineEdit, QComboBox { background: white; border: 1px solid #d9ddea;
                border-radius: 8px; padding: 11px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #7563d9; }
            QListWidget { background: white; border: 1px solid #e0e3ed; border-radius: 10px; padding: 8px; }
            QListWidget::item { padding: 12px 6px; border-radius: 6px; }
            QListWidget::item:selected { background: #eae6ff; color: #24203b; }
            QPushButton { background: #e8eaf2; border: none; border-radius: 8px; padding: 11px 15px; }
            QPushButton:hover { background: #dcdeec; }
            QPushButton#primary { background: #6853cf; color: white; font-weight: 600; }
            QPushButton#primary:hover { background: #5843bf; }
            QPushButton:disabled { color: #969cad; background: #eceef4; }
        """)
        self.refresh()
        self.entry.setFocus()

    def selected_id(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def commit(self, change):
        previous = copy.deepcopy(self.store.tasks)
        try:
            change()
            self.store.save()
        except (OSError, ValueError) as error:
            self.store.tasks = previous
            QMessageBox.warning(self, "Could not save", str(error))
            self.refresh()
            return False
        self.refresh()
        return True

    def refresh(self, *_):
        selected = self.selected_id()
        self.list.blockSignals(True)
        self.list.clear()
        query = self.search.text().casefold().strip()
        mode = self.filter.currentIndex()
        for task in self.store.tasks:
            if query not in task["title"].casefold():
                continue
            if (mode == 1 and task["done"]) or (mode == 2 and not task["done"]):
                continue
            item = QListWidgetItem(task["title"])
            item.setData(Qt.ItemDataRole.UserRole, task["id"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if task["done"] else Qt.CheckState.Unchecked)
            font = item.font()
            font.setStrikeOut(task["done"])
            item.setFont(font)
            self.list.addItem(item)
            if task["id"] == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        done = sum(t["done"] for t in self.store.tasks)
        self.summary.setText(f"{len(self.store.tasks) - done} remaining  ·  {done} completed")
        self.empty.setText("No matching tasks." if self.store.tasks else "A fresh start. Add your first task above.")
        self.empty.setVisible(self.list.count() == 0)
        self.clear.setEnabled(done > 0)
        self.update_actions()

    def update_actions(self):
        selected = self.selected_id() is not None
        self.edit.setEnabled(selected)
        self.delete.setEnabled(selected)

    def add_task(self):
        title = self.entry.text().strip()
        if not title:
            self.entry.setFocus()
            return
        if self.commit(lambda: self.store.add(title)):
            self.entry.clear()
            self.entry.setFocus()

    def toggle_task(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        done = item.checkState() == Qt.CheckState.Checked
        def change():
            next(t for t in self.store.tasks if t["id"] == task_id)["done"] = done
        self.commit(change)

    def edit_task(self, *_):
        task = next((t for t in self.store.tasks if t["id"] == self.selected_id()), None)
        if task is None:
            return
        title, ok = QInputDialog.getText(self, "Edit task", "Task:", text=task["title"])
        if ok:
            if not title.strip():
                QMessageBox.information(self, "Empty task", "Please enter a task title.")
                return
            self.commit(lambda: task.update(title=title.strip()))

    def delete_task(self):
        task_id = self.selected_id()
        if task_id is None:
            return
        if QMessageBox.question(self, "Delete task?", "Permanently delete the selected task?", defaultButton=QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.commit(lambda: setattr(self.store, "tasks", [t for t in self.store.tasks if t["id"] != task_id]))

    def clear_completed(self):
        if QMessageBox.question(self, "Clear completed?", "Permanently delete all completed tasks?", defaultButton=QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.commit(lambda: setattr(self.store, "tasks", [t for t in self.store.tasks if not t["done"]]))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Everyday To-do")
    window = TodoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
