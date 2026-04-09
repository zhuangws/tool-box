"""
PDF布局控制模块

支持不同的PDF合并布局方式:
- 单页单张 (1列1行)
- 单页两张 (1列2行)
- 单页四张 (2列2行)
"""

import logging
from typing import List, Tuple
import fitz

logger = logging.getLogger(__name__)


class PageLayout:
    """PDF页面布局枚举"""
    ONE_PER_PAGE = "1列1行"    # 一页1张
    TWO_PER_PAGE = "1列2行"    # 一页2张
    FOUR_PER_PAGE = "2列2行"   # 一页4张


def get_layout_config(layout: str) -> Tuple[int, int, bool]:
    """获取布局配置
    
    Args:
        layout: 布局类型字符串
    
    Returns:
        Tuple[列数, 行数, 是否横向优先]
    """
    configs = {
        PageLayout.ONE_PER_PAGE: (1, 1, False),     # 一页1张
        PageLayout.TWO_PER_PAGE: (1, 2, False),     # 一页2张 (竖向)
        PageLayout.FOUR_PER_PAGE: (2, 2, True),    # 一页4张 (横向: 2列2行)
    }
    return configs.get(layout, (1, 1, False))


def merge_pdfs_with_layout(pdf_paths: List[str], output: str, layout: str = PageLayout.ONE_PER_PAGE) -> Tuple[int, int]:
    """按指定布局合并PDF文件
    
    根据布局参数，将多个PDF文件合并到一个或多个页面中:
    - 1列1行: 每页放置1张发票
    - 1列2行: 每页垂直放置2张发票 (从上到下)
    - 2列2行: A4横向，每页放置4张发票 (2行2列)
    
    Args:
        pdf_paths: PDF文件路径列表
        output: 输出文件路径
        layout: 布局类型 (默认: 1列1行)
    
    Returns:
        Tuple[文件数, 页数]
    """
    cols, rows, horizontal = get_layout_config(layout)
    per_page = cols * rows
    
    if not pdf_paths:
        return 0, 0
    
    src_docs = []
    for path in pdf_paths:
        try:
            doc = fitz.open(path)
            src_docs.append(doc)
        except Exception as e:
            logger.error(f"打开文件失败 {path}: {e}")
            continue
    
    if not src_docs:
        logger.warning("没有有效的PDF文件")
        return 0, 0
    
    output_doc = fitz.open()
    total_pages = 0
    
    # 判断是否使用横向A4 (2列2行时)
    if layout == PageLayout.FOUR_PER_PAGE:
        # A4横向
        page_width = 841
        page_height = 595
    else:
        # A4竖向
        page_width = 595
        page_height = 841
    
    margin = 10  # 边距
    
    # 计算每个发票区域的尺寸
    usable_width = page_width - 2 * margin
    usable_height = page_height - 2 * margin
    cell_width = (usable_width - (cols - 1) * margin) / cols
    cell_height = (usable_height - (rows - 1) * margin) / rows
    
    # 按布局分批处理
    for i in range(0, len(src_docs), per_page):
        batch = src_docs[i:i + per_page]
        
        # 创建新页面
        page = output_doc.new_page(width=page_width, height=page_height)
        
        for idx, src_doc in enumerate(batch):
            if layout == PageLayout.FOUR_PER_PAGE:
                # 2列2行: 横向排布 (先填满列)
                col = idx % cols
                row = idx // cols
            elif horizontal:
                # 横向排布: 先填满行
                col = idx % cols
                row = idx // cols
            else:
                # 竖向排布: 先填满列
                col = idx % cols
                row = idx // cols
            
            # 计算目标位置 (左上角坐标)
            x0 = margin + col * (cell_width + margin)
            y0 = margin + row * (cell_height + margin)
            x1 = x0 + cell_width
            y1 = y0 + cell_height
            
            # 源文档的页面
            if len(src_doc) > 0:
                page.show_pdf_page(
                    fitz.Rect(x0, y0, x1, y1),
                    src_doc,
                    0,
                    clip=None
                )
        
        total_pages += 1
    
    # 保存输出
    output_doc.save(output)
    output_doc.close()
    
    # 关闭所有源文档
    for doc in src_docs:
        doc.close()
    
    return len(pdf_paths), total_pages


def merge_pdfs_standard(pdf_paths: List[str], output: str) -> Tuple[int, int]:
    """标准合并 (每页一张，原样保留)
    
    Args:
        pdf_paths: PDF文件路径列表
        output: 输出文件路径
    
    Returns:
        Tuple[文件数, 页数]
    """
    return merge_pdfs_with_layout(pdf_paths, output, PageLayout.ONE_PER_PAGE)