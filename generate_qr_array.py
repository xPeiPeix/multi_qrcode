import qrcode
import numpy as np
from PIL import Image
import os
import math
import shutil

# QR码最大版本常量
MAX_VERSION = 40
# QR码之间的间距（像素）
QR_CODE_SPACING = 20
# 添加额外边距（像素）
QR_CODE_MARGIN = 40
# 默认临时文件夹
DEFAULT_TEMP_DIR = "qrcodes"

def split_text(text, chunk_size=100):
    """将文本分割成固定大小的块"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def generate_qr_code(text, index, output_dir=DEFAULT_TEMP_DIR):
    """生成单个QR码并保存"""
    qr = qrcode.QRCode(
        version=1,  # 初始版本为1，自动适应
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=6,  # 增加边界宽度，确保足够的静区
    )
    
    # 添加索引前缀以确保正确的读取顺序
    # 使用明确的格式 "IDX:nnn:" 其中nnn是固定3位数的索引号，便于解析
    index_str = f"IDX:{index:03d}:"
    text_with_index = f"{index_str}{text}"
    
    # 添加数据并限制版本
    qr.add_data(text_with_index)
    try:
        # 尝试使用自动适应版本，但限制最大版本
        qr.make(fit=True)
        
        # 检查版本是否超出范围
        if qr.version > MAX_VERSION:
            raise ValueError(f"QR码版本 ({qr.version}) 超出了最大支持版本 ({MAX_VERSION})。数据过大或复杂，请减小文本块大小。")
    except qrcode.exceptions.DataOverflowError:
        # 数据溢出错误处理
        raise ValueError(f"文本块太大，无法编码为QR码。请减小chunk_size值。当前块大小: {len(text)}字符")
    
    # 生成图像
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"qrcode_{index:03d}.png")
    img.save(filename)
    return filename

def arrange_qr_codes_in_array(filenames, rows=None, cols=None, output_file="qr_array.png"):
    """将多个QR码排列成网格，确保大小一致且不会截断"""
    if not filenames:
        return None
    
    # 加载图像
    images = [Image.open(filename) for filename in filenames]
    
    # 找出所有QR码中的最大宽度和高度
    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)
    
    print(f"检测到QR码最大尺寸: {max_width}x{max_height}像素")
    
    # 规范化所有QR码尺寸到一致大小
    normalized_images = []
    for img in images:
        # 如果图片尺寸已经是最大尺寸，则直接添加
        if img.width == max_width and img.height == max_height:
            normalized_images.append(img)
        else:
            # 创建新的白色背景图像，大小为最大尺寸
            new_img = Image.new('RGB', (max_width, max_height), color='white')
            
            # 计算居中位置
            x_offset = (max_width - img.width) // 2
            y_offset = (max_height - img.height) // 2
            
            # 将原图粘贴到新图像上的居中位置
            new_img.paste(img, (x_offset, y_offset))
            normalized_images.append(new_img)
    
    # 自动计算行数和列数
    if rows is None and cols is None:
        # 默认为近似正方形排列
        cols = int(math.ceil(math.sqrt(len(normalized_images))))
        rows = int(math.ceil(len(normalized_images) / cols))
    elif rows is None:
        rows = int(math.ceil(len(normalized_images) / cols))
    elif cols is None:
        cols = int(math.ceil(len(normalized_images) / rows))
    
    # 计算总宽度和高度，包括QR码间距和外边距
    total_width = cols * max_width + (cols - 1) * QR_CODE_SPACING + 2 * QR_CODE_MARGIN
    total_height = rows * max_height + (rows - 1) * QR_CODE_SPACING + 2 * QR_CODE_MARGIN
    
    # 创建空白图像，包括额外边距
    result = Image.new('RGB', (total_width, total_height), color='white')
    
    # 将QR码填充到网格中，考虑间距和边距
    for idx, img in enumerate(normalized_images):
        if idx >= rows * cols:
            break  # 防止索引越界
            
        row = idx // cols
        col = idx % cols
        
        # 计算带间距和边距的位置
        x = QR_CODE_MARGIN + col * (max_width + QR_CODE_SPACING)
        y = QR_CODE_MARGIN + row * (max_height + QR_CODE_SPACING)
        
        # 粘贴图像
        result.paste(img, (x, y))
    
    # 保存结果
    result.save(output_file)
    print(f"QR码阵列已保存为 {output_file}")
    return output_file

def clean_temp_directory(temp_dir=DEFAULT_TEMP_DIR):
    """清理临时文件夹及其所有内容"""
    try:
        if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
            print(f"正在删除临时文件夹 '{temp_dir}' 及其所有内容...")
            shutil.rmtree(temp_dir)
            print(f"临时文件夹 '{temp_dir}' 已成功删除")
        else:
            print(f"临时文件夹 '{temp_dir}' 不存在，无需清理")
    except Exception as e:
        print(f"清理临时文件夹时出错: {str(e)}")

def create_qr_array(text, chunk_size=100, rows=None, cols=None, output_file="qr_array.png", temp_dir=DEFAULT_TEMP_DIR):
    """主函数：分割文本、生成多个QR码并排列成阵列"""
    # 分割文本
    chunks = split_text(text, chunk_size)
    print(f"文本已分割为 {len(chunks)} 个块")
    
    # 为每个块生成QR码
    filenames = []
    try:
        for i, chunk in enumerate(chunks):
            filename = generate_qr_code(chunk, i, temp_dir)
            filenames.append(filename)
        
        # 将QR码排列为阵列
        array_file = arrange_qr_codes_in_array(filenames, rows, cols, output_file)
        
        return array_file, len(chunks)
    except ValueError as e:
        # 重新抛出错误以便上层捕获
        raise ValueError(str(e))
    finally:
        # 清理临时文件和文件夹
        clean_temp_directory(temp_dir)

if __name__ == "__main__":
    # 测试
    sample_text = "这是一个示例文本，将被分割成多个QR码并排列成阵列。" * 10
    try:
        array_file, num_chunks = create_qr_array(sample_text, chunk_size=50)
        print(f"生成了 {num_chunks} 个QR码，组合成阵列保存在 {array_file}")
    except ValueError as e:
        print(f"错误: {e}") 