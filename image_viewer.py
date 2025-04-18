#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
可缩放图像查看器组件

提供以下功能：
- 图像缩放（鼠标滚轮）
- 图像平移（鼠标拖动）
- 自动适应窗口大小
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter, QColor
from PyQt6.QtCore import Qt, QRectF


class ZoomableImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建场景和图元
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # 创建图像项
        self.image_item = QGraphicsPixmapItem()
        self.scene.addItem(self.image_item)
        
        # 设置渲染提示
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | 
            QPainter.RenderHint.SmoothPixmapTransform
        )
        
        # 设置拖动模式
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # 设置背景颜色
        self.setBackgroundBrush(QColor(240, 240, 240))
        
        # 设置调整大小模式
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # 适应视图模式
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # 跟踪缩放级别
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
        # 当前加载的图像路径
        self.current_image_path = None
        
        # 设置提示文本
        self.setToolTip("滚轮: 缩放 | 拖动: 平移")

    def load_image(self, image_path):
        """加载图像并调整视图大小"""
        if not image_path:
            return False
            
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return False
            
        # 更新图像项
        self.image_item.setPixmap(pixmap)
        
        # 重置变换
        self.resetTransform()
        self.zoom_factor = 1.0
        
        # 调整场景大小
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        # 调整视图以适应场景
        self.fit_in_view()
        
        # 保存当前图像路径
        self.current_image_path = image_path
        
        return True
        
    def fit_in_view(self):
        """调整视图以适应整个图像"""
        if self.image_item.pixmap().isNull():
            return
            
        # 适应视图大小
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # 更新缩放系数
        transform = self.transform()
        self.zoom_factor = transform.m11()  # 水平缩放系数

    def wheelEvent(self, event: QWheelEvent):
        """处理鼠标滚轮事件以实现缩放"""
        if self.image_item.pixmap().isNull():
            return
            
        # 获取鼠标滚轮的角度增量
        delta = event.angleDelta().y()
        
        # 缩放系数
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # 确定缩放方向
        if delta > 0:
            # 放大
            zoom_factor = zoom_in_factor
        else:
            # 缩小
            zoom_factor = zoom_out_factor
            
        # 计算新的缩放系数
        new_zoom = self.zoom_factor * zoom_factor
        
        # 确保缩放系数在合理范围内
        if new_zoom < self.min_zoom:
            zoom_factor = self.min_zoom / self.zoom_factor
        elif new_zoom > self.max_zoom:
            zoom_factor = self.max_zoom / self.zoom_factor
            
        # 应用缩放
        self.scale(zoom_factor, zoom_factor)
        self.zoom_factor *= zoom_factor
        
    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        
        if not self.image_item.pixmap().isNull():
            # 如果缩放系数接近1.0，则重新适应视图
            if 0.9 < self.zoom_factor < 1.1:
                self.fit_in_view() 