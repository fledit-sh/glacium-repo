# node_editor_demo.py
# pip install PySide6
import sys
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, QPointF, QRectF, QLineF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QMenu,
)

# -----------------------------
# Styling helpers
# -----------------------------
def pen(color: QColor, w: float = 1.5) -> QPen:
    p = QPen(color)
    p.setWidthF(w)
    p.setCosmetic(True)  # width independent of zoom
    return p

def brush(color: QColor) -> QBrush:
    return QBrush(color)

# -----------------------------
# Port
# -----------------------------
@dataclass(frozen=True)
class PortSpec:
    kind: str  # "in" or "out"
    name: str

class PortItem(QGraphicsEllipseItem):
    R = 6.0

    def __init__(self, node: "NodeItem", spec: PortSpec, parent: Optional[QGraphicsItem] = None):
        super().__init__(-self.R, -self.R, 2 * self.R, 2 * self.R, parent)
        self.node = node
        self.spec = spec
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)

        base = QColor("#4B5563")  # gray
        if spec.kind == "in":
            base = QColor("#2563EB")  # blue
        else:
            base = QColor("#F59E0B")  # amber

        self._base_color = base
        self._hover = False
        self.update_style()

    def update_style(self):
        c = QColor(self._base_color)
        if self._hover:
            c = c.lighter(130)
        self.setBrush(brush(c))
        self.setPen(pen(QColor("#111827"), 1.0))

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update_style()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update_style()
        super().hoverLeaveEvent(event)

    def center_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(0.0, 0.0))

# -----------------------------
# Edge
# -----------------------------
class EdgeItem(QGraphicsPathItem):
    def __init__(self, src_port: PortItem, dst_port: Optional[PortItem] = None):
        super().__init__()
        self.src_port = src_port
        self.dst_port = dst_port
        self._dst_pos = src_port.center_scene_pos()

        self.setZValue(-10)  # behind nodes
        self.setPen(pen(QColor("#10B981"), 2.0))  # green

        self.rebuild_path()

    def set_dst_pos(self, pos: QPointF):
        self._dst_pos = pos
        self.rebuild_path()

    def set_dst_port(self, port: PortItem):
        self.dst_port = port
        self.rebuild_path()

    def rebuild_path(self):
        p0 = self.src_port.center_scene_pos()
        p3 = self.dst_port.center_scene_pos() if self.dst_port else self._dst_pos

        dx = max(60.0, abs(p3.x() - p0.x()) * 0.5)
        c1 = QPointF(p0.x() + dx, p0.y())
        c2 = QPointF(p3.x() - dx, p3.y())

        path = QPainterPath(p0)
        path.cubicTo(c1, c2, p3)
        self.setPath(path)

# -----------------------------
# Node
# -----------------------------
class NodeItem(QGraphicsRectItem):
    def __init__(self, title: str = "Node", w: float = 160.0, h: float = 90.0):
        super().__init__(0.0, 0.0, w, h)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        self.title_item = QGraphicsTextItem(title, self)
        self.title_item.setDefaultTextColor(QColor("#E5E7EB"))
        self.title_item.setPos(10.0, 6.0)

        self._hover = False
        self._ports_in: list[PortItem] = []
        self._ports_out: list[PortItem] = []

        self.add_port(PortSpec("in", "in"))
        self.add_port(PortSpec("out", "out"))

        self.update_style()
        self.layout_ports()

    def add_port(self, spec: PortSpec):
        port = PortItem(self, spec, self)
        if spec.kind == "in":
            self._ports_in.append(port)
        else:
            self._ports_out.append(port)

    def layout_ports(self):
        # simple: stack ports
        top = 35.0
        gap = 20.0

        for i, p in enumerate(self._ports_in):
            p.setPos(0.0, top + i * gap)  # left edge
        for i, p in enumerate(self._ports_out):
            p.setPos(self.rect().width(), top + i * gap)  # right edge

    def ports_in(self) -> list[PortItem]:
        return self._ports_in

    def ports_out(self) -> list[PortItem]:
        return self._ports_out

    def update_style(self):
        base = QColor("#111827")  # near-black
        border = QColor("#374151")  # gray border
        if self.isSelected():
            border = QColor("#60A5FA")  # blue highlight
        if self._hover:
            base = base.lighter(110)

        self.setBrush(brush(base))
        self.setPen(pen(border, 2.0))

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update_style()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update_style()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            # will update after selection actually changes, handled in scene/view by calling update_style
            pass
        if change == QGraphicsItem.ItemPositionHasChanged:
            # scene will update edge geometry via view hooking (kept simple)
            scene = self.scene()
            if scene and hasattr(scene, "request_edges_rebuild"):
                scene.request_edges_rebuild()
        return super().itemChange(change, value)

# -----------------------------
# Scene + View
# -----------------------------
class NodeScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.setSceneRect(-2000, -2000, 4000, 4000)

        self._drag_edge: Optional[EdgeItem] = None
        self._drag_src_port: Optional[PortItem] = None

        self._edges: list[EdgeItem] = []

        # grid colors
        self._grid_minor = QColor(255, 255, 255, 18)
        self._grid_major = QColor(255, 255, 255, 30)

    def add_node(self, pos: QPointF, title: str):
        n = NodeItem(title=title)
        n.setPos(pos)
        self.addItem(n)
        return n

    def add_edge(self, e: EdgeItem):
        self._edges.append(e)
        self.addItem(e)

    def request_edges_rebuild(self):
        for e in self._edges:
            e.rebuild_path()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        painter.save()

        painter.fillRect(rect, QColor("#0B1220"))

        # grid
        minor = 25
        major = 100

        left = int(rect.left()) - (int(rect.left()) % minor)
        top = int(rect.top()) - (int(rect.top()) % minor)

        # minor lines
        painter.setPen(pen(self._grid_minor, 1.0))
        x = left
        while x < rect.right():
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += minor
        y = top
        while y < rect.bottom():
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
            y += minor

        # major lines
        left = int(rect.left()) - (int(rect.left()) % major)
        top = int(rect.top()) - (int(rect.top()) % major)
        painter.setPen(pen(self._grid_major, 1.2))
        x = left
        while x < rect.right():
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += major
        y = top
        while y < rect.bottom():
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
            y += major

        painter.restore()

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None

        # start edge drag if clicking on output port
        if isinstance(item, PortItem) and item.spec.kind == "out" and event.button() == Qt.LeftButton:
            self._drag_src_port = item
            self._drag_edge = EdgeItem(src_port=item)
            self.add_edge(self._drag_edge)
            self._drag_edge.set_dst_pos(event.scenePos())
            event.accept()
            return

        super().mousePressEvent(event)

        # refresh selection visuals
        for it in self.selectedItems():
            if isinstance(it, NodeItem):
                it.update_style()

    def mouseMoveEvent(self, event):
        if self._drag_edge:
            self._drag_edge.set_dst_pos(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_edge and self._drag_src_port:
            item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None
            if isinstance(item, PortItem) and item.spec.kind == "in":
                # connect if not same node
                if item.node is not self._drag_src_port.node:
                    self._drag_edge.set_dst_port(item)
                    self._drag_edge.rebuild_path()
                else:
                    self.removeItem(self._drag_edge)
                    self._edges.remove(self._drag_edge)
            else:
                # drop nowhere => cancel
                self.removeItem(self._drag_edge)
                self._edges.remove(self._drag_edge)

            self._drag_edge = None
            self._drag_src_port = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

        # refresh selection visuals
        for it in self.items():
            if isinstance(it, NodeItem):
                it.update_style()

class NodeView(QGraphicsView):
    def __init__(self, scene: NodeScene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self._panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event):
        # zoom
        factor = 1.0015 ** event.angleDelta().y()
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_add = menu.addAction("Add Node")
        act = menu.exec(event.globalPos())
        if act == act_add:
            scene_pos = self.mapToScene(event.pos())
            s: NodeScene = self.scene()  # type: ignore
            idx = sum(isinstance(i, NodeItem) for i in s.items())
            s.add_node(scene_pos, f"Node {idx + 1}")

# -----------------------------
# main
# -----------------------------
def main():
    app = QApplication(sys.argv)
    scene = NodeScene()

    # seed nodes
    a = scene.add_node(QPointF(-200, -80), "Source")
    b = scene.add_node(QPointF(120, 40), "Sink")

    # initial edge
    e = EdgeItem(a.ports_out()[0], b.ports_in()[0])
    scene.add_edge(e)

    view = NodeView(scene)
    view.setWindowTitle("PySide6 Node Editor Demo")
    view.resize(1100, 700)
    view.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()