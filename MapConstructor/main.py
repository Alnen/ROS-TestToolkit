import enum
import logging
import os
import sys

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic


class MapSceneContainer(QtGui.QGraphicsScene):

    class InteractionMode(enum.Enum):
        CREATION = 1
        EDITING = 2

    class Figures(enum.Enum):
        RECTANGLE = 1
        ROBOT_REFERENCE = 2

    DEFAULT_RECT_SIZE = QtCore.QSizeF(10, 10)

    def __init__(self, *__args):
        super().__init__(*__args)
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)
        self.mode = MapSceneContainer.InteractionMode.CREATION
        self.start_position = None
        self.current_item = None
        self.position_diff = None

    def switch_interaction_state(self):
        if self.mode == MapSceneContainer.InteractionMode.CREATION:
            self.mode = MapSceneContainer.InteractionMode.EDITING
        elif self.mode == MapSceneContainer.InteractionMode.EDITING:
            self.mode = MapSceneContainer.InteractionMode.CREATION

    def mousePressEvent(self, graphics_scene_mouse_event):
        super().mousePressEvent(graphics_scene_mouse_event)
        if self.mode == MapSceneContainer.InteractionMode.CREATION:
            self.start_position = QtCore.QPointF(graphics_scene_mouse_event.scenePos())
            self.current_item = self.addRect(
                self.start_position.x(),
                self.start_position.y(),
                MapSceneContainer.DEFAULT_RECT_SIZE.width(),
                MapSceneContainer.DEFAULT_RECT_SIZE.height(),
                QtGui.QPen(QtGui.QColor(0, 0, 0)),
                QtGui.QBrush(QtGui.QColor(0, 0, 0))
            )
        elif self.mode == MapSceneContainer.InteractionMode.EDITING:
            self.current_item = self.itemAt(graphics_scene_mouse_event.scenePos())
            if self.current_item is not None:
                self.position_diff = graphics_scene_mouse_event.scenePos() - self.current_item.scenePos()

    def mouseMoveEvent(self, graphics_scene_mouse_event):
        super().mouseMoveEvent(graphics_scene_mouse_event)
        if self.current_item is not None:
            if self.mode == MapSceneContainer.InteractionMode.CREATION:
                width = abs(self.start_position.x() - graphics_scene_mouse_event.scenePos().x())
                height = abs(self.start_position.y() - graphics_scene_mouse_event.scenePos().y())

                if self.start_position.x() < graphics_scene_mouse_event.scenePos().x():
                    start_x = self.start_position.x()
                else:
                    start_x = graphics_scene_mouse_event.scenePos().x()

                if self.start_position.y() < graphics_scene_mouse_event.scenePos().y():
                    start_y = self.start_position.y()
                else:
                    start_y = graphics_scene_mouse_event.scenePos().y()

                self.current_item.setRect(start_x, start_y, width, height)

            elif self.mode == MapSceneContainer.InteractionMode.EDITING:
                old_position = self.current_item.pos()
                self.current_item.setPos(graphics_scene_mouse_event.scenePos() - self.position_diff)
                if len(self.collidingItems(self.current_item)) != 0:
                    self.current_item.setPos(old_position)

    def mouseReleaseEvent(self, graphics_scene_mouse_event):
        super().mouseReleaseEvent(graphics_scene_mouse_event)
        self.start_position = None
        self.current_item = None

    def keyPressEvent(self, qkeyevent):
        super().keyPressEvent(qkeyevent)
        if qkeyevent.key() == QtCore.Qt.Key_Escape:
            if self.mode == MapSceneContainer.InteractionMode.CREATION:
                self.removeItem(self.current_item)
                self.current_item = None
            elif self.mode == MapSceneContainer.InteractionMode.EDITING:
                self.current_item = None


class MainWindow(QtGui.QMainWindow):

    def generate_image(self):
        self.image = QtGui.QPixmap.grabWidget(self.ui.graphicsview)

    def generate_xml_map_description(self):
        xml_text_stream = QtCore.QByteArray()
        xml_stream_writer = QtCore.QXmlStreamWriter(xml_text_stream)
        xml_stream_writer.setAutoFormatting(True)
        xml_stream_writer.setAutoFormattingIndent(2)
        xml_stream_writer.writeStartDocument()
        xml_stream_writer.writeStartElement('scene')
        xml_stream_writer.writeTextElement('width', str(100))
        xml_stream_writer.writeTextElement('height', str(100))
        xml_stream_writer.writeStartElement('objects')
        for item in self.graphics_scene.items():
            xml_stream_writer.writeStartElement('rectangle')
            xml_stream_writer.writeTextElement('x', str(item.scenePos().x()))
            xml_stream_writer.writeTextElement('y', str(item.scenePos().y()))
            xml_stream_writer.writeTextElement('width', str(item.rect().width()))
            xml_stream_writer.writeTextElement('height', str(item.rect().height()))
            xml_stream_writer.writeEndElement()
        xml_stream_writer.writeEndDocument()
        self.xml_map_description = xml_text_stream.data().decode()

    def generatefromconstructor(self):
        self.generate_image()
        self.generate_xml_map_description()
        self.ui.xml_browser.setText(self.xml_map_description)
        self.ui.lb_image.setPixmap(self.image)

    def saveimagetodisk(self):
        self.generate_image()
        filename = QtGui.QFileDialog.getSaveFileName()
        self.logger.info('Map was saved to file: %s', filename)
        self.image.save(filename)

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.logger = logging.getLogger(self.__module__ + '.' + self.__class__.__name__)
        self.image = None
        self.xml_map_description = None

        self.resize(250, 150)
        self.move(300, 300)
        self.setWindowTitle('Simple')

        self.graphics_scene = MapSceneContainer(QtCore.QRectF(0.0, 0.0, 100.0, 100.0))
        ui_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "forms", 'mainwindow.ui')
        self.ui = uic.loadUi(ui_path, self)
        self.ui.graphicsview.setScene(self.graphics_scene)
        self.ui.graphicsview.setMouseTracking(True)
        self.ui.pb_switchInteractionMode.clicked.connect(lambda: self.graphics_scene.switch_interaction_state())
        self.ui.pb_generate.clicked.connect(lambda: self.generatefromconstructor())
        self.ui.pb_save.clicked.connect(lambda: self.saveimagetodisk())


def main(argv):
    app = QtGui.QApplication(argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


def configure_loggers():
    # configure logger
    rootlogger = logging.getLogger()
    rootlogger.setLevel(logging.DEBUG)
    stdouthandler = logging.StreamHandler(sys.stdout)
    stdouthandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s')
    stdouthandler.setFormatter(formatter)
    rootlogger.addHandler(stdouthandler)
    # PyQT logger
    qtlogger = logging.getLogger('PyQt4')
    qtlogger.setLevel(logging.INFO)

if __name__ == '__main__':
    configure_loggers()
    main(sys.argv)
