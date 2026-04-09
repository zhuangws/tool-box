"""
PDF合并功能模块

提供PDF文件合并和去重功能:
- merge_pdfs: 将多个PDF文件合并为一个
- deduplicate_by_invoice_no: 根据发票号码去除重复文件
"""

import logging
from typing import List, Tuple, Callable
import fitz

logger = logging.getLogger(__name__)


def merge_pdfs(pdf_paths: List[str], output: str) -> Tuple[int, int]:
    """合并多个PDF文件
    
    依次打开每个PDF文件，将所有页面插入到输出文档中。
    支持处理损坏或格式错误的文件，遇到错误会跳过并记录日志。
    
    Args:
        pdf_paths: 要合并的PDF文件路径列表
        output: 输出文件的完整路径
    
    Returns:
        Tuple[int, int]: 
            - 第一个元素: 成功处理的文件数量
            - 第二个元素: 合并后的总页数
    
    Raises:
        异常会被捕获并记录日志，最终仍会尝试保存已合并的内容
    
    Example:
        >>> files = ["a.pdf", "b.pdf", "c.pdf"]
        >>> count, pages = merge_pdfs(files, "merged.pdf")
        >>> print(f"合并了 {count} 个文件, 共 {pages} 页")
    """
    merged = fitz.open()
    total_pages = 0
    
    for pdf_path in pdf_paths:
        try:
            doc = fitz.open(pdf_path)
            merged.insert_pdf(doc)
            total_pages += len(doc)
            doc.close()
        except Exception as e:
            logger.error(f"合并文件失败 {pdf_path}: {e}")
            continue
    
    merged.save(output)
    merged.close()
    
    return len(pdf_paths), total_pages


def deduplicate_by_invoice_no(pdf_paths: List[str], get_invoice_no: Callable[[str], str]) -> List[str]:
    """根据发票号码对PDF文件列表去重
    
    遍历文件列表，使用回调函数获取每份文件的发票号码。
    如果发票号码已出现过则跳过，保留首次出现的文件。
    没有发票号码的文件会保留（视为有效文件）。
    
    Args:
        pdf_paths: PDF文件路径列表
        get_invoice_no: 获取发票号码的回调函数，签名为 (path: str) -> str
    
    Returns:
        List[str]: 去重后的文件路径列表，保持原有顺序
    
    Example:
        >>> from extractor import extract_pdf_info
        >>> files = ["a.pdf", "b.pdf", "c.pdf"]
        >>> unique = deduplicate_by_invoice_no(files, lambda p: extract_pdf_info(p).invoice_no)
    """
    seen = set()
    unique = []
    
    for path in pdf_paths:
        invoice_no = get_invoice_no(path)
        if invoice_no and invoice_no not in seen:
            seen.add(invoice_no)
            unique.append(path)
        elif not invoice_no:
            unique.append(path)
    
    return unique