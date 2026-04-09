"""
PDF发票信息提取器模块

从PDF文件中提取发票的关键信息，包括:
- 发票号码
- 开票日期
- 金额
- 购买方/销售方名称
- 备注信息

支持批量提取功能
"""

import re
import logging
import fitz
from typing import List

from .models import InvoiceInfo

logger = logging.getLogger(__name__)


def extract_pdf_info(pdf_path: str) -> InvoiceInfo:
    """从PDF文件中提取发票信息
    
    打开PDF文件，解析第一页内容，使用正则表达式提取以下信息:
    - 发票号码: 匹配 "发票号码:数字" 格式
    - 开票日期: 匹配 "开票日期:YYYY年MM月DD日" 格式
    - 金额: 匹配 "¥数字" 格式
    - 购买方/销售方: 匹配 "名称:" 关键字，根据位置判断是购买方还是销售方
    - 备注: 匹配 "手机号码" 或 "计费时段" 相关行
    
    Args:
        pdf_path: PDF文件的完整路径
    
    Returns:
        InvoiceInfo: 提取的发票信息对象
    
    Raises:
        异常会被捕获并记录日志，返回空的 InvoiceInfo
    
    Example:
        >>> info = extract_pdf_info("invoice.pdf")
        >>> print(f"发票号: {info.invoice_no}, 金额: {info.amount}")
    """
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            doc.close()
            logger.warning(f"PDF文件为空: {pdf_path}")
            return InvoiceInfo(file_path=pdf_path)
        
        text = doc[0].get_text()
        doc.close()
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        invoice_no = date = buyer = seller = remark = ''
        amount = 0.0
        
        for i, line in enumerate(lines):
            if '发票号码' in line:
                m = re.search(r'发票号码[：:](\d+)', line)
                if m:
                    invoice_no = m.group(1)
            elif '开票日期' in line:
                m = re.search(r'开票日期[：:](\d{4})年(\d{2})月(\d{2})日', line)
                if m:
                    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            elif '¥' in line:
                m = re.search(r'¥([\d.]+)', line)
                if m:
                    try:
                        amount = float(m.group(1))
                    except ValueError:
                        pass
            elif '名称：' in line:
                if 8 <= i <= 11:
                    buyer = line.replace('名称：', '')
                elif 15 <= i <= 18:
                    seller = line.replace('名称：', '')
        
        for line in lines:
            if '手机号码' in line or '计费时段' in line:
                remark = line.strip()
        
        return InvoiceInfo(
            file_path=pdf_path,
            invoice_no=invoice_no,
            date=date,
            amount=amount,
            buyer=buyer,
            seller=seller,
            remark=remark
        )
    except Exception as e:
        logger.error(f"提取PDF信息失败 {pdf_path}: {e}", exc_info=True)
        return InvoiceInfo(file_path=pdf_path)


def extract_batch(pdf_paths: List[str]) -> List[InvoiceInfo]:
    """批量提取多个PDF文件的发票信息
    
    Args:
        pdf_paths: PDF文件路径列表
    
    Returns:
        List[InvoiceInfo]: 发票信息列表，顺序与输入一致
    
    Example:
        >>> files = ["a.pdf", "b.pdf", "c.pdf"]
        >>> infos = extract_batch(files)
        >>> for info in infos:
        ...     print(info.invoice_no)
    """
    return [extract_pdf_info(p) for p in pdf_paths]