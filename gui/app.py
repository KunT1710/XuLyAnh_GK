import sys
import os
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPen, QIcon
import icon
from views.edit import Ui_MainWindow, resource_path
import requests
from io import BytesIO

class APIWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

    def __init__(self, url, method="POST", data=None, files=None, headers=None):
        super().__init__()
        self.url = url
        self.method = method
        self.data = data
        self.files = files
        self.headers = headers

    def run(self):
        try:
            if self.method == "POST":
                response = requests.post(self.url, data=self.data, files=self.files, headers=self.headers)
            else:
                response = requests.get(self.url, headers=self.headers)
            
            response.raise_for_status()
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QtWidgets.QMainWindow):
    CELL_SIZE = 20
    LINE_ALPHA = 120
    LINE_THICKNESS = 2
    JWT_token = None
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

    # ------------------------ LOADING STATE ------------------------
    def show_loading(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.ui.centralwidget.setEnabled(False) # Disable interaction

    def hide_loading(self):
        QtWidgets.QApplication.restoreOverrideCursor()
        self.ui.centralwidget.setEnabled(True)

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

    # Open Image
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
            url = "http://localhost:8000/session/create"
            self.show_loading()

            with open(file_name, "rb") as f:
                file_bytes = f.read()
            
            files = {"file": (os.path.basename(file_name), file_bytes, "image/png")} # Simple mime type guess
            
            self.session_worker = APIWorker(url, method="POST", files=files)
            self.session_worker.finished.connect(self.on_session_created)
            self.session_worker.error.connect(self.on_api_error)
            self.session_worker.start()

    def on_session_created(self, response):
        try:
            data = response.json()
            self.session_id = data.get("session_id")
            self.JWT_token = data.get("access_token")
            print(f"Session created: {self.session_id}")
        except Exception as e:
            print(f"Lỗi parse session: {e}")
        finally:
            self.hide_loading()

    def load_image_from_file(self, file_path):
        self.original_pixmap = QPixmap(file_path)
        if self.original_pixmap.isNull():
            return

        self.openFileButton.hide()
        self.image_scroll_area.show()
        self.current_scale = 1.0
        self.update_image_display()

    # Display image
    def setup_image_viewer(self):
        self.image_scroll_area = QtWidgets.QScrollArea()
        self.image_scroll_area.setWidgetResizable(False) 
        self.image_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.image_scroll_area.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.image_scroll_area.hide()

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll_area.setWidget(self.image_label)

        # Add to layout of displayImage
        if self.ui.displayImage.layout() is None:
             layout = QtWidgets.QVBoxLayout(self.ui.displayImage)
             layout.setContentsMargins(0, 0, 0, 0)
             self.ui.displayImage.setLayout(layout)
        
        self.ui.displayImage.layout().addWidget(self.image_scroll_area)

    def update_image_display(self):
        if self.original_pixmap.isNull():
            return
        new_width = int(self.original_pixmap.width() * self.current_scale)
        new_height = int(self.original_pixmap.height() * self.current_scale)
        
        # Optimize: Use FastTransformation for speed. 
        pixmap = self.original_pixmap.scaled(
            new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation
        )
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(pixmap.size())
        
    
    def setup_tool_events(self):
        self.ui.zoomIn.clicked.connect(self.zoom_in_action)
        self.ui.zoomOut.clicked.connect(self.zoom_out_action)
        self.ui.paint.clicked.connect(self.paint_action)
        self.ui.cut.clicked.connect(self.cut_action)
        self.ui.filter.clicked.connect(self.filter_action)
        self.ui.add.clicked.connect(self.add_action)
        self.ui.transfer.clicked.connect(self.transfer_action)
        self.ui.rotate.clicked.connect(self.rotate_action)
        self.ui.edge.clicked.connect(self.edge_action)
        self.ui.unDo.clicked.connect(self.unDo_action)
        self.ui.reDo.clicked.connect(self.reDo_action)
        self.ui.down.clicked.connect(self.down_action)
        
        # Save Frame Events
        self.ui.saveButton.clicked.connect(self.process_save_image)
        self.ui.btnCloseDown.clicked.connect(self.ui.downFrame.hide)
        self.ui.btnCloseSidebar.clicked.connect(self.ui.sidebarFrame.hide)

    # front-end
    def zoom_in_action(self):
        self.current_scale *= self.zoom_factor
        self.update_image_display()

    def zoom_out_action(self):
        self.current_scale /= self.zoom_factor
        self.current_scale = max(0.1, self.current_scale)
        self.update_image_display()
    
    def paint_action(self):
        print("Paint action clicked")

    def cut_action(self):
        self.load_sidebar_content(title="Cut Options",
                                  buttons=["Rect Cut", "Auto Cut"],
                                  callback=self.apply_cut)
    def apply_cut(self, cut_type):
        if cut_type == "Auto Cut":
            if not hasattr(self, "session_id"):
                print("Chưa có session!")
                return

            url = "http://localhost:8000/cut/bg-auto"
            payload = {"session_id": self.session_id}
            self.call_api_and_update(url, payload)

        elif cut_type == "Rect Cut":
            print("Rect Cut chưa được implement")
        else:
            print(f"Áp dụng cut: {cut_type}")

    def rotate_action(self):
        self.load_sidebar_content(
        title="Rotate Options",
        buttons=["90°", "180°", "360°"],
        callback=self.apply_rotate
    )
    def apply_rotate(self, rotate_type):
        if self.original_pixmap.isNull():
            return

        transform = QtGui.QTransform()
        if rotate_type == "90°":
            transform.rotate(90)
        elif rotate_type == "180°":
            transform.rotate(180)
        elif rotate_type == "360°":
            transform.rotate(360)
        else:
            print(f"Rotate {rotate_type} chưa được implement")
            return

        # 1. Xử lý Frontend
        self.original_pixmap = self.original_pixmap.transformed(transform)
        self.update_image_display()

        # 2. Upload lên Server (Full-stack logic)
        self.upload_image_to_server(self.original_pixmap)
        
    # back-end
    def filter_action(self):
        self.load_sidebar_content(
        title="Filter Options",
        buttons=["Median", "Mean", "Gaussian"],
        callback=self.apply_filter
    )
    # ------------------------ HELPERS ------------------------
    def update_image_from_server(self):
        """Helper để tải ảnh mới nhất từ server về và hiển thị (Async)"""
        if not hasattr(self, "session_id"):
            self.hide_loading()
            return

        url = f"http://localhost:8000/undo_redo/current?session_id={self.session_id}"
        headers = {"token": self.JWT_token}
        
        self.image_worker = APIWorker(url, method="GET", headers=headers)
        self.image_worker.finished.connect(self.on_image_update_success)
        self.image_worker.error.connect(self.on_api_error)
        self.image_worker.start()

    def on_image_update_success(self, response):
        try:
            image_data = response.content
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            if not pixmap.isNull():
                self.original_pixmap = pixmap
                self.update_image_display()
            else:
                print("Ảnh tải về bị lỗi")
        except Exception as e:
            print(f"Lỗi hiển thị ảnh: {e}")
        finally:
            self.hide_loading()

    def upload_image_to_server(self, pixmap: QPixmap):
        """Helper để upload ảnh hiện tại (đã xử lý ở frontend) lên server (Async)"""
        if not hasattr(self, "session_id"):
            return

        url = "http://localhost:8000/update"
        headers = {"token": self.JWT_token}
        
        # Convert QPixmap to bytes
        byte_array = QtCore.QByteArray()
        buffer = QtCore.QBuffer(byte_array)
        buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_bytes = byte_array.data()

        files = {"file": ("update.png", image_bytes, "image/png")}
        data = {"session_id": self.session_id}

        self.show_loading()
        self.upload_worker = APIWorker(url, method="POST", data=data, files=files, headers=headers)
        self.upload_worker.finished.connect(self.on_upload_success)
        self.upload_worker.error.connect(self.on_api_error)
        self.upload_worker.start()

    def on_upload_success(self, response):
        print("Upload ảnh thành công")
        self.hide_loading()

    def on_api_error(self, error_msg):
        self.hide_loading()
        print(f"Lỗi API: {error_msg}")
        QtWidgets.QMessageBox.warning(self, "Lỗi", f"Có lỗi xảy ra: {error_msg}")

    # ------------------------ BACKEND ACTIONS ------------------------
    def apply_filter(self, filter_name):
        if not hasattr(self, "session_id"):
            print("Chưa có session!")
            return

        url = ""
        payload = {"session_id": self.session_id}
        
        if filter_name == "Median":
            url = "http://localhost:8000/filter/median"
            payload["ksize"] = 5
        elif filter_name == "Mean":
            url = "http://localhost:8000/filter/mean"
            payload["ksize"] = 5
        elif filter_name == "Gaussian":
            url = "http://localhost:8000/filter/gaussian"
            payload["ksize"] = 5
            payload["sigma"] = 1.0
        else:
            print(f"Filter {filter_name} chưa được implement")
            return

        self.call_api_and_update(url, payload)

    def transfer_action(self):
        self.load_sidebar_content(
            title="Transfer Options",
            buttons=["Gray", "Binary", "Brightness", "Blur"],
            callback=self.apply_transfer
        )

    def apply_transfer(self, transfer_name):
        if not hasattr(self, "session_id"):
            print("Chưa có session!")
            return

        url = ""
        payload = {"session_id": self.session_id}

        if transfer_name == "Gray":
            url = "http://localhost:8000/transfer/gray"
        elif transfer_name == "Binary":
            url = "http://localhost:8000/transfer/binary"
            payload["thresh"] = 127
        elif transfer_name == "Brightness":
            url = "http://localhost:8000/transfer/brightness"
            payload["beta"] = 30 # Tăng sáng mặc định
        elif transfer_name == "Blur":
            url = "http://localhost:8000/transfer/blur"
            payload["ksize"] = 5
        else:
            print(f"Transfer {transfer_name} chưa được implement")
            return

        self.call_api_and_update(url, payload)

    def edge_action(self):
        self.load_sidebar_content(
            title="Edge Options",
            buttons=["Sobel", "Prewitt", "Robert", "Canny"],
            callback=self.apply_edge
        )

    def apply_edge(self, edge_name):
        if not hasattr(self, "session_id"):
            print("Chưa có session!")
            return

        url = ""
        payload = {"session_id": self.session_id}

        if edge_name == "Sobel":
            url = "http://localhost:8000/edge-detect/sobel"
        elif edge_name == "Prewitt":
            url = "http://localhost:8000/edge-detect/prewitt"
        elif edge_name == "Robert":
            url = "http://localhost:8000/edge-detect/robert"
        elif edge_name == "Canny":
            url = "http://localhost:8000/edge-detect/canny"
        else:
            print(f"Edge {edge_name} chưa được implement")
            return

        self.call_api_and_update(url, payload)

    def call_api_and_update(self, url, payload):
        self.show_loading()
        headers = {"token": self.JWT_token}
        self.worker = APIWorker(url, method="POST", data=payload, headers=headers)
        self.worker.finished.connect(self.on_api_success)
        self.worker.error.connect(self.on_api_error)
        self.worker.start()

    def on_api_success(self, response):
        print("API call success")
        # Chain call to update image
        self.update_image_from_server()

    # full-stack
    def add_action(self):
        print("Add action clicked")

    def unDo_action(self):
        print("Undo clicked")

    def reDo_action(self):
        print("Redo clicked")

    def down_action(self):
        """Show the download/save options frame"""
        self.ui.downFrame.show()
        self.ui.downFrame.raise_()

    def process_save_image(self):
        if self.original_pixmap.isNull():
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Không có ảnh để lưu!")
            return

        # 1. Get inputs
        file_name = self.ui.nameFileValue.text().strip()
        file_format = self.ui.formatValue.currentText().lower() # jpg, png, pgm
        quality = self.ui.qualityVaule.value()

        if not file_name:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên file!")
            return

        # 2. Choose directory
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
        if not dir_path:
            return

        # 3. Construct full path
        full_path = os.path.join(dir_path, f"{file_name}.{file_format}")

        # 4. Save
        try:
            # Quality mapping: 0-100 for JPG. PNG ignores quality in save() usually (compression level is different), 
            # but PyQt's save() 'quality' param maps to compression for PNG (0-100 where 100 is small compression? No, usually 0-100 quality).
            # Qt docs: quality is 0-100. -1 is default.
            
            # For JPG: 0 (small) to 100 (large, high quality).
            # For PNG: 0 (large, no compression) to 100 (small, max compression)? 
            # Actually QPixmap.save quality is format dependent. 
            # Let's just pass the value.
            
            success = self.original_pixmap.save(full_path, file_format.upper(), quality)
            
            if success:
                QtWidgets.QMessageBox.information(self, "Thành công", f"Đã lưu ảnh tại:\n{full_path}")
                self.ui.downFrame.hide()
            else:
                QtWidgets.QMessageBox.critical(self, "Lỗi", "Lưu ảnh thất bại!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi khi lưu ảnh: {e}")

        
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
