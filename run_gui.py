#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多QR码阵列生成与读取 - GUI启动器

这是一个简单的启动脚本，用于启动多QR码阵列生成与读取的图形用户界面。
"""

import sys

if __name__ == "__main__":
    try:
        from PyQt6.QtWidgets import QApplication
        from qr_array_gui import QRArrayApp
    except ImportError:
        print("错误: 未能导入PyQt6模块。")
        print("请确保已安装所需依赖:")
        print("  pip install -r requirements.txt")
        print("或者:")
        print("  pip install PyQt6")
        sys.exit(1)
    
    print("正在启动多QR码阵列生成与读取GUI...")
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = QRArrayApp()
    window.show()
    
    sys.exit(app.exec()) 