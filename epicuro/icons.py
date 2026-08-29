from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


FG = QColor("#DCE7F3")
ACCENT = QColor("#69A8FF")
CYAN = QColor("#5ED6F5")
GREEN = QColor("#5BD892")
RED = QColor("#FF7185")
AMBER = QColor("#F4C663")
PURPLE = QColor("#B79AFF")
MUTED = QColor("#8A9AAF")


def _pen(color: QColor, width: float) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _accent_for(name: str) -> QColor:
    if name in {"play", "done"}:
        return GREEN
    if name in {"stop", "trash", "error", "exit", "cleanup"}:
        return RED
    if name == "pause":
        return AMBER
    if name in {"audio", "library"}:
        return PURPLE
    if name in {"folder", "copy", "file", "clipboard"}:
        return CYAN
    return ACCENT


def make_icon(name: str, size: int = 28, color: QColor | None = None) -> QIcon:
    """Draw crisp local line icons. No icon fonts, SVG bundles or network assets."""
    fg = color or FG
    accent = color or _accent_for(name)
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)

    s = float(size)
    thin = max(1.35, s / 17.5)
    bold = max(1.75, s / 14.0)
    cx = cy = s / 2
    p.setBrush(Qt.NoBrush)
    p.setPen(_pen(fg, thin))

    if name in {"new", "link"}:
        p.drawRoundedRect(QRectF(s*.22, s*.16, s*.46, s*.66), s*.06, s*.06)
        p.drawLine(QPointF(s*.31, s*.31), QPointF(s*.57, s*.31))
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.63, s*.61), QPointF(s*.82, s*.61))
        p.drawLine(QPointF(s*.725, s*.515), QPointF(s*.725, s*.705))

    elif name in {"analyze", "search"}:
        p.drawEllipse(QRectF(s*.18, s*.17, s*.47, s*.47))
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.57, s*.57), QPointF(s*.80, s*.80))
        if name == "analyze":
            p.setPen(_pen(fg, thin))
            p.drawLine(QPointF(s*.32, s*.34), QPointF(s*.50, s*.34))
            p.drawLine(QPointF(s*.41, s*.25), QPointF(s*.41, s*.43))

    elif name == "clipboard":
        p.drawRoundedRect(QRectF(s*.23, s*.22, s*.54, s*.61), s*.07, s*.07)
        p.setPen(_pen(accent, bold))
        p.drawRoundedRect(QRectF(s*.36, s*.14, s*.28, s*.16), s*.05, s*.05)
        p.drawLine(QPointF(s*.34, s*.46), QPointF(s*.66, s*.46))
        p.drawLine(QPointF(s*.34, s*.60), QPointF(s*.59, s*.60))

    elif name == "download":
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(cx, s*.17), QPointF(cx, s*.61))
        p.drawLine(QPointF(s*.36, s*.50), QPointF(cx, s*.64))
        p.drawLine(QPointF(s*.64, s*.50), QPointF(cx, s*.64))
        p.setPen(_pen(fg, thin))
        p.drawLine(QPointF(s*.24, s*.78), QPointF(s*.76, s*.78))

    elif name == "video":
        p.drawRoundedRect(QRectF(s*.16, s*.24, s*.68, s*.52), s*.08, s*.08)
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        path = QPainterPath()
        path.moveTo(s*.43, s*.36)
        path.lineTo(s*.67, s*.50)
        path.lineTo(s*.43, s*.64)
        path.closeSubpath()
        p.drawPath(path)

    elif name == "audio":
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.58, s*.20), QPointF(s*.58, s*.64))
        p.drawLine(QPointF(s*.58, s*.20), QPointF(s*.77, s*.25))
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        p.drawEllipse(QRectF(s*.27, s*.59, s*.31, s*.23))
        p.drawEllipse(QRectF(s*.63, s*.49, s*.20, s*.18))

    elif name == "library":
        p.drawRoundedRect(QRectF(s*.17, s*.18, s*.66, s*.64), s*.06, s*.06)
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.33, s*.18), QPointF(s*.33, s*.82))
        p.setPen(_pen(fg, thin))
        for y in (.36, .52, .68):
            p.drawLine(QPointF(s*.45, s*y), QPointF(s*.70, s*y))

    elif name == "folder":
        path = QPainterPath()
        path.moveTo(s*.15, s*.34)
        path.lineTo(s*.38, s*.34)
        path.lineTo(s*.46, s*.42)
        path.lineTo(s*.84, s*.42)
        path.lineTo(s*.79, s*.76)
        path.lineTo(s*.15, s*.76)
        path.closeSubpath()
        p.setPen(_pen(accent, bold))
        p.drawPath(path)
        p.setPen(_pen(fg, thin))
        p.drawLine(QPointF(s*.20, s*.52), QPointF(s*.75, s*.52))

    elif name == "file":
        path = QPainterPath()
        path.moveTo(s*.27, s*.16)
        path.lineTo(s*.59, s*.16)
        path.lineTo(s*.76, s*.33)
        path.lineTo(s*.76, s*.82)
        path.lineTo(s*.27, s*.82)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(s*.59, s*.16), QPointF(s*.59, s*.34))
        p.drawLine(QPointF(s*.59, s*.34), QPointF(s*.76, s*.34))
        p.setPen(_pen(accent, thin))
        p.drawLine(QPointF(s*.37, s*.52), QPointF(s*.66, s*.52))
        p.drawLine(QPointF(s*.37, s*.65), QPointF(s*.62, s*.65))

    elif name == "copy":
        p.drawRoundedRect(QRectF(s*.31, s*.29, s*.44, s*.49), s*.06, s*.06)
        p.setPen(_pen(accent, bold))
        p.drawRoundedRect(QRectF(s*.19, s*.18, s*.44, s*.49), s*.06, s*.06)

    elif name == "settings":
        for y, x in ((.29, .61), (.50, .40), (.71, .65)):
            p.setPen(_pen(fg, thin))
            p.drawLine(QPointF(s*.18, s*y), QPointF(s*.82, s*y))
            p.setPen(_pen(accent, bold))
            p.drawEllipse(QRectF(s*x-s*.045, s*y-s*.045, s*.09, s*.09))

    elif name == "tools":
        p.setPen(_pen(fg, thin))
        p.drawLine(QPointF(s*.25, s*.75), QPointF(s*.68, s*.32))
        p.drawEllipse(QRectF(s*.17, s*.67, s*.16, s*.16))
        p.setPen(_pen(accent, bold))
        p.drawArc(QRectF(s*.55, s*.15, s*.29, s*.29), 35*16, 210*16)

    elif name in {"diagnostic", "refresh"}:
        if name == "diagnostic":
            p.setPen(_pen(accent, bold))
            p.drawEllipse(QRectF(s*.18, s*.18, s*.64, s*.64))
            p.drawLine(QPointF(s*.28, s*.54), QPointF(s*.39, s*.54))
            p.drawLine(QPointF(s*.39, s*.54), QPointF(s*.46, s*.38))
            p.drawLine(QPointF(s*.46, s*.38), QPointF(s*.56, s*.65))
            p.drawLine(QPointF(s*.56, s*.65), QPointF(s*.66, s*.46))
            p.drawLine(QPointF(s*.66, s*.46), QPointF(s*.75, s*.46))
        else:
            p.setPen(_pen(accent, bold))
            p.drawArc(QRectF(s*.20, s*.20, s*.60, s*.60), 40*16, 265*16)
            p.drawLine(QPointF(s*.66, s*.20), QPointF(s*.80, s*.22))
            p.drawLine(QPointF(s*.80, s*.22), QPointF(s*.76, s*.36))

    elif name == "cleanup":
        p.setPen(_pen(fg, thin))
        p.drawLine(QPointF(s*.33, s*.72), QPointF(s*.66, s*.28))
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.23, s*.71), QPointF(s*.48, s*.81))
        p.drawLine(QPointF(s*.48, s*.81), QPointF(s*.62, s*.64))

    elif name == "help":
        p.drawEllipse(QRectF(s*.18, s*.18, s*.64, s*.64))
        p.setPen(_pen(accent, bold))
        p.drawArc(QRectF(s*.35, s*.28, s*.30, s*.25), 0, 175*16)
        p.drawLine(QPointF(cx, s*.52), QPointF(cx, s*.62))
        p.drawPoint(QPointF(cx, s*.71))

    elif name == "play":
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        path = QPainterPath()
        path.moveTo(s*.34, s*.25)
        path.lineTo(s*.73, cy)
        path.lineTo(s*.34, s*.75)
        path.closeSubpath()
        p.drawPath(path)

    elif name == "pause":
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        p.drawRoundedRect(QRectF(s*.28, s*.25, s*.15, s*.50), s*.03, s*.03)
        p.drawRoundedRect(QRectF(s*.57, s*.25, s*.15, s*.50), s*.03, s*.03)

    elif name == "stop":
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        p.drawRoundedRect(QRectF(s*.29, s*.29, s*.42, s*.42), s*.055, s*.055)

    elif name == "trash":
        p.drawRoundedRect(QRectF(s*.31, s*.34, s*.38, s*.43), s*.04, s*.04)
        p.drawLine(QPointF(s*.24, s*.29), QPointF(s*.76, s*.29))
        p.drawLine(QPointF(s*.40, s*.22), QPointF(s*.60, s*.22))
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.43, s*.43), QPointF(s*.43, s*.66))
        p.drawLine(QPointF(s*.57, s*.43), QPointF(s*.57, s*.66))

    elif name in {"up", "down"}:
        p.setPen(_pen(accent, bold))
        if name == "up":
            p.drawLine(QPointF(cx, s*.74), QPointF(cx, s*.26))
            p.drawLine(QPointF(cx, s*.26), QPointF(s*.35, s*.42))
            p.drawLine(QPointF(cx, s*.26), QPointF(s*.65, s*.42))
        else:
            p.drawLine(QPointF(cx, s*.26), QPointF(cx, s*.74))
            p.drawLine(QPointF(cx, s*.74), QPointF(s*.35, s*.58))
            p.drawLine(QPointF(cx, s*.74), QPointF(s*.65, s*.58))

    elif name == "all":
        for y in (.31, .50, .69):
            p.setPen(Qt.NoPen)
            p.setBrush(accent if y == .50 else MUTED)
            p.drawEllipse(QRectF(s*.20, s*y-s*.035, s*.07, s*.07))
            p.setBrush(Qt.NoBrush)
            p.setPen(_pen(fg, thin))
            p.drawLine(QPointF(s*.36, s*y), QPointF(s*.79, s*y))

    elif name == "error":
        p.setPen(_pen(accent, bold))
        p.drawEllipse(QRectF(s*.19, s*.19, s*.62, s*.62))
        p.drawLine(QPointF(s*.38, s*.38), QPointF(s*.62, s*.62))
        p.drawLine(QPointF(s*.62, s*.38), QPointF(s*.38, s*.62))

    elif name == "done":
        p.setPen(_pen(accent, bold))
        p.drawEllipse(QRectF(s*.19, s*.19, s*.62, s*.62))
        p.drawLine(QPointF(s*.32, s*.51), QPointF(s*.45, s*.64))
        p.drawLine(QPointF(s*.45, s*.64), QPointF(s*.70, s*.38))

    elif name == "exit":
        p.drawRoundedRect(QRectF(s*.21, s*.19, s*.37, s*.62), s*.05, s*.05)
        p.setPen(_pen(accent, bold))
        p.drawLine(QPointF(s*.46, cy), QPointF(s*.81, cy))
        p.drawLine(QPointF(s*.69, s*.39), QPointF(s*.81, cy))
        p.drawLine(QPointF(s*.69, s*.61), QPointF(s*.81, cy))

    else:
        p.setPen(_pen(accent, bold))
        p.drawEllipse(QRectF(s*.22, s*.22, s*.56, s*.56))

    p.end()
    return QIcon(pm)
