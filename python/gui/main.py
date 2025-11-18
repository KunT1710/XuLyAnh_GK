import sys
from PyQt6 import QtWidgets
from edit import Ui_MainWindow
import icon

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Kết nối sự kiện đúng tên nút
        self.zoomIn.clicked.connect(self.zoom_in_action)
        self.zoomOut.clicked.connect(self.zoom_out_action)
        self.cut.clicked.connect(self.cut_action)

    def zoom_in_action(self):
        print("Phóng to!")

    def zoom_out_action(self):
        print("Thu nhỏ!")

    def cut_action(self):
        print("Cắt ảnh!")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
