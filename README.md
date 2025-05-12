# 多QR码阵列生成与读取 (Multi-QR Code Array Generator and Reader)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt-6.2%2B-green)](https://pypi.org/project/PyQt6/)
[![Version](https://img.shields.io/badge/version-1.4.4-brightgreen)](CHANGELOG.md)

这个项目实现了将长文本分割为多个QR码并排列成阵列，以及读取QR码阵列并重组文本的功能。特别适用于**需要传递大量数据且没有网络连接的场景**（例如内网传外网），克服了单个二维码传输信息有限且分段传输容易导致格式混乱的问题。

## 背景与目的

在特殊的网络环境中（例如内网隔离环境），数据传输面临严峻挑战：
- 单个二维码的信息容量有限（通常不超过4KB）
- 多个二维码分段传输容易导致代码结构被打乱或顺序混乱
- 手动拼接大量文本块容易出错

本项目通过创新的设计解决了这些问题：
- 将大文本智能分割成多个带索引的QR码
- 将这些QR码按照特定规则排列成一个阵列图像
- 通过专用的解码工具，可以从阵列图像中准确识别每个QR码及其索引
- 无论内容大小，都能准确还原原始数据，保持格式和结构的完整性

## 快速开始

### 1. 安装依赖

在Windows环境下，使用PowerShell执行以下命令安装所需库：

```powershell
pip install -r requirements.txt
```

### 2. 启动图形界面

```powershell
python run_gui.py
```

程序启动后，您将看到如下界面：

<div align="center">
  <img src="./assets/image1.png" alt="程序主界面" width="700">
  <p><i>图1：多QR码阵列工具主界面</i></p>
</div>

### 3. 使用流程

#### 3.1 文本编码到QR码阵列

1. 在文本编辑区域输入或粘贴要传输的文本
2. 设置合适的文本块大小和布局选项，根据内容类型选择推荐值
   
<div align="center">
  <img src="./assets/image2.png" alt="文本输入和选项设置" width="700">
  <p><i>图2：输入文本并设置编码选项</i></p>
</div>

3. 点击"生成QR码阵列"按钮
4. 在指定的输出位置查看生成的QR码阵列图像

<div align="center">
  <img src="./assets/image3.png" alt="生成的QR码阵列" width="700">
  <p><i>图3：生成的多QR码阵列</i></p>
</div>

#### 3.2 从QR码阵列解码

1. 切换到"图像解码"选项卡
2. 点击"浏览"按钮选择QR码阵列图像（或拍照导入、拖放图像、粘贴图像）
3. 勾选"可视化调试"可查看识别过程和索引序号

<div align="center">
  <img src="./assets/image4.png" alt="解码过程与可视化调试" width="700">
  <p><i>图4：解码过程与可视化调试界面，显示识别的QR码索引</i></p>
</div>

4. 点击"解码QR码阵列"按钮
5. 在结果区域查看解码的文本内容

<div align="center">
  <img src="./assets/image5.png" alt="解码结果" width="700">
  <p><i>图5：解码后的文本显示界面</i></p>
</div>

#### 3.3 文件编码

无需手动提供文本，直接选择文件进行编码：
1. 切换到"文件编码"选项卡
2. 选择要编码的文件
3. 设置编码选项
4. 点击"生成QR码阵列"按钮

> **小贴士**：解析的QR码数量没有严格限制，主要受限于拍摄设备的图像清晰度和显示屏幕的大小。在实际应用中，建议根据屏幕大小和摄像头质量调整QR码的数量和大小，以获得最佳的传输效果。

## 功能特点

- 将长文本分割成多个小块
- 为每个文本块生成带索引的QR码
- 将多个QR码排列成一个二维阵列
- 读取QR码阵列，识别每个QR码的内容
- 根据索引重组文本，还原原始信息
- 支持中文和Unicode字符
- 支持二进制文件传输（通过Base64编码）
- 提供图形用户界面，易于使用
- 支持多种图像格式（PNG、JPG、JPEG、BMP、WebP、TIFF等）

## 项目文件说明

本项目由以下主要文件组成：

| 文件名 | 说明 |
| --- | --- |
| `generate_qr_array.py` | 实现QR码生成核心功能，将文本分割成块并生成QR码阵列 |
| `read_qr_array.py` | 实现QR码阵列读取功能，识别阵列中的QR码并重组文本 |
| `qr_code_file_transfer.py` | 文件传输模块，支持将任意文件编码为QR码阵列并解码恢复 |
| `qr_array_gui.py` | 图形用户界面实现，基于PyQt6，提供直观的操作体验 |
| `run_gui.py` | 启动图形界面的入口脚本 |
| `requirements.txt` | 项目依赖库列表 |
| `README.md` | 项目说明文档 |
| `CHANGELOG.md` | 版本更新历史记录 |

### 核心功能文件详细说明

- **generate_qr_array.py**：
  - 实现文本分割功能
  - 为每个文本块生成带索引的QR码（使用"IDX:000:"格式的索引前缀）
  - 将多个QR码排列成阵列图像
  - 支持自定义行列数和每个QR码的文本块大小
  - 包含错误处理和版本控制逻辑

- **read_qr_array.py**：
  - 提取QR码阵列中的所有QR码
  - 解析每个QR码的内容和索引
  - 按索引顺序重组文本
  - 提供可视化调试功能
  - 支持多种索引格式，具有强大的容错能力
  - 支持多种图像格式（PNG、JPG、JPEG、BMP、WebP、TIFF等）

- **qr_code_file_transfer.py**：
  - 封装文件编码和解码逻辑
  - 支持文本和二进制文件传输
  - 使用Base64编码处理二进制数据
  - 提供命令行界面
  - 支持纯文本和带文件标记的QR码解码

- **qr_array_gui.py**：
  - 基于PyQt6的图形界面实现
  - 提供文本编码、文件编码和图像解码功能
  - 支持文件选择和保存
  - 包含图像预览和日志功能
  - 使用工作线程处理长时间操作，避免界面冻结
  - 支持读取多种格式的QR码阵列图像

## 安装依赖

在Windows环境下，使用PowerShell执行以下命令安装所需库：

```powershell
pip install -r requirements.txt
```

或者单独安装依赖：

```powershell
pip install qrcode pillow opencv-python pyzbar numpy PyQt6
```

## 使用方法

### 图形用户界面

启动图形用户界面，提供直观的操作体验：

```powershell
python run_gui.py
```

GUI界面包含三个主要功能选项卡：
1. **文本编码**：将输入文本编码为QR码阵列
2. **文件编码**：将任意文件编码为QR码阵列
3. **图像解码**：从QR码阵列图像解码恢复原始文本/文件

界面底部提供操作日志查看和图像预览功能。

### 命令行接口

#### 生成QR码阵列

运行 `generate_qr_array.py` 文件：

```powershell
python generate_qr_array.py
```

可以修改代码中的 `sample_text` 变量来生成包含自定义文本的QR码阵列。

#### 读取QR码阵列

运行 `read_qr_array.py` 文件：

```powershell
python read_qr_array.py
```

默认会读取当前目录下的 `qr_array.png` 文件。也支持读取其他格式图像文件（如JPG、BMP等）。

#### 使用文件传输功能

文件传输功能提供了更完整的功能，用于将任何文件编码为QR码阵列，以及从QR码阵列恢复文件：

**编码文件：**

```powershell
python qr_code_file_transfer.py encode <文件路径> [--chunk-size <每个QR码的字符数>] [--rows <行数>] [--cols <列数>] [--output <输出文件名>]
```

例如：

```powershell
python qr_code_file_transfer.py encode test_message.txt --chunk-size 200 --cols 3
```

**解码文件：**

```powershell
python qr_code_file_transfer.py decode <QR码阵列图像路径> [--output-dir <输出目录>] [--debug]
```

例如：

```powershell
python qr_code_file_transfer.py decode test_message_qr_array.png --output-dir recovered
```

## 参数说明

### 生成QR码阵列参数

- `text`：要编码的文本内容
- `chunk_size`：每个QR码包含的最大字符数
- `rows`：阵列的行数（可选，默认自动计算）
- `cols`：阵列的列数（可选，默认自动计算）
- `output_file`：输出的QR码阵列图像文件名

### 读取QR码阵列参数

- `array_image_path`：QR码阵列图像的路径（支持PNG、JPG、JPEG、BMP、WebP、TIFF等格式）
- `visual_debug`：是否显示可视化调试信息

## 编码注意事项

本项目支持中文和其他Unicode字符的传输。为了确保在各种系统上正确显示中文字符，我们采用了UTF-8-SIG编码（带有BOM的UTF-8）来写入恢复的文本文件。

### 关于中文乱码问题

如果遇到中文字符显示为乱码的情况，可能是由于编码不匹配导致的。在这种情况下：

1. 确保Python运行环境支持UTF-8
2. 使用 UTF-8-SIG 编码打开和写入文件
3. 在一些特殊系统上，可能需要在读取文件时指定正确的编码

## 示例

以下是一个完整的示例，演示如何使用此项目传输文件：

```python
# 将文件编码为QR码阵列
python qr_code_file_transfer.py encode important_document.txt --chunk-size 500 --cols 4

# 从QR码阵列解码文件
python qr_code_file_transfer.py decode important_document_qr_array.png --output-dir recovered
```

也可以使用图形界面进行操作，更加直观方便：

```python
python qr_array_gui.py
```

## 注意事项

- QR码之间需要有足够的空白区域，以确保能够正确识别
- 阵列中的QR码过多可能会导致识别困难
- 每个QR码的容量有限，推荐使用较小的chunk_size（如200-500字符）
- 对于图像和其他二进制文件，会通过Base64编码，这会增加大约33%的数据量
- 推荐在良好光照条件下使用高质量相机读取QR码阵列
- 当使用JPG等有损压缩格式时，图像质量可能会影响QR码识别效果，建议使用PNG等无损格式或保持较高的图像质量

## 贡献指南

欢迎对本项目提出改进建议或贡献代码。请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与贡献。

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。 