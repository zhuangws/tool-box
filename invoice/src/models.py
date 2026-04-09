"""
发票数据模型模块

定义发票信息的数据结构和操作方法
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class InvoiceInfo:
    """发票信息数据类
    
    用于存储从PDF发票中提取的结构化信息
    
    属性:
        file_path: PDF文件完整路径
        invoice_no: 发票号码(唯一标识)
        date: 开票日期 (格式: YYYY-MM-DD)
        amount: 发票金额(元)
        buyer: 购买方名称
        seller: 销售方名称
        remark: 备注信息(如手机号码、计费时段等)
    """
    file_path: str = ''
    invoice_no: str = ''
    date: str = ''
    amount: float = 0.0
    buyer: str = ''
    seller: str = ''
    remark: str = ''
    
    def to_dict(self) -> Dict:
        """将发票信息转换为字典
        
        Returns:
            包含所有字段的字典
        """
        return asdict(self)
    
    def __bool__(self) -> bool:
        """判断发票信息是否有效
        
        只要有任意一个有效字段即认为有效
        
        Returns:
            bool: 是否有有效信息
        """
        return bool(self.invoice_no or self.date or self.amount or self.buyer or self.seller)