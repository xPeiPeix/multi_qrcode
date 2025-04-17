"""
多QR码阵列生成与读取

这个包提供了将长文本分割为多个QR码并排列成阵列，以及读取QR码阵列并重组文本的功能。
特别适用于需要传递大量数据且没有网络连接的场景。

主要功能:
- 文本分割与QR码生成
- QR码阵列布局与组合
- QR码阵列识别与文本重组
- 文件编码与解码传输
- 图形用户界面
"""

__version__ = '1.1.0'
__author__ = 'QR Array Project Team'
__date__ = '2025-04-16'

from .generate_qr_array import (
    split_text,
    generate_qr_code,
    arrange_qr_codes_in_array,
    create_qr_array
)

from .read_qr_array import (
    read_qr_code,
    extract_qr_codes_from_array,
    combine_qr_code_data,
    read_qr_array
)

# 导出用于文件传输的主要函数
from .qr_code_file_transfer import (
    encode_file_to_qr_array,
    decode_qr_array_to_file
)

# 尝试导入GUI功能，如果PyQt6不可用则忽略
try:
    from .qr_array_gui import QRArrayApp, main as gui_main
except ImportError:
    pass 