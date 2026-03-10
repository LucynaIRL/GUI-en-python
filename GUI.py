import sys
import os
import subprocess
import time
import requests

from PySide6.QtCore import Slot,QThread,Signal,QObject
from PySide6.QtWidgets import QApplication, QLabel, QWidget,QVBoxLayout, QHBoxLayout,QPushButton,QComboBox, QFileDialog, QTableWidget,QTableWidgetItem,QHeaderView
from PySide6.QtGui import QIcon
from styles.catppuccin_style import CatppuccinStyle

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

JAR  = os.path.join(BASE_DIR, "ProcesadorDeDatos-1.0.jar")
JAVA = os.path.join(BASE_DIR, "jre", "bin", "java.exe")

api = subprocess.Popen(
    [JAVA, "-jar", JAR],
    creationflags=subprocess.CREATE_NO_WINDOW
)

for _ in range(20):
        try:
            requests.get("http://localhost:8080/actuator/health", timeout=1)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
#Cliente http para la api en java
class ApiClient(QObject):
    hojas_listas    = Signal(object)
    columnas_listas = Signal(object)
    conteos_listos  = Signal(object)
    error           = Signal(str)

    def __init__(self,base_url):
        super().__init__()
        self.base_url   = base_url
        self.session    = requests.Session()


    def post_archivo(self,endpoint,data = None):
        url= f"{self.base_url}/{endpoint}"
        response = self.session.post(url,data=data)
        response.raise_for_status()
        return response.json()
    @Slot(str)
    def get_hojas(self,file):
        data ={'archivo' : file}
        resultado = self.post_archivo("api/hojas",data=data)
        self.hojas_listas.emit(resultado)
    @Slot(str,str)
    def get_columnas(self,file,hoja):
        data = {'hoja': hoja,'archivo' : file}
        resultado = self.post_archivo("api/columnas",data=data)
        self.columnas_listas.emit(resultado)
    @Slot(str,str,int)
    def get_conteos(self,file,hoja,columna):
        data = {"hoja" : hoja,'archivo' :file,"columna" : columna}
        resultado = self.post_archivo("api/conteos",data=data)
        self.conteos_listos.emit(resultado)

#window
def populate(tabla, conteos):
    tabla.clear()
    tabla.setHorizontalHeaderLabels(['Valor','Repeticiones'])
    conteos_ordenados = dict(sorted(conteos.items(),key=lambda item:item[1],reverse=True))
    tabla.setRowCount(len(conteos_ordenados))
    for row, (key, value) in enumerate(conteos_ordenados.items()):
        tabla.setItem(row, 0, QTableWidgetItem(str(key)))
        tabla.setItem(row, 1, QTableWidgetItem(str(value)))


class Ventana (QWidget):
    pedir_hojas     = Signal(str)
    pedir_columnas  = Signal(str,str)
    pedir_conteos   = Signal(str,str,int)
    def __init__(self):
        super().__init__()
        self.filename = None
        self.api_thread = QThread()
        self.api = ApiClient('http://localhost:8080')
        self.api.moveToThread(self.api_thread)
        self.api_thread.start()
        self.setWindowTitle("Procesador de Excel")
        self.setWindowIcon(QIcon('styles/logo.png'))
        layout = QVBoxLayout(self)

        #Conectamos señales
        self.pedir_hojas.connect(self.api.get_hojas)
        self.pedir_columnas.connect(self.api.get_columnas)
        self.pedir_conteos.connect(self.api.get_conteos)

        self.api.hojas_listas.connect(self.hoja_lista)
        self.api.columnas_listas.connect(self.columnas_listas)
        self.api.conteos_listos.connect(self.conteos_listos)

        # Panels
        self.topbar = QWidget()
        self.topbarLayout = QHBoxLayout(self.topbar)
        self.CentralPanel = QWidget()
        self.CentralLayout = QHBoxLayout(self.CentralPanel)
        # Widgets

            #Button (needs a slot function if clicked)
        self.button = QPushButton("Selecciona tu archivo")
        self.button.clicked.connect(self.buttonpress)

            # Tabla
        self.tabla = QTableWidget(5,2)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setHorizontalHeaderLabels(['Valor','Repeticiones'])

            #ComboBox (hojas)
        self.hojas = QComboBox()
        self.hojas.setVisible(False)
        self.hojas.activated.connect(self.hoja_elegida)

            #ComboBox (Columnas)
        self.columnas = QComboBox()
        self.columnas.setVisible(False)
        self.columnas.activated.connect(self.columna_elegida)

            #adding widgets to a layout which has a container as father
        layout.addWidget(self.topbar)
        layout.addWidget(self.CentralPanel)
        self.topbarLayout.addWidget(self.button)
        self.topbarLayout.addWidget(self.hojas)
        self.topbarLayout.addWidget(self.columnas)
        self.CentralLayout.addWidget(self.tabla)
    # Slots

    # Botón presionado
    @Slot()
    def buttonpress(self):
        # File chooser
        filename, filtro = QFileDialog.getOpenFileName(
            self,  # padre
            'Selecciona el excel',  # titulo
            '',  # carpeta inicial
            'Archivos Excel(*.xlsx)'
        )
        if filename:
            self.filename = filename
            self.columnas.setVisible(False)
            self.hojas.setVisible(False)
            self.hojas.clear()

            self.pedir_hojas.emit(filename)

    # Hoja Elegida

    @Slot()
    def hoja_elegida(self):
        self.columnas.clear()
        hoja = self.hojas.currentText()
        self.pedir_columnas.emit(self.filename,hoja)

    # Columna elegida

    @Slot()
    def columna_elegida(self):
            hoja = self.hojas.currentText()
            columna = self.columnas.currentIndex()
            self.pedir_conteos.emit(self.filename,hoja,columna)
    #Api response Slots
    @Slot(object)
    def hoja_lista(self,hojas):
        self.hojas.addItems(hojas)
        self.hojas.setVisible(True)

    @Slot(object)
    def columnas_listas(self, columnas):
        self.columnas.addItems(columnas)
        self.columnas.setVisible(True)

    @Slot(object)
    def conteos_listos(self, conteos):
        populate(self.tabla,conteos)

        # Funciones
    def closeEvent(self,event):
        self.api_thread.quit()
        self.api_thread.wait()
        self.api.session.close()
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(api.pid)])
        api.wait()
        event.accept()

#main loop
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Style
    style = CatppuccinStyle()
    app.setStyle(style)
    app.setPalette(style.create_palette())
    ventana = Ventana()
    ventana.show()
    sys.exit(app.exec())