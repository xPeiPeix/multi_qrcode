#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多QR码阵列生成与读取 - 图形用户界面

基于PyQt6的用户界面，提供以下功能：
- 文本输入和粘贴
- 文件选择和导入
- QR码阵列生成配置
- QR码阵列生成和解码
- 日志查看和导出
"""

import os
import sys
import time
import traceback
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QSpinBox, QTabWidget,
    QGroupBox, QFormLayout, QLineEdit, QMessageBox, QComboBox, QSplitter,
    QCheckBox, QProgressBar, QPlainTextEdit, QScrollArea, QStyle,
    QStyleFactory
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QMimeData, QEvent
from PyQt6.QtGui import QPixmap, QImage, QFont, QIntValidator, QTextOption, QIcon, QDragEnterEvent, QDropEvent, QKeyEvent, QClipboard, QColor

# 导入QR码阵列生成与读取功能
from generate_qr_array import create_qr_array
from read_qr_array import read_qr_array
from qr_code_file_transfer import encode_file_to_qr_array, decode_qr_array_to_file

# 导入图像查看器
from image_viewer import ZoomableImageViewer

# QR码相关常量
QR_VERSION_MAX = 40  # QR码最大版本
QR_MAX_CHARS = {
    # QR码各版本最大字符数 (使用L级别错误校正的估计值)
    # 以下是各种数据类型的大致容量，实际会根据字符集和混合类型有所不同
    'numeric': 7089,        # 数字
    'alphanumeric': 4296,   # 字母数字
    'binary': 2953,         # 二进制
    'kanji': 1817,          # 汉字/日文
    'utf8': 850             # UTF-8通用估计值（更保守的设置，考虑QR版本限制）
}

# QR码块大小推荐值（字符数限制，基于不同类型文本）
QR_RECOMMENDED_CHUNK_SIZE = {
    'plain_ascii': 850,     # 纯ASCII文本（较大值）
    'mixed': 700,           # 混合文本（较大值）
    'chinese': 500,         # 中文/非ASCII文本（较大值）
}

# 工作线程类，用于在后台执行长时间操作
class WorkerThread(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, function, args=None, kwargs=None):
        super().__init__()
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
    
    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"错误: {str(e)}\n{traceback.format_exc()}")

# 自定义日志类，将日志输出重定向到界面
class LogHandler:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.log_contents = []
    
    def write(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.log_contents.append(log_entry)
        self.text_widget.append(log_entry)
        # 自动滚动到底部
        self.text_widget.ensureCursorVisible()
    
    def export_log(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.log_contents))
        return True

# 自定义纯文本编辑器，用于去除格式化内容
class PlainTextInputWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("在此输入或粘贴要编码的文本...\n注意：将自动移除所有粘贴的文本格式")
        self.textChanged.connect(self.update_char_count)
        self.char_count_label = None
        self.max_chars = QR_MAX_CHARS['utf8']
        self.warning_threshold = 0.8  # 80%警告阈值
        
        # 设置自动换行
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
    
    def set_char_count_label(self, label):
        self.char_count_label = label
        self.update_char_count()
    
    def set_max_chars(self, max_chars):
        self.max_chars = max_chars
        self.update_char_count()
        
    def update_char_count(self):
        if self.char_count_label:
            text = self.toPlainText()
            count = len(text)
            status = "正常"
            style = "color: black;"
            
            if count > self.max_chars:
                status = "超出限制"
                style = "color: red; font-weight: bold;"
            elif count > self.max_chars * self.warning_threshold:
                status = "接近限制"
                style = "color: orange; font-weight: bold;"
                
            self.char_count_label.setText(f"字符数: {count}/{self.max_chars} ({status})")
            self.char_count_label.setStyleSheet(style)
            
            # 设置背景颜色以视觉提示字符限制
            if count > self.max_chars:
                self.setStyleSheet("background-color: #fff0f0;")  # 轻微红色背景
            elif count > self.max_chars * self.warning_threshold:
                self.setStyleSheet("background-color: #fffaf0;")  # 轻微黄色背景
            else:
                self.setStyleSheet("")  # 恢复默认背景
    
    def insertFromMimeData(self, source):
        # 仅粘贴纯文本，去除所有格式
        if source.hasText():
            self.insertPlainText(source.text())

# 添加可接收粘贴事件的标签组件
class ImageDropZone(QWidget):
    """可以接收拖放和粘贴图像的区域"""
    
    # 定义信号
    image_pasted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建标签
        self.drop_label = QLabel("拖放图像到此处\n或按Ctrl+V粘贴")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            background-color: #f5f5f5;
            border: 2px dashed #cccccc;
            border-radius: 8px;
            padding: 20px;
            font-size: 14px;
            color: #666666;
        """)
        
        # 添加到布局
        layout.addWidget(self.drop_label)
        
        # 启用焦点
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘按键事件"""
        # 检测Ctrl+V组合键
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.handle_paste()
        else:
            super().keyPressEvent(event)
    
    def handle_paste(self):
        """处理粘贴事件"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # 从剪贴板获取图像
            image = clipboard.image()
            
            if not image.isNull():
                # 创建临时文件保存图像
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, f"pasted_image_{int(time.time())}.png")
                
                # 保存图像
                if image.save(temp_file, "PNG"):
                    # 发出信号
                    self.image_pasted.emit(temp_file)
                    
                    # 更新提示文本
                    self.drop_label.setText(f"图像已从剪贴板粘贴\n{os.path.basename(temp_file)}")
                    return
        
        # 如果没有图像或保存失败，显示错误消息
        self.drop_label.setText("无法从剪贴板粘贴图像\n请确保剪贴板包含有效图像")

# 主窗口类
class QRArrayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_image_path = None
        self.workers = []
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('多QR码阵列生成与读取')
        self.setMinimumSize(1000, 750)
        
        # 设置应用样式
        self.setStyle(QStyleFactory.create('Fusion'))
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)  # 使用更现代的选项卡样式
        text_tab = QWidget()
        file_tab = QWidget()
        decode_tab = QWidget()
        
        # 添加选项卡
        self.tabs.addTab(text_tab, "文本编码")
        self.tabs.addTab(file_tab, "文件编码")
        self.tabs.addTab(decode_tab, "图像解码")
        
        # 文本编码选项卡布局
        text_layout = QVBoxLayout(text_tab)
        text_layout.setContentsMargins(15, 15, 15, 15)
        
        # 文本输入区域
        text_input_group = QGroupBox("文本输入")
        text_input_layout = QVBoxLayout()
        text_input_layout.setSpacing(8)
        
        # 添加说明标签
        input_info_label = QLabel("在此输入或粘贴要编码为QR码的文本。系统将自动移除粘贴文本的所有格式。")
        input_info_label.setStyleSheet("color: #666; font-style: italic;")
        text_input_layout.addWidget(input_info_label)
        
        self.text_input = PlainTextInputWidget()
        self.char_count_label = QLabel("字符数: 0/850 (正常)")
        self.text_input.set_char_count_label(self.char_count_label)
        
        text_input_layout.addWidget(self.text_input)
        text_input_layout.addWidget(self.char_count_label)
        text_input_group.setLayout(text_input_layout)
        
        # 文本编码选项
        text_options_group = QGroupBox("编码选项")
        text_options_layout = QFormLayout()
        text_options_layout.setVerticalSpacing(10)
        
        self.text_chunk_size = QSpinBox()
        self.text_chunk_size.setRange(100, 850)  # 增加最小值到100，保持大尺寸QR码
        self.text_chunk_size.setValue(500)  # 增加默认值为500
        self.text_chunk_size.setSingleStep(50)
        self.text_chunk_size.valueChanged.connect(self.update_max_chars)
        text_options_layout.addRow("每个QR码字符数:", self.text_chunk_size)
        
        chunk_size_info = QLabel(
            "推荐值: 纯ASCII文本 (850), 混合文本 (700), 中文文本 (500)"
        )
        chunk_size_info.setStyleSheet("color: #666; font-style: italic;")
        text_options_layout.addRow("", chunk_size_info)
        
        self.text_cols = QSpinBox()
        self.text_cols.setRange(1, 10)
        self.text_cols.setValue(3)
        text_options_layout.addRow("列数:", self.text_cols)
        
        self.text_rows = QSpinBox()
        self.text_rows.setRange(0, 10)
        self.text_rows.setValue(0)
        self.text_rows.setSpecialValueText("自动")
        text_options_layout.addRow("行数:", self.text_rows)
        
        # 创建水平布局用于文件名和浏览按钮
        output_file_layout = QHBoxLayout()
        
        self.text_output_file = QLineEdit("text_qr_array.png")
        output_file_layout.addWidget(self.text_output_file)
        
        self.text_output_browse = QPushButton("浏览...")
        self.text_output_browse.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.text_output_browse.clicked.connect(self.browse_text_output)
        self.text_output_browse.setMaximumWidth(100)
        output_file_layout.addWidget(self.text_output_browse)
        
        text_options_layout.addRow("输出文件名:", output_file_layout)
        
        text_options_group.setLayout(text_options_layout)
        
        # 文本编码操作按钮
        text_actions_layout = QHBoxLayout()
        self.generate_text_button = QPushButton("生成QR码阵列")
        self.generate_text_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.generate_text_button.setStyleSheet("font-weight: bold; padding: 8px;")
        self.generate_text_button.clicked.connect(self.generate_text_qr_array)
        text_actions_layout.addWidget(self.generate_text_button)
        
        # 添加组件到文本编码选项卡
        text_layout.addWidget(text_input_group, 3)
        text_layout.addWidget(text_options_group, 1)
        text_layout.addLayout(text_actions_layout)
        
        # 文件编码选项卡布局
        file_layout = QVBoxLayout(file_tab)
        file_layout.setContentsMargins(15, 15, 15, 15)
        
        # 文件选择
        file_select_group = QGroupBox("文件选择")
        file_select_layout = QFormLayout()
        file_select_layout.setVerticalSpacing(10)
        
        # 文件路径和浏览按钮水平布局
        file_path_layout = QHBoxLayout()
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("请选择要编码的文件或将文件拖放到此处...")
        file_path_layout.addWidget(self.file_path)
        
        self.file_browse = QPushButton("浏览...")
        self.file_browse.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.file_browse.clicked.connect(self.browse_input_file)
        self.file_browse.setMaximumWidth(100)
        file_path_layout.addWidget(self.file_browse)
        
        file_select_layout.addRow("文件路径:", file_path_layout)
        
        file_select_group.setLayout(file_select_layout)
        
        # 文件编码选项
        file_options_group = QGroupBox("编码选项")
        file_options_layout = QFormLayout()
        file_options_layout.setVerticalSpacing(10)
        
        self.file_chunk_size = QSpinBox()
        self.file_chunk_size.setRange(100, 850)  # 保持上限为850
        self.file_chunk_size.setValue(700)  # 增加默认值到700
        self.file_chunk_size.setSingleStep(50)
        file_options_layout.addRow("每个QR码字符数:", self.file_chunk_size)
        
        file_chunk_size_info = QLabel(
            "较大的字符数可更有效地传输文件\n"
            "注意：使用高分辨率扫描设备以确保成功解码大型QR码"
        )
        file_chunk_size_info.setStyleSheet("color: #666; font-style: italic;")
        file_options_layout.addRow("", file_chunk_size_info)
        
        self.file_cols = QSpinBox()
        self.file_cols.setRange(1, 10)
        self.file_cols.setValue(4)
        file_options_layout.addRow("列数:", self.file_cols)
        
        self.file_rows = QSpinBox()
        self.file_rows.setRange(0, 10)
        self.file_rows.setValue(0)
        self.file_rows.setSpecialValueText("自动")
        file_options_layout.addRow("行数:", self.file_rows)
        
        # 文件输出目录水平布局
        file_output_layout = QHBoxLayout()
        
        self.file_output_dir = QLineEdit("output")
        file_output_layout.addWidget(self.file_output_dir)
        
        self.file_output_browse = QPushButton("浏览...")
        self.file_output_browse.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.file_output_browse.clicked.connect(self.browse_file_output_dir)
        self.file_output_browse.setMaximumWidth(100)
        file_output_layout.addWidget(self.file_output_browse)
        
        file_options_layout.addRow("输出目录:", file_output_layout)
        
        file_options_group.setLayout(file_options_layout)
        
        # 文件编码操作按钮
        file_actions_layout = QHBoxLayout()
        self.generate_file_button = QPushButton("生成QR码阵列")
        self.generate_file_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.generate_file_button.setStyleSheet("font-weight: bold; padding: 8px;")
        self.generate_file_button.clicked.connect(self.generate_file_qr_array)
        file_actions_layout.addWidget(self.generate_file_button)
        
        # 添加组件到文件编码选项卡
        file_layout.addWidget(file_select_group, 1)
        file_layout.addWidget(file_options_group, 2)
        file_layout.addLayout(file_actions_layout)
        
        # 解码选项卡布局
        decode_layout = QVBoxLayout(decode_tab)
        decode_layout.setContentsMargins(15, 15, 15, 15)
        
        # 图像选择
        image_select_group = QGroupBox("图像选择")
        image_select_layout = QFormLayout()
        image_select_layout.setVerticalSpacing(10)
        
        # 图像路径和浏览按钮水平布局
        image_path_layout = QHBoxLayout()
        
        self.image_path = QLineEdit()
        self.image_path.setReadOnly(True)
        self.image_path.setPlaceholderText("请选择要解码的QR码阵列图像或将图像拖放到此处...")
        image_path_layout.addWidget(self.image_path)
        
        self.image_browse = QPushButton("浏览...")
        self.image_browse.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.image_browse.clicked.connect(self.browse_input_image)
        self.image_browse.setMaximumWidth(100)
        image_path_layout.addWidget(self.image_browse)
        
        image_select_layout.addRow("图像路径:", image_path_layout)
        
        # 添加图像拖放区域
        self.image_drop_zone = ImageDropZone()
        self.image_drop_zone.image_pasted.connect(self.handle_pasted_image)
        image_select_layout.addRow("", self.image_drop_zone)
        
        image_select_group.setLayout(image_select_layout)
        
        # 解码选项
        decode_options_group = QGroupBox("解码选项")
        decode_options_layout = QFormLayout()
        decode_options_layout.setVerticalSpacing(10)
        
        # 解码输出目录水平布局
        decode_output_layout = QHBoxLayout()
        
        self.decode_output_dir = QLineEdit("decoded")
        decode_output_layout.addWidget(self.decode_output_dir)
        
        self.decode_output_browse = QPushButton("浏览...")
        self.decode_output_browse.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.decode_output_browse.clicked.connect(self.browse_decode_output_dir)
        self.decode_output_browse.setMaximumWidth(100)
        decode_output_layout.addWidget(self.decode_output_browse)
        
        self.visual_debug = QCheckBox("可视化调试")
        self.visual_debug.setToolTip("在解码过程中显示识别结果，帮助分析识别问题")
        decode_options_layout.addRow("", self.visual_debug)
        
        decode_options_layout.addRow("输出目录:", decode_output_layout)
        
        decode_options_group.setLayout(decode_options_layout)
        
        # 解码操作按钮
        decode_actions_layout = QHBoxLayout()
        self.decode_button = QPushButton("解码QR码阵列")
        self.decode_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.decode_button.setStyleSheet("font-weight: bold; padding: 8px;")
        self.decode_button.clicked.connect(self.decode_qr_array)
        decode_actions_layout.addWidget(self.decode_button)
        
        # 添加组件到解码选项卡
        decode_layout.addWidget(image_select_group, 1)
        decode_layout.addWidget(decode_options_group, 2)
        decode_layout.addLayout(decode_actions_layout)
        
        # 创建底部区域
        bottom_area = QWidget()
        bottom_layout = QVBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)  # 设置为不确定进度
        self.progress_bar.hide()
        bottom_layout.addWidget(self.progress_bar)
        
        # 状态和预览区域
        status_preview = QSplitter(Qt.Orientation.Horizontal)
        
        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(8, 8, 8, 8)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        self.log_handler = LogHandler(self.log_text)
        
        log_buttons_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("清除日志")
        self.clear_log_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.clear_log_button.clicked.connect(self.clear_log)
        self.export_log_button = QPushButton("导出日志")
        self.export_log_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.export_log_button.clicked.connect(self.export_log)
        log_buttons_layout.addWidget(self.clear_log_button)
        log_buttons_layout.addWidget(self.export_log_button)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_buttons_layout)
        log_group.setLayout(log_layout)
        
        # 图像预览区域
        preview_group = QGroupBox("图像预览")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        # 使用可缩放图像查看器
        self.image_viewer = ZoomableImageViewer()
        
        preview_layout.addWidget(self.image_viewer)
        
        # 添加缩放提示
        zoom_info = QLabel("提示: 使用鼠标滚轮缩放, 拖动图像平移")
        zoom_info.setStyleSheet("color: #666; font-style: italic; font-size: 9pt;")
        zoom_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(zoom_info)
        
        preview_group.setLayout(preview_layout)
        
        status_preview.addWidget(log_group)
        status_preview.addWidget(preview_group)
        status_preview.setSizes([400, 500])
        
        bottom_layout.addWidget(status_preview)
        
        # 将组件添加到主布局
        main_layout.addWidget(self.tabs, 1)
        main_layout.addWidget(bottom_area, 1)
        
        # 初始化字符限制
        self.update_max_chars()
        
        # 设置全局样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit, QPlainTextEdit, QTextEdit {
                border: 1px solid #aaaaaa;
                border-radius: 3px;
                padding: 3px;
            }
            QSpinBox {
                min-width: 80px;
            }
        """)
        
        # 初始日志
        self.log("多QR码阵列生成与读取 GUI 已启动")
        self.log(f"版本: 1.5.1, 日期: 2025-05-30")
        self.log("提示: 可以直接将文件拖放到窗口中或使用Ctrl+V粘贴图像以快速解码")
    
    def update_max_chars(self):
        """更新字符数量限制，基于选定的QR码块大小"""
        chunk_size = self.text_chunk_size.value()
        # 保守估计，考虑到索引和头信息占用一些空间
        max_chars = min(chunk_size, QR_MAX_CHARS['utf8'])
        self.text_input.set_max_chars(max_chars)
        
        # 更新界面提示
        text = self.text_input.toPlainText()
        if len(text) > max_chars:
            QMessageBox.warning(
                self, 
                "字符限制已更改", 
                f"当前文本 ({len(text)} 字符) 超出了新的字符限制 ({max_chars})。\n"
                "请减少文本长度，否则生成QR码时可能会出错。"
            )
    
    # 浏览文件对话框
    def browse_text_output(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存QR码阵列", "", "PNG图像 (*.png);;所有文件 (*)"
        )
        if filename:
            self.text_output_file.setText(filename)
    
    def browse_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*)"
        )
        if filename:
            self.file_path.setText(filename)
    
    def browse_file_output_dir(self):
        dirname = QFileDialog.getExistingDirectory(
            self, "选择输出目录", ""
        )
        if dirname:
            self.file_output_dir.setText(dirname)
    
    def browse_input_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择QR码阵列图像", "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.tif);;PNG图像 (*.png);;JPG图像 (*.jpg *.jpeg);;BMP图像 (*.bmp);;WebP图像 (*.webp);;TIFF图像 (*.tiff *.tif);;所有文件 (*)"
        )
        if filename:
            self.image_path.setText(filename)
            self.current_image_path = filename
            self.show_image_preview(filename)
    
    def browse_decode_output_dir(self):
        dirname = QFileDialog.getExistingDirectory(
            self, "选择解码输出目录", ""
        )
        if dirname:
            self.decode_output_dir.setText(dirname)
    
    # 日志功能
    def log(self, message):
        self.log_handler.write(message)
    
    def clear_log(self):
        self.log_text.clear()
        self.log_handler.log_contents = []
    
    def export_log(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出日志", f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "文本文件 (*.txt);;所有文件 (*)"
        )
        if filename:
            if self.log_handler.export_log(filename):
                QMessageBox.information(self, "成功", f"日志已导出到 {filename}")
            else:
                QMessageBox.warning(self, "错误", "日志导出失败")
    
    # 图像预览
    def show_image_preview(self, image_path):
        try:
            # 使用可缩放图像查看器加载图像
            if self.image_viewer.load_image(image_path):
                self.log(f"加载预览图像: {image_path}")
            else:
                self.image_viewer.scene.clear()
                self.log(f"无法加载图像: {image_path}")
        except Exception as e:
            self.log(f"预览图像时出错: {str(e)}")
            self.image_viewer.scene.clear()
    
    # 数据验证
    def validate_text_input(self):
        """验证文本输入是否有效，并检查字符数量"""
        text = self.text_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "请输入要编码的文本")
            return False
        
        max_chars = self.text_input.max_chars
        if len(text) > max_chars:
            result = QMessageBox.question(
                self, "文本块大小",
                f"输入文本字符数 ({len(text)}) 超过了当前设置的每个QR码字符数 ({max_chars})。\n\n"
                "系统将自动分割文本成多个QR码。较大的QR码能更有效传输数据，但需要确保您有\n"
                "高质量的扫描设备进行解码。\n\n"
                "是否继续生成QR码阵列？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes  # 默认为Yes，鼓励继续
            )
            return result == QMessageBox.StandardButton.Yes
        
        return True
    
    # 工作线程操作
    def start_worker(self, function, args=None, kwargs=None):
        # 显示进度条
        self.progress_bar.show()
        
        # 创建并启动工作线程
        worker = WorkerThread(function, args, kwargs)
        worker.finished.connect(self.on_worker_finished)
        worker.error.connect(self.on_worker_error)
        worker.start()
        
        # 保存工作线程引用以避免被垃圾回收
        self.workers.append(worker)
    
    def on_worker_finished(self, result):
        # 隐藏进度条
        self.progress_bar.hide()
        
        # 处理结果
        if isinstance(result, tuple) and len(result) == 2:
            # 生成QR码阵列的结果
            array_file, num_chunks = result
            self.log(f"操作完成: 生成了 {num_chunks} 个QR码")
            self.log(f"QR码阵列保存在: {array_file}")
            self.current_image_path = array_file
            self.show_image_preview(array_file)
            
            # 显示成功消息
            QMessageBox.information(
                self, 
                "QR码生成成功", 
                f"已成功生成 {num_chunks} 个QR码的阵列图像。\n"
                f"图像保存在: {array_file}"
            )
        else:
            # 解码QR码阵列的结果
            if result:
                self.log(f"操作完成: 文件已解码并保存为 {result}")
                
                # 从路径提取文件名
                filename = os.path.basename(result)
                
                # 询问用户是否打开文件
                reply = QMessageBox.question(
                    self,
                    "解码成功",
                    f"QR码阵列已成功解码！\n\n"
                    f"文件保存为: {result}\n\n"
                    "是否立即打开文件？\n\n"
                    "提示: 如果解码出错或内容不完整，请尝试以下方法:\n"
                    "1. 确保QR码图像清晰且完整\n"
                    "2. 勾选'可视化调试'选项以查看识别情况\n"
                    "3. 查看操作日志了解更多详情",
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Open
                )

                if reply == QMessageBox.StandardButton.Open:
                    try:
                        os.startfile(result) # Windows specific command
                        self.log(f"已尝试打开文件: {result}")
                    except Exception as e:
                        self.log(f"无法打开文件: {str(e)}")
                        QMessageBox.warning(self, "打开失败", f"无法自动打开文件: {result}\n错误: {str(e)}")
                
                # 如果是文本文件，尝试在日志区域显示内容预览
                if filename.endswith('.txt'):
                    try:
                        with open(result, 'r', encoding='utf-8') as f:
                            content = f.read(500)  # 读取前500个字符
                        
                        self.log("解码内容预览:")
                        self.log("------------")
                        self.log(content + ("..." if len(content) >= 500 else ""))
                        self.log("------------")
                    except Exception as e:
                        self.log(f"无法预览文件内容: {str(e)}")
            else:
                self.log("操作完成，但未返回结果")
                
                # 显示警告消息
                QMessageBox.warning(
                    self, 
                    "解码未完成", 
                    "解码操作未能返回有效结果。\n"
                    "请查看操作日志获取详细错误信息。"
                )
    
    def on_worker_error(self, error_msg):
        # 隐藏进度条
        self.progress_bar.hide()
        
        # 显示错误
        self.log(f"发生错误: {error_msg}")
        
        # 解析错误信息，提供更友好的提示
        if "Invalid version" in error_msg:
            QMessageBox.critical(
                self, "错误", 
                "QR码版本错误：输入数据过大，超出QR码最大容量。\n\n"
                "请尝试以下解决方案：\n"
                "1. 减少每个QR码的字符数（当前设置可能过大）\n"
                "2. 减少输入文本的长度或将其分成多个部分\n"
                "3. 如果包含中文或特殊字符，建议将每个QR码字符数设置为400以下"
            )
        elif "QR码版本" in error_msg and "超出了最大支持版本" in error_msg:
            QMessageBox.critical(
                self, "错误", 
                f"{error_msg}\n\n"
                "请减少每个QR码的字符数或减少文本复杂度。"
            )
        else:
            QMessageBox.critical(self, "错误", f"操作失败: {error_msg}")
    
    # QR码阵列生成与解码操作
    def generate_text_qr_array(self):
        # 验证输入
        if not self.validate_text_input():
            return
        
        # 获取文本和选项
        text = self.text_input.toPlainText()
        chunk_size = self.text_chunk_size.value()
        cols = self.text_cols.value()
        rows = None if self.text_rows.value() == 0 else self.text_rows.value()
        output_file = self.text_output_file.text()
        
        # 记录操作
        self.log(f"开始生成文本QR码阵列")
        self.log(f"文本长度: {len(text)} 字符")
        self.log(f"每个QR码字符数: {chunk_size}")
        self.log(f"列数: {cols}, 行数: {'自动' if rows is None else rows}")
        
        # 在工作线程中执行
        self.start_worker(
            create_qr_array,
            args=[text],
            kwargs={
                'chunk_size': chunk_size,
                'rows': rows,
                'cols': cols,
                'output_file': output_file
            }
        )
    
    def generate_file_qr_array(self):
        # 获取文件路径和选项
        file_path = self.file_path.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "请选择有效的输入文件")
            return
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # 1MB
            result = QMessageBox.question(
                self, "文件较大",
                f"选择的文件大小为 {file_size / 1024:.1f} KB。\n"
                "大文件会生成很多QR码，可能难以扫描和重建。\n\n"
                "是否仍要继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return
        
        chunk_size = self.file_chunk_size.value()
        cols = self.file_cols.value()
        rows = None if self.file_rows.value() == 0 else self.file_rows.value()
        output_dir = self.file_output_dir.text()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        base_name = os.path.basename(file_path)
        output_file = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}_qr_array.png")
        
        # 记录操作
        self.log(f"开始生成文件QR码阵列")
        self.log(f"文件路径: {file_path}")
        self.log(f"文件大小: {file_size / 1024:.1f} KB")
        self.log(f"每个QR码字符数: {chunk_size}")
        self.log(f"列数: {cols}, 行数: {'自动' if rows is None else rows}")
        
        # 在工作线程中执行
        self.start_worker(
            encode_file_to_qr_array,
            args=[file_path],
            kwargs={
                'chunk_size': chunk_size,
                'rows': rows,
                'cols': cols,
                'output_file': output_file
            }
        )
    
    def decode_qr_array(self):
        # 获取图像路径和选项
        image_path = self.image_path.text()
        if not image_path or not os.path.exists(image_path):
            QMessageBox.warning(self, "警告", "请选择有效的QR码阵列图像")
            return
        
        output_dir = self.decode_output_dir.text()
        visual_debug = self.visual_debug.isChecked()
        
        # 记录操作
        self.log(f"开始解码QR码阵列")
        self.log(f"图像路径: {image_path}")
        self.log(f"输出目录: {output_dir}")
        self.log(f"可视化调试: {'是' if visual_debug else '否'}")
        
        # 在工作线程中执行
        self.start_worker(
            decode_qr_array_to_file,
            args=[image_path],
            kwargs={
                'output_dir': output_dir,
                'visual_debug': visual_debug
            }
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖入开始事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """处理放下事件"""
        mime_data = event.mimeData()
        
        if mime_data.hasUrls():
            # 获取第一个URL
            url = mime_data.urls()[0]
            file_path = url.toLocalFile()
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                # 检查文件类型
                # 检查当前选中的选项卡
                current_tab = self.tabs.currentIndex()
                
                # 根据当前选项卡决定处理方式
                if current_tab == 0:  # 文本编码选项卡
                    # 如果是文本文件，尝试读取内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.text_input.setPlainText(f.read())
                            self.log(f"已从拖入的文件加载文本: {file_path}")
                    except Exception as e:
                        QMessageBox.warning(self, "警告", f"无法读取文本文件: {str(e)}")
                
                elif current_tab == 1:  # 文件编码选项卡
                    # 设置文件路径
                    self.file_path.setText(file_path)
                    self.log(f"已选择文件: {file_path}")
                
                elif current_tab == 2:  # 图像解码选项卡
                    # 检查是否为图像文件
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif']:
                        self.image_path.setText(file_path)
                        self.current_image_path = file_path
                        self.show_image_preview(file_path)
                        self.log(f"已加载图像: {file_path}")
                    else:
                        QMessageBox.warning(self, "警告", "请拖入支持的图像文件格式")

    def handle_pasted_image(self, image_path):
        """处理从剪贴板粘贴的图像"""
        if os.path.exists(image_path):
            self.image_path.setText(image_path)
            self.current_image_path = image_path
            self.show_image_preview(image_path)
            self.log(f"已从剪贴板粘贴图像: {image_path}")
            
            # 如果是临时图像，提示用户
            if tempfile.gettempdir() in image_path:
                self.log("注意: 这是一个临时文件，应用程序关闭后可能会被删除")

# 主函数
def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle(QStyleFactory.create('Fusion'))
    
    # 设置调色板颜色使深色模式看起来更好
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(palette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(palette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(palette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(palette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(palette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(palette.ColorRole.Link, QColor(0, 100, 200))
    palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = QRArrayApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 