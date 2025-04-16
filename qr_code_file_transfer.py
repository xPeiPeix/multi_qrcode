import base64
import os
import argparse
import re
from generate_qr_array import create_qr_array
from read_qr_array import read_qr_array

def encode_file_to_qr_array(file_path, chunk_size=1000, rows=None, cols=None, output_file=None):
    """将文件编码为QR码阵列"""
    # 检查文件是否为文本文件
    is_text = False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
            is_text = True
    except UnicodeDecodeError:
        is_text = False
    
    # 获取文件名和扩展名
    file_name = os.path.basename(file_path)
    
    if is_text:
        # 对于文本文件，直接使用文本内容
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        # 标记为文本文件
        header = f"QRTEXT:{file_name}:"
        full_data = header + file_content
    else:
        # 对于二进制文件，使用Base64编码
        with open(file_path, 'rb') as f:
            file_data = f.read()
        # Base64编码
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        # 标记为二进制文件
        header = f"QRFILE:{file_name}:"
        full_data = header + encoded_data
    
    # 如果未指定输出文件名，则使用原文件名+后缀
    if output_file is None:
        output_file = f"{os.path.splitext(file_name)[0]}_qr_array.png"
    
    # 创建QR码阵列
    print(f"文件类型: {'文本' if is_text else '二进制'}")
    print(f"文件大小: {len(full_data) - len(header)} 字符/字节")
    print(f"编码后数据大小: {len(full_data)} 字符")
    print(f"头部标识: {header}")
    
    array_file, num_chunks = create_qr_array(
        text=full_data,
        chunk_size=chunk_size,
        rows=rows,
        cols=cols,
        output_file=output_file
    )
    
    return array_file, num_chunks

def decode_qr_array_to_file(array_image_path, output_dir='.', visual_debug=False):
    """从QR码阵列解码文件"""
    # 读取QR码阵列
    combined_text = read_qr_array(array_image_path, visual_debug)
    
    if not combined_text:
        print("未能从QR码阵列中解码数据")
        return None
    
    print(f"解码的原始数据: {combined_text[:50]}...")
    
    # 处理可能带有索引前缀的数据
    # 检查是否有形如 "0:QRTEXT:" 或 "0:QRFILE:" 的前缀
    match = re.match(r'^\d+:(QRTEXT:|QRFILE:)', combined_text)
    if match:
        # 去除索引前缀
        index_end = combined_text.find(':')
        if index_end != -1:
            combined_text = combined_text[index_end+1:]
            print(f"检测到索引前缀，已移除。处理后数据: {combined_text[:50]}...")
    
    # 检查文件类型
    if combined_text.startswith("QRTEXT:"):
        # 文本文件处理
        prefix_len = 7  # "QRTEXT:" 的长度
        is_text = True
        print("检测到文本文件格式")
    elif combined_text.startswith("QRFILE:"):
        # 二进制文件处理
        prefix_len = 7  # "QRFILE:" 的长度
        is_text = False
        print("检测到二进制文件格式")
    else:
        print(f"无效的文件数据格式，前缀为: {combined_text[:20]}")
        return None
    
    # 解析文件名和数据
    try:
        # 去除前缀
        data = combined_text[prefix_len:]
        
        # 查找第一个冒号位置
        colon_pos = data.find(':')
        if colon_pos == -1:
            print("无法找到文件名与内容分隔符")
            return None
        
        # 提取文件名和编码数据
        file_name = data[:colon_pos]
        file_content = data[colon_pos+1:]
        
        print(f"提取的文件名: {file_name}")
        print(f"内容长度: {len(file_content)} 字符")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 构建输出文件路径
        output_path = os.path.join(output_dir, file_name)
        
        if is_text:
            # 对于文本文件，使用UTF-8-SIG编码写入，以正确处理中文字符
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                f.write(file_content)
            print(f"已写入文本文件，内容前50个字符: {file_content[:50]}...")
        else:
            # 对于二进制文件，解码Base64数据
            try:
                file_data = base64.b64decode(file_content)
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                print(f"已写入二进制文件，大小: {len(file_data)} 字节")
            except Exception as e:
                print(f"Base64解码错误: {e}")
                return None
        
        print(f"文件已成功解码并保存为: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"解码文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    parser = argparse.ArgumentParser(description='通过QR码阵列传输文件')
    subparsers = parser.add_subparsers(dest='command', help='command')
    
    # 编码命令
    encode_parser = subparsers.add_parser('encode', help='将文件编码为QR码阵列')
    encode_parser.add_argument('file', help='要编码的文件路径')
    encode_parser.add_argument('--chunk-size', type=int, default=1000, help='每个QR码的最大字符数 (默认: 1000)')
    encode_parser.add_argument('--rows', type=int, help='QR码阵列的行数 (默认: 自动计算)')
    encode_parser.add_argument('--cols', type=int, help='QR码阵列的列数 (默认: 自动计算)')
    encode_parser.add_argument('--output', help='输出文件名 (默认: 使用原文件名)')
    
    # 解码命令
    decode_parser = subparsers.add_parser('decode', help='从QR码阵列解码文件')
    decode_parser.add_argument('image', help='QR码阵列图像路径')
    decode_parser.add_argument('--output-dir', default='.', help='输出目录 (默认: 当前目录)')
    decode_parser.add_argument('--debug', action='store_true', help='启用可视化调试')
    
    args = parser.parse_args()
    
    if args.command == 'encode':
        encode_file_to_qr_array(
            args.file,
            chunk_size=args.chunk_size,
            rows=args.rows,
            cols=args.cols,
            output_file=args.output
        )
    
    elif args.command == 'decode':
        decode_qr_array_to_file(
            args.image,
            output_dir=args.output_dir,
            visual_debug=args.debug
        )
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 