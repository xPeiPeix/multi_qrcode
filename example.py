#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多QR码阵列使用示例

本脚本展示了多QR码阵列生成与读取的基本用法。
包括文本分割、QR码生成、QR码阵列读取以及文件传输功能。
"""

import os
import time
from generate_qr_array import create_qr_array
from read_qr_array import read_qr_array
from qr_code_file_transfer import encode_file_to_qr_array, decode_qr_array_to_file

def example_text_transfer():
    """展示基本的文本传输功能"""
    print("===== 基本文本传输示例 =====")
    
    # 创建测试文本
    text = "这是一个用于测试的中文文本，将被分割成多个QR码并排列成阵列。" * 5
    
    print(f"原始文本长度: {len(text)} 字符")
    print(f"原始文本前50个字符: {text[:50]}...")
    
    # 生成QR码阵列
    print("\n[1] 生成QR码阵列...")
    array_file, num_chunks = create_qr_array(
        text=text,
        chunk_size=100,  # 每个QR码最多包含100个字符
        cols=2,          # 设置为2列排列
        output_file="example_qr_array.png"
    )
    
    print(f"生成了 {num_chunks} 个QR码")
    print(f"QR码阵列保存在: {array_file}")
    
    # 读取QR码阵列
    print("\n[2] 读取QR码阵列...")
    combined_text = read_qr_array(array_file)
    
    if combined_text:
        print("读取成功!")
        print(f"重组后文本长度: {len(combined_text)} 字符")
        print(f"重组后文本前50个字符: {combined_text[:50]}...")
        
        # 验证读取结果
        if combined_text == text:
            print("\n✓ 验证通过：重组后的文本与原始文本完全匹配")
        else:
            print("\n✗ 验证失败：重组后的文本与原始文本不匹配")
    else:
        print("读取失败!")

def example_file_transfer():
    """展示文件传输功能"""
    print("\n===== 文件传输示例 =====")
    
    # 创建一个测试文件
    test_file = "example_text_file.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("这是一个示例文件，用于测试QR码文件传输功能。\n")
        f.write("QR码阵列技术可以帮助我们在没有网络连接的情况下传输数据。\n")
        f.write("这种方式特别适合以下场景：\n")
        f.write("1. 线下文件传输\n")
        f.write("2. 敏感数据传递（无需通过网络）\n")
        f.write("3. 离线备份重要信息\n\n")
        f.write("当文件较小时，可以通过手机扫描QR码阵列，快速重建原始文件。")
    
    print(f"创建测试文件: {test_file}")
    
    # 编码文件为QR码阵列
    print("\n[1] 将文件编码为QR码阵列...")
    output_dir = "example_output"
    os.makedirs(output_dir, exist_ok=True)
    
    array_file, num_chunks = encode_file_to_qr_array(
        file_path=test_file,
        chunk_size=200,
        cols=2,
        output_file=os.path.join(output_dir, "example_file_qr_array.png")
    )
    
    print(f"文件已编码为 {num_chunks} 个QR码")
    print(f"QR码阵列保存在: {array_file}")
    
    # 解码QR码阵列为文件
    print("\n[2] 从QR码阵列解码文件...")
    recovered_file = decode_qr_array_to_file(
        array_image_path=array_file,
        output_dir=os.path.join(output_dir, "recovered")
    )
    
    if recovered_file:
        print(f"文件成功解码并保存为: {recovered_file}")
        print("\n解码文件内容预览:")
        with open(recovered_file, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"{content[:150]}...")
    else:
        print("文件解码失败!")

if __name__ == "__main__":
    print("多QR码阵列生成与读取示例")
    print("=" * 50)
    print("版本: 1.0.0")
    print("日期: 2025-04-16")
    print("=" * 50)
    
    # 运行基本文本传输示例
    example_text_transfer()
    
    # 运行文件传输示例
    example_file_transfer()
    
    print("\n示例结束。查看生成的QR码阵列图像和恢复的文件。") 