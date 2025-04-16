import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import re

def read_qr_code(image_path, visual_debug=False):
    """读取单个QR码图像"""
    # 读取图像
    image = cv2.imread(image_path)
    
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
        cv2.imshow("QR Code Reader", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    results = []
    for obj in decoded_objects:
        results.append(obj.data.decode('utf-8'))
    
    return results

def extract_qr_codes_from_array(array_image_path, visual_debug=False):
    """从QR码阵列图像中提取所有QR码"""
    # 读取图像
    image = cv2.imread(array_image_path)
    
    if image is None:
        print(f"错误: 无法读取图像文件 '{array_image_path}'")
        return []
    
    # 将图像转为灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 解码QR码
    decoded_objects = decode(gray)
    
    if visual_debug:
        # 在图像上标记识别到的QR码
        for i, obj in enumerate(decoded_objects):
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points]))
                cv2.polylines(image, [hull], True, (0, 255, 0), 2)
            else:
                cv2.polylines(image, [np.array(points)], True, (0, 255, 0), 2)
            
            # 显示QR码索引
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.putText(image, str(i), (pts[0][0][0], pts[0][0][1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # 显示图像
        cv2.imshow("QR Code Array Reader", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    # 解析结果
    results = []
    for obj in decoded_objects:
        try:
            data = obj.data.decode('utf-8')
            print(f"识别到QR码数据: {data[:30]}..." if len(data) > 30 else f"识别到QR码数据: {data}")
            results.append(data)
        except UnicodeDecodeError:
            print("QR码数据解码失败：非UTF-8编码")
            continue
    
    return results

def combine_qr_code_data(qr_data_list):
    """从QR码数据中提取索引并按顺序重组文本"""
    # 创建一个字典，用于存储索引和对应的文本
    indexed_data = {}
    
    # 解析每个QR码数据
    for data in qr_data_list:
        match = re.match(r'^(\d+):(.*)$', data)
        if match:
            index = int(match.group(1))
            text = match.group(2)
            indexed_data[index] = text
            print(f"匹配成功: 索引={index}, 文本长度={len(text)}")
        else:
            print(f"无法解析索引: {data[:30]}..." if len(data) > 30 else f"无法解析索引: {data}")
            # 如果只有一个QR码且没有索引，直接返回内容
            if len(qr_data_list) == 1:
                print("只有一个QR码且无索引，直接返回内容")
                return data
    
    if not indexed_data:
        print("没有有效的索引数据")
        if len(qr_data_list) == 1:
            return qr_data_list[0]
        return None
    
    # 按索引排序并合并文本
    sorted_indices = sorted(indexed_data.keys())
    combined_text = ''.join(indexed_data[index] for index in sorted_indices)
    
    return combined_text

def read_qr_array(array_image_path, visual_debug=False):
    """主函数：读取QR码阵列并重组文本"""
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