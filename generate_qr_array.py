import qrcode
import numpy as np
from PIL import Image
import os
import math

def split_text(text, chunk_size=100):
    """将文本分割成固定大小的块"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def generate_qr_code(text, index, output_dir="qrcodes"):
    """生成单个QR码并保存"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # 添加索引前缀以确保正确的读取顺序
    text_with_index = f"{index}:{text}"
    qr.add_data(text_with_index)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"qrcode_{index}.png")
    img.save(filename)
    return filename

def arrange_qr_codes_in_array(filenames, rows=None, cols=None, output_file="qr_array.png"):
    """将多个QR码排列成网格"""
    if not filenames:
        return None
    
    # 加载图像
    images = [Image.open(filename) for filename in filenames]
    
    # 确定所有图像的尺寸一致
    width, height = images[0].size
    
    # 自动计算行数和列数
    if rows is None and cols is None:
        # 默认为近似正方形排列
        cols = int(math.ceil(math.sqrt(len(images))))
        rows = int(math.ceil(len(images) / cols))
    elif rows is None:
        rows = int(math.ceil(len(images) / cols))
    elif cols is None:
        cols = int(math.ceil(len(images) / rows))
    
    # 创建空白图像
    result = Image.new('RGB', (cols * width, rows * height), color='white')
    
    # 将QR码填充到网格中
    for idx, img in enumerate(images):
        row = idx // cols
        col = idx % cols
        result.paste(img, (col * width, row * height))
    
    result.save(output_file)
    print(f"QR码阵列已保存为 {output_file}")
    return output_file

def create_qr_array(text, chunk_size=100, rows=None, cols=None, output_file="qr_array.png"):
    """主函数：分割文本、生成多个QR码并排列成阵列"""
    # 分割文本
    chunks = split_text(text, chunk_size)
    print(f"文本已分割为 {len(chunks)} 个块")
    
    # 为每个块生成QR码
    filenames = []
    for i, chunk in enumerate(chunks):
        filename = generate_qr_code(chunk, i)
        filenames.append(filename)
    
    # 将QR码排列为阵列
    array_file = arrange_qr_codes_in_array(filenames, rows, cols, output_file)
    
    return array_file, len(chunks)

if __name__ == "__main__":
    # 测试
    sample_text = "这是一个示例文本，将被分割成多个QR码并排列成阵列。" * 10
    array_file, num_chunks = create_qr_array(sample_text, chunk_size=50)
    print(f"生成了 {num_chunks} 个QR码，组合成阵列保存在 {array_file}") 