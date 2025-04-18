import qrcode
import numpy as np
from PIL import Image
import os
import math

# QR码最大版本常量
MAX_VERSION = 40
# QR码之间的间距（像素）
QR_CODE_SPACING = 20

def split_text(text, chunk_size=100):
    """将文本分割成固定大小的块"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def generate_qr_code(text, index, output_dir="qrcodes"):
    """生成单个QR码并保存"""
    qr = qrcode.QRCode(
        version=1,  # 初始版本为1，自动适应
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,  # 保持足够的安静区（quiet zone）
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
    """将多个QR码排列成网格，增加间距防止定位码被截断"""
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
    
    # 计算额外间距后的总宽度和高度
    total_width = cols * width + (cols - 1) * QR_CODE_SPACING
    total_height = rows * height + (rows - 1) * QR_CODE_SPACING
    
    # 创建空白图像，增加额外边距
    result = Image.new('RGB', (total_width, total_height), color='white')
    
    # 将QR码填充到网格中，考虑间距
    for idx, img in enumerate(images):
        if idx >= rows * cols:
            break  # 防止索引越界
            
        row = idx // cols
        col = idx % cols
        
        # 计算带间距的位置
        x = col * (width + QR_CODE_SPACING)
        y = row * (height + QR_CODE_SPACING)
        
        # 粘贴图像
        result.paste(img, (x, y))
    
    # 保存结果
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
    try:
        for i, chunk in enumerate(chunks):
            filename = generate_qr_code(chunk, i)
            filenames.append(filename)
        
        # 将QR码排列为阵列
        array_file = arrange_qr_codes_in_array(filenames, rows, cols, output_file)
        
        return array_file, len(chunks)
    except ValueError as e:
        # 清理已生成的临时文件
        for filename in filenames:
            try:
                os.remove(filename)
            except:
                pass
                
        # 重新抛出错误以便上层捕获
        raise ValueError(str(e))
    finally:
        # 清理临时QR码文件
        for filename in filenames:
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"清理临时文件时出错: {e}")

if __name__ == "__main__":
    # 测试
    sample_text = "这是一个示例文本，将被分割成多个QR码并排列成阵列。" * 10
    try:
        array_file, num_chunks = create_qr_array(sample_text, chunk_size=50)
        print(f"生成了 {num_chunks} 个QR码，组合成阵列保存在 {array_file}")
    except ValueError as e:
        print(f"错误: {e}") 