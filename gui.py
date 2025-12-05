"""
GUI editor for the Schedule Poster Generator.
Wrapper around the modular gui package.
"""
import sys
from PySide6.QtWidgets import QApplication
from gui import PosterEditor

def main():
    app = QApplication(sys.argv)
    window = PosterEditor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()