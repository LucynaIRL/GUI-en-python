from PySide6.QtWidgets import QProxyStyle, QStyleFactory
from PySide6.QtGui import QPalette, QColor


class CatppuccinStyle(QProxyStyle):
    def __init__(self):
        super().__init__(QStyleFactory.create("Fusion"))

    def create_palette(self):
        palette = QPalette()

        base = QColor("#1E1E2E")
        surface = QColor("#313244")
        text = QColor("#CDD6F4")
        accent = QColor("#B4BEFE")

        palette.setColor(QPalette.Window, base)
        palette.setColor(QPalette.Base, surface)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Button, surface)
        palette.setColor(QPalette.ButtonText, text)
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, base)

        return palette