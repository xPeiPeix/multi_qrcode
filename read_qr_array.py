import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import re
import os

def read_qr_code(image_path, visual_debug=False):
    """读取单个QR码图像"""
    # 读取图像
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"错误: 无法读取图像文件 '{image_path}'")
        return []
    
    # 将图像转为灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 解码QR码
    decoded_objects = decode(gray)
    
    if visual_debug:
        # 在图像上标记识别到的QR码
        for obj in decoded_objects:
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points]))
                cv2.polylines(image, [hull], True, (0, 255, 0), 2)
            else:
                cv2.polylines(image, [np.array(points)], True, (0, 255, 0), 2)
            
            # 打印识别的数据和类型
            print(f"类型: {obj.type}, 数据: {obj.data.decode('utf-8')}")
        
        # 显示图像
        cv2.imshow("QR Code Viewer", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    results = []
    for obj in decoded_objects:
        results.append(obj.data.decode('utf-8'))
    
    return results

def extract_qr_codes_from_array(array_image_path, visual_debug=False):
    """从QR码阵列图像中提取所有QR码"""
    # 检查文件是否存在
    if not os.path.exists(array_image_path):
        print(f"错误: 图像文件 '{array_image_path}' 不存在")
        return []
        
    # 尝试使用OpenCV读取图像
    image = cv2.imread(array_image_path)
    
    # 如果OpenCV读取失败，尝试使用PIL读取
    if image is None:
        try:
            # 使用PIL读取图像，然后转换为OpenCV格式
            pil_image = Image.open(array_image_path)
            # 转换为RGB模式（如果是RGBA，去除透明通道）
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            # 转换为NumPy数组
            image = np.array(pil_image)
            # 如果图像是RGB格式，转换为BGR（OpenCV使用BGR）
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            print(f"使用PIL成功读取图像: {array_image_path}")
        except Exception as e:
            print(f"错误: 尝试使用PIL读取图像失败 '{array_image_path}': {str(e)}")
            return []
    
    if image is None:
        print(f"错误: 无法读取图像文件 '{array_image_path}'")
        return []
    
    # 将图像转为灰度
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"错误: 图像转换为灰度失败: {str(e)}")
        # 尝试直接使用当前图像
        gray = image
    
    # 解码QR码
    try:
        decoded_objects = decode(gray)
    except Exception as e:
        print(f"错误: QR码解码失败: {str(e)}")
        # 尝试使用原图像直接解码
        try:
            decoded_objects = decode(image)
        except Exception as e2:
            print(f"错误: 原图像QR码解码也失败: {str(e2)}")
            return []
    
    if visual_debug:
        # 创建一个可视化图像副本
        visual_image = image.copy()
        
        # 在图像上标记识别到的QR码
        for i, obj in enumerate(decoded_objects):
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points]))
                cv2.polylines(visual_image, [hull], True, (0, 255, 0), 3)
            else:
                cv2.polylines(visual_image, [np.array(points)], True, (0, 255, 0), 3)
            
            # 显示QR码索引（尝试从数据中提取）
            try:
                data = obj.data.decode('utf-8')
                # 尝试找出索引
                index_match = re.search(r'IDX:(\d{3}):', data)
                if index_match:
                    index_num = index_match.group(1)
                else:
                    index_num = str(i)
                
                # 在QR码上方显示索引号，更加明显
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                text_x = pts[0][0][0]
                text_y = pts[0][0][1] - 10  # 在QR码上方显示
                
                # 绘制索引号（带背景色以提高可见性）
                cv2.rectangle(visual_image, 
                              (text_x - 5, text_y - 25), 
                              (text_x + 70, text_y + 5), 
                              (255, 255, 255), -1)
                cv2.putText(visual_image, f"ID:{index_num}", 
                            (text_x, text_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            except Exception as e:
                print(f"在可视化过程中发生错误: {str(e)}")
        
        # 保存可视化结果到文件
        # 根据原文件扩展名确定调试图像的保存路径
        base_path, ext = os.path.splitext(array_image_path)
        debug_image_path = f"{base_path}_debug.png"
        
        cv2.imwrite(debug_image_path, visual_image)
        print(f"已保存调试图像到: {debug_image_path}")
        
        # 显示图像 - 使用英文标题以避免中文编码问题
        cv2.imshow("QR Code Array Detection Result", visual_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    # 解析结果
    results = []
    for obj in decoded_objects:
        try:
            data = obj.data.decode('utf-8')
            print(f"识别到QR码数据: {data[:40]}..." if len(data) > 40 else f"识别到QR码数据: {data}")
            results.append(data)
        except UnicodeDecodeError:
            print("QR码数据解码失败：非UTF-8编码")
            continue
    
    return results

def combine_qr_code_data(qr_data_list):
    """从QR码数据中提取索引并按顺序重组文本"""
    # 创建一个字典，用于存储索引和对应的文本
    indexed_data = {}
    
    # 解析每个QR码数据，支持新旧两种索引格式
    for data in qr_data_list:
        # 调试输出，帮助诊断问题
        print(f"正在解析数据，前10个字符: [{data[:10]}]")
        
        # 尝试新格式 "IDX:000:"
        # 使用search而不是match，并且优化正则表达式，使其更加宽松
        match = re.search(r'IDX:(\d{3}):(.*)', data, re.DOTALL)
        if match:
            index = int(match.group(1))
            text = match.group(2)
            indexed_data[index] = text
            print(f"匹配成功(新格式): 索引={index}, 文本长度={len(text)}")
            continue
            
        # 尝试旧格式 "0:"
        match = re.search(r'^(\d+):(.*)', data, re.DOTALL)
        if match:
            index = int(match.group(1))
            text = match.group(2)
            indexed_data[index] = text
            print(f"匹配成功(旧格式): 索引={index}, 文本长度={len(text)}")
            continue
        
        print(f"无法解析索引: {data[:40]}..." if len(data) > 40 else f"无法解析索引: {data}")
        # 如果只有一个QR码且没有索引，直接返回内容
        if len(qr_data_list) == 1:
            print("只有一个QR码且无索引，直接返回内容")
            return data
    
    if not indexed_data:
        print("没有有效的索引数据")
        
        # 紧急修复：如果所有数据都以IDX:开头但无法正常解析，进行手动解析
        manual_recovery = False
        if all(data.startswith('IDX:') for data in qr_data_list):
            print("检测到所有数据块都包含IDX:前缀，尝试手动恢复...")
            try:
                for data in qr_data_list:
                    # 简单的手动提取索引
                    parts = data.split(':', 2)  # 最多分割2次
                    if len(parts) >= 3 and parts[0] == 'IDX':
                        try:
                            index = int(parts[1])
                            text = parts[2]
                            indexed_data[index] = text
                            manual_recovery = True
                            print(f"手动恢复索引: {index}")
                        except ValueError:
                            print(f"手动恢复索引失败: {parts[1]}")
            except Exception as e:
                print(f"手动恢复过程出错: {e}")
        
        if not manual_recovery:
            if len(qr_data_list) == 1:
                return qr_data_list[0]
            return None
    
    # 按索引排序并合并文本
    sorted_indices = sorted(indexed_data.keys())
    print(f"有效索引列表: {sorted_indices}")
    combined_text = ''.join(indexed_data[index] for index in sorted_indices)
    
    return combined_text

def read_qr_array(array_image_path, visual_debug=False):
    """主函数：读取QR码阵列并重组文本"""
    print(f"正在读取图像: {array_image_path}")
    
    # 检查文件类型
    _, ext = os.path.splitext(array_image_path)
    if ext.lower() not in ['.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif']:
        print(f"警告: 文件类型 {ext} 可能不被支持，将尝试读取")
    
    # 从阵列图像中提取所有QR码数据
    qr_data_list = extract_qr_codes_from_array(array_image_path, visual_debug)
    
    if not qr_data_list:
        print("未能从图像中识别到任何QR码")
        return None
    
    print(f"成功识别到 {len(qr_data_list)} 个QR码")
    
    # 按索引排序并重组文本
    combined_text = combine_qr_code_data(qr_data_list)
    
    if combined_text is None:
        print("无法合并QR码数据")
    else:
        print(f"合并后的数据长度: {len(combined_text)} 字符")
    
    return combined_text

if __name__ == "__main__":
    # 测试
    array_image_path = "qr_array.png"
    combined_text = read_qr_array(array_image_path, visual_debug=True)
    
    if combined_text:
        print("\n重组后的完整文本:")
        print(combined_text) 