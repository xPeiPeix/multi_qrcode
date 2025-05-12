#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多QR码阵列生成与读取 - 基本使用示例

本示例展示了如何使用项目核心功能：
1. 生成QR码阵列
2. 读取QR码阵列
3. 文件编码和解码
"""

import os
import sys

# 添加项目根目录到系统路径，以便导入相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目核心模块
from generate_qr_array import create_qr_array
from read_qr_array import read_qr_array
from qr_code_file_transfer import encode_file_to_qr_array, decode_qr_array_to_file

def example_text_to_qr_array():
    """示例1：将文本转换为QR码阵列"""
    print("=" * 50)
    print("示例1：将文本转换为QR码阵列")
    print("=" * 50)
    
    # 示例文本
    sample_text = """
    这是一个示例文本，用于演示如何使用多QR码阵列生成功能。
    该项目可以将长文本分割为多个QR码，并排列成一个阵列，以便于传输和读取。
    特别适合在没有网络连接的情况下传递大量数据。
    
    这个示例文本会被分割成多个小块，每个小块生成一个QR码，然后排列成阵列。
    阵列图像可以保存为PNG文件，便于打印或显示。
    """
    
    # 设置参数
    chunk_size = 100  # 每个QR码包含的最大字符数
    output_file = "examples/sample_qr_array.png"  # 输出文件路径
    
    try:
        # 生成QR码阵列
        array_file, num_chunks = create_qr_array(
            text=sample_text,
            chunk_size=chunk_size,
            output_file=output_file
        )
        
        print(f"成功生成QR码阵列：")
        print(f"- 文本长度: {len(sample_text)} 个字符")
        print(f"- 分割为: {num_chunks} 个QR码")
        print(f"- 输出文件: {array_file}")
        print(f"- 每个QR码最大字符数: {chunk_size}")
        print()
        
        return array_file
    except Exception as e:
        print(f"生成QR码阵列时出错: {str(e)}")
        return None

def example_read_qr_array(array_image_path):
    """示例2：读取QR码阵列并重组文本"""
    if not array_image_path or not os.path.exists(array_image_path):
        print("QR码阵列图像不存在，跳过读取示例")
        return
        
    print("=" * 50)
    print("示例2：读取QR码阵列并重组文本")
    print("=" * 50)
    
    try:
        # 读取QR码阵列
        text = read_qr_array(array_image_path, visual_debug=True)
        
        print(f"成功读取QR码阵列：")
        print(f"- 重组后文本长度: {len(text)} 个字符")
        print(f"- 重组后文本前100个字符: {text[:100]}...")
        print()
    except Exception as e:
        print(f"读取QR码阵列时出错: {str(e)}")

def example_file_transfer():
    """示例3：文件编码和解码"""
    print("=" * 50)
    print("示例3：文件编码和解码")
    print("=" * 50)
    
    # 创建示例文件
    example_file = "examples/sample_file.txt"
    with open(example_file, "w", encoding="utf-8") as f:
        f.write("这是一个示例文件，用于测试QR码文件传输功能。\n" * 10)
    
    # 设置参数
    output_file = "examples/file_qr_array.png"
    output_dir = "examples/recovered"
    
    try:
        # 编码文件为QR码阵列
        print("编码文件为QR码阵列...")
        encode_file_to_qr_array(
            file_path=example_file,
            output_file=output_file,
            chunk_size=200
        )
        
        print(f"文件已成功编码为QR码阵列: {output_file}")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 从QR码阵列解码文件
        print("\n从QR码阵列解码文件...")
        recovered_file = decode_qr_array_to_file(
            array_image_path=output_file,
            output_dir=output_dir
        )
        
        if recovered_file:
            print(f"文件已成功从QR码阵列解码: {recovered_file}")
            
            # 验证文件内容
            with open(recovered_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"- 恢复的文件大小: {len(content)} 字节")
            print(f"- 内容前50个字符: {content[:50]}...")
    except Exception as e:
        print(f"文件传输示例出错: {str(e)}")

def main():
    """运行所有示例"""
    # 确保examples目录存在
    os.makedirs("examples", exist_ok=True)
    
    # 示例1：文本到QR码阵列
    array_file = example_text_to_qr_array()
    
    # 示例2：读取QR码阵列
    example_read_qr_array(array_file)
    
    # 示例3：文件传输
    example_file_transfer()
    
    print("\n所有示例已完成。生成的文件在 'examples' 目录中。")

if __name__ == "__main__":
    main() 