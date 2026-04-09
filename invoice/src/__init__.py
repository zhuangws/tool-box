"""
Invoice PDF合并工具插件包

提供以下功能:
- InvoiceInfo: 发票信息数据模型
- extract_pdf_info: 从PDF文件中提取发票信息
- merge_pdfs: 合并多个PDF文件
- merge_pdfs_with_layout: 按布局合并PDF文件
- PageLayout: 页面布局枚举

使用方法:
    from plugins.invoice import InvoiceInfo, extract_pdf_info, merge_pdfs, merge_pdfs_with_layout, PageLayout
    
    # 提取发票信息
    info = extract_pdf_info("invoice.pdf")
    print(f"发票号码: {info.invoice_no}")
    print(f"金额: {info.amount}")
    
    # 标准合并
    files = ["a.pdf", "b.pdf"]
    count, pages = merge_pdfs(files, "merged.pdf")
    
    # 按布局合并 (每页2张)
    count, pages = merge_pdfs_with_layout(files, "merged.pdf", PageLayout.TWO_PER_PAGE)
"""

from .models import InvoiceInfo
from .extractor import extract_pdf_info
from .merge import merge_pdfs
from .layout import merge_pdfs_with_layout, PageLayout

__all__ = ['InvoiceInfo', 'extract_pdf_info', 'merge_pdfs', 'merge_pdfs_with_layout', 'PageLayout']