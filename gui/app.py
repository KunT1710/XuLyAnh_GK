import sys
import os
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPen, QIcon
import icon
from views.edit import Ui_MainWindow, resource_path


class MainWindow(QtWidgets.QMainWindow):
    CELL_SIZE = 20
    LINE_ALPHA = 120
    LINE_THICKNESS = 2

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.original_pixmap = QPixmap()
        self.current_scale = 1.0
        self.zoom_factor = 1.2

        self.ui.sidebarFrame.hide()
        self.ui.downFrame.hide()

        self.setup_display_image()
        self.setup_image_open_ui()
        self.setup_image_viewer()
        self.setup_tool_events()

    # ------------------------ GRID BACKGROUND ------------------------
    def create_grid_background(self, size: QSize) -> QPixmap:
        pixmap = QPixmap(size)
        pixmap.fill(QColor(236, 234, 234))

        painter = QPainter(pixmap)
        grid_color = QColor(255, 255, 255, self.LINE_ALPHA)
        pen = QPen(grid_color)
        pen.setWidth(self.LINE_THICKNESS)
        painter.setPen(pen)

        for x in range(0, size.width(), self.CELL_SIZE):
            painter.drawLine(x, 0, x, size.height())
        for y in range(0, size.height(), self.CELL_SIZE):
            painter.drawLine(0, y, size.width(), y)

        painter.end()
        return pixmap

    def update_grid_background(self):
        size = self.ui.displayImage.size()
        pixmap = self.create_grid_background(size)
        self.displayImageLabel.setPixmap(pixmap)
        self.displayImageLabel.setScaledContents(True)

    # ------------------------ DISPLAY IMAGE ------------------------
    def setup_display_image(self):
        size = self.ui.displayImage.size()
        self.displayImageLabel = QtWidgets.QLabel(self.ui.displayImage)
        self.displayImageLabel.setGeometry(0, 0, size.width(), size.height())
        self.update_grid_background()

    # ------------------------ OPEN IMAGE ------------------------
    def setup_image_open_ui(self):
        layout = QtWidgets.QVBoxLayout(self.ui.displayImage)
        layout.setContentsMargins(0, 0, 0, 0)

        self.openFileButton = QtWidgets.QPushButton("  Mở file ảnh")
        self.openFileButton.setFixedSize(200, 50)
        icon_path = os.path.join(os.path.dirname(__file__), "icon/open.png")
        self.openFileButton.setIcon(QIcon(icon_path))
        self.openFileButton.setIconSize(QSize(32, 32))
        self.openFileButton.setObjectName("openFileButton")

        h = QtWidgets.QHBoxLayout()
        h.addStretch()
        h.addWidget(self.openFileButton)
        h.addStretch()

        layout.addStretch()
        layout.addLayout(h)
        layout.addStretch()

        self.openFileButton.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Chọn File Ảnh", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_name:
            self.load_image_from_file(file_name)

    def load_image_from_file(self, file_path):
        self.original_pixmap = QPixmap(file_path)
        if self.original_pixmap.isNull():
            return

        self.openFileButton.hide()
        self.image_scroll_area.show()
        self.current_scale = 1.0
        self.update_image_display()

    # ------------------------ IMAGE VIEWER ------------------------
    def setup_image_viewer(self):
        self.image_scroll_area = QtWidgets.QScrollArea(self.ui.displayImage)
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setGeometry(self.ui.displayImage.rect())
        self.image_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.image_scroll_area.hide()

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.image_scroll_area.setWidget(self.image_label)

    def update_image_display(self):
        if self.original_pixmap.isNull():
            return
        new_width = int(self.original_pixmap.width() * self.current_scale)
        new_height = int(self.original_pixmap.height() * self.current_scale)
        pixmap = self.original_pixmap.scaled(
            new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(new_width, new_height)
        
    
    # event
    def setup_tool_events(self):
        self.ui.zoomIn.clicked.connect(self.zoom_in_action)
        self.ui.zoomOut.clicked.connect(self.zoom_out_action)
        self.ui.cut.clicked.connect(self.cut_action)
        self.ui.down.clicked.connect(self.down_action)
        self.ui.filter.clicked.connect(self.filter_action)
        
    def zoom_in_action(self):
        self.current_scale *= self.zoom_factor
        self.update_image_display()
        self.ui.sidebarFrame.show()
        self.ui.sidebarFrame.raise_()

    def zoom_out_action(self):
        self.current_scale /= self.zoom_factor
        self.current_scale = max(0.1, self.current_scale)
        self.update_image_display()

    def cut_action(self):
        self.load_sidebar_content(
            title="Cut Options",
            buttons=["Test1", "Test2"],
            callback=self.apply_filter
        )
        
    def down_action(self):
        self.ui.downFrame.show()
        self.ui.downFrame.raise_()
        

    def filter_action(self):
        self.load_sidebar_content(
        title="Filter Options",
        buttons=["Median", "Mean", "Gaussian"],
        callback=self.apply_filter
    )

    def apply_filter(self, filter_name):
        print(f"Áp dụng filter: {filter_name}")

        
    def load_sidebar_content(self, title: str, buttons: list, callback):
        """
        Load dynamic content into sidebar.
        :param title: str, text hiển thị ở title
        :param buttons: list of str, tên các nút
        :param callback: function, callback khi nhấn nút, nhận param là tên nút
        """
        self.ui.sidebarFrame.show()
        self.ui.sidebarFrame.raise_()
        if self.ui.sidebarFrame.layout() is None:
            main_layout = QtWidgets.QVBoxLayout()
            main_layout.setContentsMargins(12, 15, 12, 15)
            self.ui.sidebarFrame.setLayout(main_layout)
        else:
            main_layout = self.ui.sidebarFrame.layout()
        self.ui.title_chucNang_2.setText(title)
        self.ui.title_chucNang_2.setMaximumHeight(50)
        if self.ui.title_chucNang_2.parent() != self.ui.sidebarFrame:
            self.ui.title_chucNang_2.setParent(self.ui.sidebarFrame)
        self.ui.title_chucNang_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.ui.title_chucNang_2.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
        """)
        if main_layout.indexOf(self.ui.title_chucNang_2) == -1:
            main_layout.insertWidget(0, self.ui.title_chucNang_2)
        if not hasattr(self, "filter_separator"):
            self.filter_separator = QtWidgets.QFrame()
            self.filter_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            self.filter_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            self.filter_separator.setStyleSheet("""
                QFrame {
                    background-color: #000000;
                    border: 2px solid #333;
                    margin-top: 5px;
                    margin-bottom: 10px;
                }
            """)
            main_layout.insertWidget(1, self.filter_separator)
        if not hasattr(self, "filter_content_frame"):
            self.filter_content_frame = QtWidgets.QFrame()
            content_layout = QtWidgets.QVBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)
            self.filter_content_frame.setLayout(content_layout)
            main_layout.insertWidget(2, self.filter_content_frame)
        else:
            content_layout = self.filter_content_frame.layout()
            for i in reversed(range(content_layout.count())):
                item = content_layout.itemAt(i)
                if item.spacerItem() is not None:
                    content_layout.takeAt(i)
                widget = item.widget()
                if widget:
                    content_layout.takeAt(i)
                    widget.deleteLater()
        btn_style = """
            QPushButton {
                background-color: #39BAF4;
                color: white;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #2a99c9;
            }
            QPushButton:pressed {
                background-color: #1d6a8b;
            }
        """
        for name in buttons:
            btn = QtWidgets.QPushButton(name)
            btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda checked, n=name: callback(n))
            content_layout.addWidget(btn)

        content_layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_grid_background()
        self.image_scroll_area.setGeometry(self.ui.displayImage.rect())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    qss_path = resource_path(os.path.join("style.qss"))
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"QSS file not found: {qss_path}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
