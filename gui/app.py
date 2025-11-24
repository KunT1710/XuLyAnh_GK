import sys
import os
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter, QPen, QIcon, QCursor, QIntValidator

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QLineEdit,
)

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
        self.is_painting = False
        self.last_point = None
        self.brush_size = 5
        self.brush_color = QColor(255, 0, 0)

    def run(self):
        try:
            if self.method == "POST":
                response = requests.post(
                    self.url, data=self.data, files=self.files, headers=self.headers
                )
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
        self.brush_size = 5
        self.brush_color = QColor(0, 0, 0)

        self.ui.sidebarFrame.hide()
        self.ui.downFrame.hide()

        self.setup_display_image()
        self.setup_image_open_ui()
        self.setup_image_viewer()
        self.setup_tool_events()

    def show_loading(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        self.ui.frame.setEnabled(False)
        self.ui.unDo_reDo.setEnabled(False)
        self.ui.down.setEnabled(False)
        self.ui.sidebarFrame.setEnabled(False)
        self.ui.downFrame.setEnabled(False)
        if hasattr(self, "openFileButton"):
            self.openFileButton.setEnabled(False)

    def hide_loading(self):
        QtWidgets.QApplication.restoreOverrideCursor()
        self.ui.frame.setEnabled(True)
        self.ui.unDo_reDo.setEnabled(True)
        self.ui.down.setEnabled(True)
        self.ui.sidebarFrame.setEnabled(True)
        self.ui.downFrame.setEnabled(True)
        if hasattr(self, "openFileButton"):
            self.openFileButton.setEnabled(True)

    # Gird
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

        if not self.original_pixmap.isNull():
            pixmap = QPixmap(size)
            pixmap.fill(QColor(255, 255, 255))
        else:
            pixmap = self.create_grid_background(size)

        self.displayImageLabel.setPixmap(pixmap)
        self.displayImageLabel.setScaledContents(True)
        self.displayImageLabel.resize(size)

    def setup_display_image(self):
        size = self.ui.displayImage.size()
        self.displayImageLabel = QtWidgets.QLabel(self.ui.displayImage)
        self.displayImageLabel.setGeometry(0, 0, size.width(), size.height())
        self.update_grid_background()
        self.stacked_layout = QtWidgets.QStackedLayout(self.ui.displayImage)

    def setup_image_open_ui(self):
        self.open_file_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.open_file_widget)
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

        self.stacked_layout.addWidget(self.open_file_widget)

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

            files = {"file": (os.path.basename(file_name), file_bytes, "image/png")}
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
        self.stacked_layout.setCurrentWidget(self.image_scroll_area)
        self.current_scale = 1.0
        self.update_grid_background()
        self.update_image_display()

    # display image
    def setup_image_viewer(self):
        self.image_scroll_area = QtWidgets.QScrollArea()
        self.image_scroll_area.setWidgetResizable(False)
        self.image_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.image_scroll_area.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll_area.setWidget(self.image_label)
        self.stacked_layout.addWidget(self.image_scroll_area)
        self.stacked_layout.setCurrentWidget(self.open_file_widget)

    def update_image_display(self):
        if self.original_pixmap.isNull():
            return
        new_width = int(self.original_pixmap.width() * self.current_scale)
        new_height = int(self.original_pixmap.height() * self.current_scale)

        pixmap = self.original_pixmap.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
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
        self.ui.saveButton.clicked.connect(self.process_save_image)
        self.ui.btnCloseDown.clicked.connect(self.ui.downFrame.hide)
        self.ui.btnCloseSidebar.clicked.connect(self.ui.sidebarFrame.hide)

        # Set cursor for close buttons
        self.ui.btnCloseDown.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.btnCloseSidebar.setCursor(Qt.CursorShape.PointingHandCursor)

        self.ui.actionFacebook.triggered.connect(self.action_face)
        self.ui.actionGithub.triggered.connect(self.action_github)
        self.ui.actionOpen.triggered.connect(self.action_Open)

        self.actionExitApp = QtGui.QAction("Thoát", self)
        exit_icon = os.path.join(os.path.dirname(__file__), "icon/exit.png")
        self.actionExitApp.setIcon(QIcon(exit_icon))
        self.actionExitApp.triggered.connect(self.close)
        self.ui.exit.addAction(self.actionExitApp)

    def action_face(self):
        import webbrowser

        webbrowser.open("https://www.facebook.com/kunt1710")

    def action_github(self):
        import webbrowser

        webbrowser.open("https://github.com/KunT1710/XuLyAnh_GK")

    def action_Open(self):
        self.open_file_dialog()

    def closeEvent(self, event):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Xác nhận thoát")
        msg.setText("Bạn có chắc chắn muốn thoát ứng dụng không?")

        icon_path = os.path.join(os.path.dirname(__file__), "icon/logo512.png")
        pix = QtGui.QPixmap(icon_path)
        if not pix.isNull():
            msg.setIconPixmap(
                pix.scaled(
                    48,
                    48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)

        msg.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)

        reply = msg.exec()

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            if hasattr(self, "session_id") and self.session_id:
                try:
                    import requests

                    url = f"http://localhost:8000/session/delete/{self.session_id}"
                    headers = {"token": self.JWT_token} if self.JWT_token else {}
                    requests.delete(url, headers=headers, timeout=2)
                    print(f"Đã xóa session: {self.session_id}")
                except Exception as e:
                    print(f"Lỗi khi xóa session: {e}")

            event.accept()
        else:
            event.ignore()

    def check_image_loaded(self):
        if self.original_pixmap.isNull():
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("Cảnh báo")
            msg.setText("Vui lòng mở ảnh trước khi thực hiện thao tác này!")

            icon_path = os.path.join(os.path.dirname(__file__), "icon/warning.png")
            pix = QtGui.QPixmap(icon_path)
            if not pix.isNull():
                msg.setIconPixmap(
                    pix.scaled(
                        48,
                        48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            else:
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)

            msg.exec()
            return False
        return True

    def zoom_in_action(self):
        if not self.check_image_loaded():
            return
        self.current_scale *= self.zoom_factor
        self.update_image_display()

    def zoom_out_action(self):
        if not self.check_image_loaded():
            return
        self.current_scale /= self.zoom_factor
        self.current_scale = max(0.1, self.current_scale)
        self.update_image_display()

    def paint_action(self):
        if not self.check_image_loaded():
            return
        # Bật chế độ vẽ
        self.is_painting = True
        self.ui.sidebarFrame.show()

        # Đổi con trỏ sang bút
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon", "pen.png")
        print(f"Loading pen icon from: {icon_path}")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Hotspot ở mũi bút (góc dưới trái hoặc tùy icon), mặc định là center
            self.image_label.setCursor(QCursor(pixmap, 0, 32)) 
        else:
            print(f"Warning: Could not load pen icon from {icon_path}")
            self.image_label.setCursor(Qt.CursorShape.CrossCursor)

        # Gắn sự kiện chuột
        self.image_label.mousePressEvent = self.on_mouse_press
        self.image_label.mouseMoveEvent = self.on_mouse_move
        self.image_label.mouseReleaseEvent = self.on_mouse_release

        # Tạo sidebar
        self.load_sidebar_content(
            title="Paint Options", custom_widget=self.create_paint_sidebar()
        )

    def update_rgb_color(self):
        try:
            r = int(self.r_edit.text())
            g = int(self.g_edit.text())
            b = int(self.b_edit.text())
            self.brush_color = QColor(r, g, b)
        except:
            pass

    def on_mouse_press(self, event):
        if not self.is_painting:
            return
        self.last_point = event.position().toPoint()

    def on_mouse_move(self, event):
        if not self.is_painting or self.last_point is None:
            return

        current_point = event.position().toPoint()

        # Vẽ trực tiếp lên original_pixmap
        painter = QPainter(self.original_pixmap)
        pen = QPen(
            self.brush_color,
            self.brush_size,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)

        # Chỉnh theo scale để vẽ đúng vị trí
        p1 = self.last_point / self.current_scale
        p2 = current_point / self.current_scale

        painter.drawLine(p1, p2)
        painter.end()

        self.last_point = current_point

        # Cập nhật UI
        self.update_image_display()

    def on_mouse_release(self, event):
        if not self.is_painting:
            return

        self.last_point = None

        # Upload ảnh lên server
        self.upload_image_to_server(self.original_pixmap)

    def cut_action(self):
        if not self.check_image_loaded():
            return
        self.load_sidebar_content(
            title="Cut Options",
            buttons=["Rect Cut", "Auto Cut"],
            callback=self.apply_cut,
        )

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
        if not self.check_image_loaded():
            return
        self.load_sidebar_content(
            title="Rotate Options",
            buttons=["90°", "180°", "360°"],
            callback=self.apply_rotate,
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

        self.original_pixmap = self.original_pixmap.transformed(transform)
        self.update_image_display()

        self.upload_image_to_server(self.original_pixmap)

    # back-end
    def filter_action(self):
        if not self.check_image_loaded():
            return
        self.load_sidebar_content(
            title="Filter Options",
            buttons=["Median", "Mean", "Gaussian"],
            callback=self.apply_filter,
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
        self.upload_worker = APIWorker(
            url, method="POST", data=data, files=files, headers=headers
        )
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

    # call api
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
        if not self.check_image_loaded():
            return
        self.load_sidebar_content(
            title="Transfer Options",
            buttons=["Gray", "Binary", "Brightness", "Blur"],
            callback=self.apply_transfer,
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
            payload["beta"] = 30
        elif transfer_name == "Blur":
            url = "http://localhost:8000/transfer/blur"
            payload["ksize"] = 5
        else:
            print(f"Transfer {transfer_name} chưa được implement")
            return

        self.call_api_and_update(url, payload)

    def edge_action(self):
        if not self.check_image_loaded():
            return
        self.load_sidebar_content(
            title="Edge Options",
            buttons=["Sobel", "Prewitt", "Robert", "Canny"],
            callback=self.apply_edge,
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
            payload["threshold1"] = 100
            payload["threshold2"] = 200
        else:
            print(f"Edge {edge_name} chưa được implement")
            return

        self.call_api_and_update(url, payload)

    def add_action(self):
        if not self.check_image_loaded():
            return
        self.load_sidebar_content(
            title="Add Noise Options",
            buttons=["Salt", "Gaussian"],
            callback=self.apply_add,
        )

    def apply_add(self, add_name):
        if not hasattr(self, "session_id"):
            print("Chưa có session!")
            return

        url = ""
        payload = {"session_id": self.session_id}

        if add_name == "Salt":
            url = "http://localhost:8000/noise/salt-pepper"
            payload["amount"] = 0.05
        elif add_name == "Gaussian":
            url = "http://localhost:8000/noise/gaussian"
            payload["mean"] = 0
            payload["sigma"] = 25
        else:
            print(f"Add {add_name} chưa được implement")
            return

        self.call_api_and_update(url, payload)

    def unDo_action(self):
        if not self.check_image_loaded():
            return
        if not hasattr(self, "session_id"):
            return
        url = "http://localhost:8000/undo_redo/undo"
        payload = {"session_id": self.session_id}
        self.call_api_and_update(url, payload, method="POST")

    def reDo_action(self):
        if not self.check_image_loaded():
            return
        if not hasattr(self, "session_id"):
            return
        url = "http://localhost:8000/undo_redo/redo"
        payload = {"session_id": self.session_id}
        self.call_api_and_update(url, payload, method="POST")

    def down_action(self):
        """Show the download/save options frame"""
        if not self.check_image_loaded():
            return
        self.ui.downFrame.show()
        self.ui.downFrame.raise_()

    def process_save_image(self):
        if self.original_pixmap.isNull():
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Không có ảnh để lưu!")
            return

        file_name = self.ui.nameFileValue.text().strip()
        file_format = self.ui.formatValue.currentText().lower()  # jpg, png, pgm
        quality = self.ui.qualityVaule.value()

        if not file_name:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên file!")
            return

        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
        if not dir_path:
            return

        full_path = os.path.join(dir_path, f"{file_name}.{file_format}")

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
                QtWidgets.QMessageBox.information(
                    self, "Thành công", f"Đã lưu ảnh tại:\n{full_path}"
                )
                self.ui.downFrame.hide()
            else:
                QtWidgets.QMessageBox.critical(self, "Lỗi", "Lưu ảnh thất bại!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi khi lưu ảnh: {e}")

    def call_api_and_update(self, url, payload, method="POST"):
        self.show_loading()
        headers = {"token": self.JWT_token}
        self.worker = APIWorker(url, method=method, data=payload, headers=headers)
        self.worker.finished.connect(self.on_api_success)
        self.worker.error.connect(self.on_api_error)
        self.worker.start()

    def on_api_success(self, response):
        print("API call success")
        # Chain call to update image
        self.update_image_from_server()

    def create_paint_sidebar(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ============ Brush Size ============
        size_label = QLabel("Pen Size")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(50)
        slider.setValue(self.brush_size)
        slider.valueChanged.connect(lambda v: setattr(self, "brush_size", v))

        layout.addWidget(size_label)
        layout.addWidget(slider)
        layout.addSpacing(10)

        rgb_label = QLabel("Color (RGB)")
        layout.addWidget(rgb_label)


        self.r_edit = QLineEdit("0")
        self.g_edit = QLineEdit("0")
        self.b_edit = QLineEdit("0")

        rgb_container = QWidget()
        rgb_layout = QVBoxLayout(rgb_container)
        rgb_layout.setContentsMargins(0, 0, 0, 0)

        for label_text, edit in [("R:", self.r_edit), ("G:", self.g_edit), ("B:", self.b_edit)]:
            edit.setValidator(QIntValidator(0, 255))
            edit.setMaximumWidth(100)
            edit.textChanged.connect(self.update_rgb_color)
            
            row_layout = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(20)
            row_layout.addWidget(lbl)
            row_layout.addWidget(edit)
            rgb_layout.addLayout(row_layout)

        layout.addWidget(rgb_container)
        layout.addStretch()

        return widget

    def load_sidebar_content(
        self, title: str, buttons: list = None, callback=None, custom_widget=None
    ):
        """
        Load dynamic content into sidebar.
        :param title: str, text hiển thị ở title
        :param buttons: list of str, tên các nút
        :param callback: function, callback khi nhấn nút, nhận param là tên nút
        :param custom_widget: QWidget, widget tùy chỉnh để hiển thị (thay vì buttons)
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
        self.ui.title_chucNang_2.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
        """
        )
        if main_layout.indexOf(self.ui.title_chucNang_2) == -1:
            main_layout.insertWidget(0, self.ui.title_chucNang_2)
        if not hasattr(self, "filter_separator"):
            self.filter_separator = QtWidgets.QFrame()
            self.filter_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            self.filter_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            self.filter_separator.setStyleSheet(
                """
                QFrame {
                    background-color: #000000;
                    border: 2px solid #333;
                    margin-top: 5px;
                    margin-bottom: 10px;
                }
            """
            )
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
        if custom_widget:
            content_layout.addWidget(custom_widget)
        elif buttons and callback:
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

        # Ensure close button is at the bottom
        if main_layout.indexOf(self.ui.btnCloseSidebar) == -1:
            main_layout.addWidget(self.ui.btnCloseSidebar)

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
