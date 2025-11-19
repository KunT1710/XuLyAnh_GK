import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPen, QIcon

from views.edit import Ui_MainWindow
import icon


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    CELL_SIZE = 20
    LINE_ALPHA = 120
    LINE_THICKNESS = 2

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.original_pixmap = QPixmap()
        self.current_scale = 1.0
        self.zoom_factor = 1.2

        self.sidebarFrame.hide()
        self.downFrame.hide()

        size = self.displayImage.size()
        self.displayImageLabel = QtWidgets.QLabel(self.displayImage)
        self.displayImageLabel.setGeometry(0, 0, size.width(), size.height())
        self.update_grid_background()

        self.setup_image_open_ui()
        self.setup_image_viewer()

        self.setup_tool_events()

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
        """Cập nhật ảnh nền lưới khi resize."""
        size = self.displayImage.size()
        pixmap = self.create_grid_background(size)
        self.displayImageLabel.setPixmap(pixmap)
        self.displayImageLabel.setScaledContents(True)

    def setup_image_open_ui(self):
        """Nút mở file căn giữa displayImage."""
        layout = QtWidgets.QVBoxLayout(self.displayImage)
        layout.setContentsMargins(0, 0, 0, 0)

        from PyQt6.QtWidgets import QPushButton, QHBoxLayout

        self.openFileButton = QPushButton("  Mở file ảnh")
        self.openFileButton.setFixedSize(200, 50)
        import os
        from PyQt6.QtGui import QIcon

        icon_path = os.path.join(os.path.dirname(__file__), "icon/open.png")
        icon_open = QIcon(icon_path)
        self.openFileButton.setIcon(icon_open)
        self.openFileButton.setIconSize(QtCore.QSize(32, 32))
        self.openFileButton.setObjectName("openFileButton")


        layout.addStretch()
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(self.openFileButton)
        h.addStretch()
        layout.addLayout(h)
        layout.addStretch()

        self.openFileButton.clicked.connect(self.open_file_dialog)

    def setup_image_viewer(self):
        """ScrollArea + QLabel để hiển thị ảnh."""
        from PyQt6.QtWidgets import QScrollArea, QLabel

        self.image_scroll_area = QScrollArea(self.displayImage)
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setGeometry(self.displayImage.rect())
        self.image_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.image_scroll_area.hide()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.image_scroll_area.setWidget(self.image_label)
        
    def open_file_dialog(self):
        """Mở hộp thoại chọn ảnh."""
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Chọn File Ảnh",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_name:
            self.load_image_from_file(file_name)

    def load_image_from_file(self, file_path):
        """Hiển thị ảnh sau khi load."""
        self.original_pixmap = QPixmap(file_path)

        if self.original_pixmap.isNull():
            return

        self.openFileButton.hide()
        self.image_scroll_area.show()
        self.current_scale = 1.0
        self.update_image_display()

    def update_image_display(self):
        """Scale + hiển thị ảnh."""
        if self.original_pixmap.isNull():
            return

        new_width = int(self.original_pixmap.width() * self.current_scale)
        new_height = int(self.original_pixmap.height() * self.current_scale)
        
        pixmap = self.original_pixmap.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(pixmap)
        self.image_label.resize(new_width, new_height)

    def setup_tool_events(self):
        self.zoomIn.clicked.connect(self.zoom_in_action)
        self.zoomOut.clicked.connect(self.zoom_out_action)
        self.cut.clicked.connect(self.cut_action)
        self.down.clicked.connect(self.down_action)

    def zoom_in_action(self):
        self.current_scale *= self.zoom_factor
        self.update_image_display()
        self.sidebarFrame.show()
        self.sidebarFrame.raise_()

    def zoom_out_action(self):
        self.current_scale /= self.zoom_factor
        self.current_scale = max(0.1, self.current_scale)
        self.update_image_display()

    def cut_action(self):
        print("Cắt ảnh!")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_grid_background()
        self.image_scroll_area.setGeometry(self.displayImage.rect())
    def down_action(self):
        self.downFrame.show()
        self.downFrame.raise_()
        
if __name__ == "__main__":
    import os
    app = QtWidgets.QApplication(sys.argv)
    
    base = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(base, "views","style.qss")

    with open(qss_path, "r") as f:
        app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
