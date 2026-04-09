# PDF发票合并工具

一个功能完善的PDF发票合并工具，支持从PDF文件中提取发票信息、合并多个PDF文件、自动去重等功能。

## 功能特性

- **PDF发票信息提取**: 自动从PDF发票中提取发票号码、开票日期、金额、购买方/销售方等信息
- **多文件合并**: 支持将多个PDF文件合并为一个文件
- **自动去重**: 可根据发票号码自动去除重复的发票
- **图形界面**: 简洁易用的GUI界面，支持拖拽添加、批量操作
- **进度显示**: 实时显示合并进度
- **PDF打印**: 合并完成后可直接调用系统默认程序打开并打印

## 项目结构

```
plugins/invoice/
├── __init__.py      # 包初始化，导出主要接口
├── models.py        # 发票数据模型 (InvoiceInfo)
├── extractor.py     # PDF发票信息提取器
├── merge.py         # PDF合并功能
├── main.py          # GUI主程序入口
└── README.md        # 本文档
```

## 开发构建指令

### 环境要求

- Python 3.8+
- PyMuPDF (fitz) 1.22.0+
- tkinter (Python内置)

### 安装依赖

```bash
pip install PyMuPDF
```

### 开发运行

```bash
# 直接运行主程序
python plugins/invoice/main.py

# 或者从项目根目录运行
python -m plugins.invoice.main
```

### 目录结构说明

确保项目目录结构如下:

```
项目根目录/
├── plugins/
│   └── invoice/
│       ├── __init__.py
│       ├── models.py
│       ├── extractor.py
│       ├── merge.py
│       ├── main.py
│       └── README.md
├── m-ui.py  (原文件，可保留或删除)
└── 其他文件...
```

## 打包指令

```bash
# 安装打包工具
pip install pyinstaller

# 打包 (生成 dist/InvoiceMergeTool.exe)
pyinstaller --onefile --windowed --name InvoiceMergeTool --add-data "plugins;plugins" --hidden-import fitz plugins/invoice/main.py
```

**打包后运行:**
```bash
# exe位于 dist/InvoiceMergeTool.exe
# 双击运行或命令行运行
dist\InvoiceMergeTool.exe
```

**参数说明:**
- `--onefile`: 生成单个exe文件
- `--windowed`: 无控制台窗口 (GUI程序)
- `--add-data "plugins;plugins"`: 打包时包含 plugins 目录
- `--hidden-import fitz`: 强制导入 PyMuPDF 模块

## 使用说明

### 启动程序

1. 双击运行 `InvoiceMergeTool.exe` (打包后)
2. 或运行 `python plugins/invoice/main.py` (开发模式)

### 基本操作

1. **添加文件**: 
   - 点击"添加文件"按钮选择单个或多个PDF文件
   - 点击"添加文件夹"按钮选择文件夹，自动添加文件夹内所有PDF

2. **查看信息**: 
   - 文件添加后自动提取并显示发票信息(发票号码、购买方、日期、销售方、金额、备注)
   - 双击表格行可查看完整的发票详情

3. **管理文件**:
   - 选中文件后点击"移除选中"删除
   - 点击"清空列表"清空所有文件
   - 勾选"自动去重"可根据发票号码自动去除重复文件

4. **合并PDF**:
   - 选择输出保存路径(或使用默认)
   - 点击"开始合并"按钮
   - 等待合并完成，查看进度条

5. **打印**:
   - 合并成功后点击"打印PDF"用系统默认程序打开
   - 在打开的窗口中进行打印操作

### 快捷键

- 双击表格行: 查看发票详情
- 选中 + 删除: 移除选中文件

## 模块 API

### 从插件导入

```python
from plugins.invoice import InvoiceInfo, extract_pdf_info, merge_pdfs

# 提取单个PDF的发票信息
info = extract_pdf_info("invoice.pdf")
print(f"发票号: {info.invoice_no}")
print(f"金额: {info.amount}")
print(f"购买方: {info.buyer}")

# 合并PDF文件
files = ["a.pdf", "b.pdf", "c.pdf"]
count, pages = merge_pdfs(files, "merged.pdf")
print(f"合并了 {count} 个文件, 共 {pages} 页")

# 转换为字典
data = info.to_dict()
```

### 批量处理

```python
from plugins.invoice import extract_batch

# 批量提取发票信息
pdf_files = ["a.pdf", "b.pdf", "c.pdf"]
infos = extract_batch(pdf_files)

for info in infos:
    if info:  # 检查是否有效
        print(f"{info.invoice_no}: {info.amount}")
```

## 故障排除

1. **PDF无法打开**: 检查文件是否损坏或加密
2. **信息提取失败**: 确认PDF为标准发票格式
3. **合并速度慢**: 大文件或大量文件时属正常现象
4. **打包后无法运行**: 检查是否缺少依赖库

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本
- 支持PDF发票信息提取
- 支持多文件合并
- 支持自动去重
- 图形界面支持