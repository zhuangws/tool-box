#!/usr/bin/env python3
"""
PDF发票合并工具 - 主程序入口
功能：支持PDF发票文件的添加、合并、去重、打印等操作
"""

import os
import sys
import threading
import logging
from datetime import datetime
from typing import List, Dict

# 确定项目根目录
if getattr(sys, 'frozen', False):
    # 打包环境 - 使用PyInstaller的临时目录
    if hasattr(sys, '_MEIPASS'):
        _root_dir = sys._MEIPASS
    else:
        _root_dir = os.path.dirname(sys.executable)
else:
    # 开发环境
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from plugins.invoice import InvoiceInfo, extract_pdf_info, merge_pdfs_with_layout, PageLayout

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_merge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFMergeApp:
    """PDF发票合并工具主程序类
    
    提供图形界面用于:
    - 添加和管理PDF发票文件
    - 提取并显示发票信息(发票号码、日期、金额、购买方、销售方等)
    - 合并多个PDF文件
    - 自动去重功能
    - 打印输出的PDF文件
    """
    
    # 表格列配置: (列ID, 显示名称, 列宽度)
    COLUMNS = [
        ("file_path", "文件路径", 280),
        ("invoice_no", "发票号码", 140),
        ("buyer", "购买方", 110),
        ("date", "开票日期", 90),
        ("seller", "销售方", 180),
        ("amount", "金额", 70),
        ("remark", "备注", 220)
    ]
    
    def __init__(self, root):
        """初始化主窗口
        
        Args:
            root: tkinter根窗口对象
        """
        self.root = root
        self.root.title("PDF发票合并工具")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)
        
        # 颜色配置
        self.bg = '#f3f3f3'
        self.card = '#ffffff'
        self.accent = '#0078d4'
        self.text = '#1a1a1a'
        self.subtext = '#616161'
        
        # 数据存储
        self.pdf_files: List[str] = []  # PDF文件路径列表
        self.pdf_infos: Dict[str, InvoiceInfo] = {}  # 路径到发票信息的映射
        self.deduplicate = tk.BooleanVar()  # 去重选项
        self.layout = tk.StringVar(value=PageLayout.ONE_PER_PAGE)  # 页面布局
        self.working_dir = os.getcwd()  # 工作目录
        self.is_working = False  # 是否正在处理
        self.last_output = ''  # 最近一次输出的文件路径
        
        # UI组件引用
        self.merge_btn = None
        self.print_btn = None
        self.tree = None
        self.status = None
        self.total = None
        self.out_entry = None
        self.progress = None
        self.progress_text = None
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        self.root.configure(bg='#F2F2F2')
        
        # 标题栏
        titlebar = tk.Frame(self.root, bg='#3498DB', height=60)
        titlebar.pack(fill=tk.X)
        titlebar.pack_propagate(False)
        
        title_inner = tk.Frame(titlebar, bg='#3498DB')
        title_inner.pack(fill=tk.BOTH, expand=True, padx=24)
        
        # 左侧图标和标题
        tk.Label(title_inner, text="📄", font=("Segoe UI Emoji", 24), bg='#3498DB', fg='white').pack(side=tk.LEFT, pady=14)
        tk.Label(title_inner, text="PDF发票合并工具", font=("Microsoft YaHei", 16, "bold"), bg='#3498DB', fg='white').pack(side=tk.LEFT, pady=14, padx=(8, 0))
        
        # 右侧版本号
        tk.Label(title_inner, text="v1.0.0", font=("Segoe UI", 9), bg='#3498DB', fg='#D6EAF8').pack(side=tk.RIGHT, pady=14)
        
        # 主容器
        main = tk.Frame(self.root, bg='#F2F2F2')
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # 工具栏
        self._create_toolbar(main)
        
        # 表格区域 (白色背景)
        table_card = tk.Frame(main, bg='white', relief='solid', bd=1)
        table_card.pack(fill=tk.BOTH, expand=True)
        
        # 表格
        self._create_table(table_card)
        
        # 状态栏
        self._create_status_bar(main)
        
        # 底部区域 (灰色背景) - 合并按钮和保存路径
        bottom_card = tk.Frame(main, bg='#F2F2F2', relief='solid', bd=0)
        bottom_card.pack(fill=tk.X, pady=(12, 0))
        
        # 按钮组
        self._create_action_buttons(bottom_card)
    
    def _create_toolbar(self, parent):
        """创建工具栏
        
        包含: 添加文件、添加文件夹、移除选中、清空列表、自动去重选项、布局选择
        """
        toolbar = tk.Frame(parent, bg='white')
        toolbar.pack(fill=tk.X, pady=(0, 16))
        toolbar.config(highlightbackground="#E8E8E8", highlightthickness=1, bd=0)
        
        btn_frame = tk.Frame(toolbar, bg='white')
        btn_frame.pack(side=tk.LEFT, padx=16, pady=12)
        
        # 主按钮 (蓝色)
        main_buttons = [
            ("添加文件", self._select_files, '#3498DB'),
            ("添加文件夹", self._select_folder, '#3498DB'),
        ]
        
        for text, cmd, color in main_buttons:
            btn = tk.Button(btn_frame, text=text, command=cmd,
                           font=("Microsoft YaHei", 9), bg=color, fg='white',
                           relief='flat', bd=0, padx=16, pady=7, cursor='hand2',
                           highlightthickness=0, borderwidth=0)
            btn.config(highlightbackground=color)
            btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # 分隔线
        sep = tk.Frame(btn_frame, bg='#E8E8E8', width=1)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=12, pady=4)
        
        # 次要按钮 (灰色，带悬停效果)
        sub_buttons = [
            ("移除选中", self._remove_selected, '#999999'),
            ("清空列表", self._clear, '#999999'),
        ]
        
        for text, cmd, color in sub_buttons:
            btn = tk.Button(btn_frame, text=text, command=cmd,
                           font=("Microsoft YaHei", 9), bg='#F5F5F5', fg=color,
                           relief='flat', bd=0, padx=16, pady=7, cursor='hand2',
                           highlightthickness=0, borderwidth=0)
            # 悬停效果
            btn.bind('<Enter>', lambda e: e.widget.config(bg='#E8E8E8'))
            btn.bind('<Leave>', lambda e: e.widget.config(bg='#F5F5F5'))
            btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # 右侧选项区
        right_frame = tk.Frame(toolbar, bg='white')
        right_frame.pack(side=tk.RIGHT, padx=16, pady=12)
        
        tk.Checkbutton(right_frame, text="自动去重", variable=self.deduplicate,
                      font=("Microsoft YaHei", 9), bg='white', fg='#666666',
                      selectcolor='white', activebackground='white').pack(side=tk.LEFT, padx=16)
        
        # 布局选择
        tk.Label(right_frame, text="布局:", font=("Microsoft YaHei", 9), bg='white', fg='#666666').pack(side=tk.LEFT, padx=(8, 4))
        
        layout_frame = tk.Frame(right_frame, bg='white')
        layout_frame.pack(side=tk.LEFT, padx=4)
        
        for layout in [PageLayout.ONE_PER_PAGE, PageLayout.TWO_PER_PAGE, PageLayout.FOUR_PER_PAGE]:
            tk.Radiobutton(layout_frame, text=layout, variable=self.layout, value=layout,
                          font=("Microsoft YaHei", 9), bg='white', fg='#666666', 
                          selectcolor='white', activebackground='white').pack(side=tk.LEFT, padx=4)
    
    def _create_button(self, parent, text, cmd):
        """创建统一样式的按钮
        
        Args:
            parent: 父容器
            text: 按钮文本
            cmd: 按钮回调函数
        
        Returns:
            配置好的按钮对象
        """
        btn = tk.Button(parent, text=text, command=cmd,
                       font=("Segoe UI", 9), bg='#ffffff', fg='#606266',
                       relief='flat', bd=0, padx=14, pady=6, cursor='hand2')
        btn.bind('<Enter>', lambda e: e.widget.config(bg='#ecf5ff'))
        btn.bind('<Leave>', lambda e: e.widget.config(bg='#ffffff'))
        return btn
    
    def _create_table(self, parent):
        """创建文件列表表格
        
        显示PDF文件及其提取的发票信息
        """
        # 表格容器
        container = tk.Frame(parent, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # 创建Treeview
        style = ttk.Style()
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=36)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"), background='#F0F0F0', foreground='#333333')
        
        self.tree = ttk.Treeview(container, columns=[c[0] for c in self.COLUMNS], show='headings',
                                style="Treeview", selectmode='extended')
        
        # 垂直滚动条
        v_scroll = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scroll = ttk.Scrollbar(container, orient='horizontal', command=self.tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        for cid, cname, cwidth in self.COLUMNS:
            self.tree.heading(cid, text=cname)
            self.tree.column(cid, width=cwidth, minwidth=120, anchor='center')
        
        # 斑马纹
        self.tree.tag_configure('odd', background='#FAFAFA')
        self.tree.tag_configure('even', background='#FFFFFF')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 绑定双击事件
        self.tree.bind('<Double-Button-1>', self._on_double_click)
    
    def _create_status_bar(self, parent):
        """创建状态栏
        
        显示文件数量和总金额
        """
        info = tk.Frame(parent, bg='#F2F2F2')
        info.pack(fill=tk.X, pady=(8, 0))
        
        self.status = tk.Label(info, text="共 0 个文件", font=("Microsoft YaHei", 9), bg='#F2F2F2', fg='#666666')
        self.status.pack(side=tk.LEFT)
        
        self.total = tk.Label(info, text="总金额: ¥0.00", font=("Microsoft YaHei", 9, "bold"), bg='#F2F2F2', fg='#3498DB')
        self.total.pack(side=tk.RIGHT)
    
    def _create_output_section(self, parent):
        """创建输出路径选择区域
        
        让用户选择合并后PDF文件的保存位置
        """
        out_frame = tk.Frame(parent, bg='white')
        out_frame.pack(fill=tk.X, padx=16, pady=16)
        
        tk.Label(out_frame, text="保存到:", font=("Microsoft YaHei", 9), bg='white', fg='#666666').pack(side=tk.LEFT, padx=(0, 8))
        
        # 输入框样式
        self.out_entry = tk.Entry(out_frame, font=("Microsoft YaHei", 9), bg='#FAFAFA', fg='#333333', 
                                  relief='solid', bd=1, insertbackground='#3498DB')
        self.out_entry.config(highlightbackground="#E8E8E8", highlightthickness=1)
        self.out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        
        browse_btn = tk.Button(out_frame, text="浏览", command=self._select_output,
                              font=("Microsoft YaHei", 9), bg='#F5F5F5', fg='#666666',
                              relief='flat', bd=0, padx=20, pady=6, cursor='hand2')
        browse_btn.pack(side=tk.LEFT)
    
    def _create_progress_section(self, parent):
        """创建进度条区域
        
        显示合并进度
        """
        progress = tk.Frame(parent, bg=self.bg)
        progress.pack(fill=tk.X, pady=(0, 8))
        
        self.progress = ttk.Progressbar(progress, mode='determinate', length=100)
        self.progress.pack(fill=tk.X)
        
        self.progress_text = tk.Label(progress, text="", font=("Segoe UI", 9), bg=self.bg, fg=self.subtext)
        self.progress_text.pack()
    
    def _create_action_buttons(self, parent):
        """创建操作按钮
        
        包含: 开始合并、打印PDF
        """
        btn_group = tk.Frame(parent, bg='#F2F2F2')
        btn_group.pack(fill=tk.X, padx=0, pady=0)
        
        # 左侧: 输出路径区域
        out_frame = tk.Frame(btn_group, bg='#F2F2F2')
        out_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=16, pady=12)
        
        tk.Label(out_frame, text="保存到:", font=("Microsoft YaHei", 9), bg='#F2F2F2', fg='#666666').pack(side=tk.LEFT, padx=(0, 8))
        
        self.out_entry = tk.Entry(out_frame, font=("Microsoft YaHei", 9), bg='white', fg='#333333', 
                                  relief='solid', bd=1, insertbackground='#3498DB')
        self.out_entry.config(highlightbackground="#CCCCCC", highlightthickness=1)
        self.out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        
        browse_btn = tk.Button(out_frame, text="浏览", command=self._select_output,
                              font=("Microsoft YaHei", 9), bg='white', fg='#666666',
                              relief='solid', bd=1, padx=16, pady=5, cursor='hand2',
                              activebackground='#3498DB', activeforeground='white')
        browse_btn.bind('<Enter>', lambda e: browse_btn.config(bg='#E8E8E8'))
        browse_btn.bind('<Leave>', lambda e: browse_btn.config(bg='white'))
        browse_btn.pack(side=tk.LEFT)
        
        # 进度条区域 (初始隐藏)
        self.progress_frame = tk.Frame(btn_group, bg='#F2F2F2')
        
        self.progress = ttk.Progressbar(self.progress_frame, mode='determinate', length=100)
        self.progress.pack(fill=tk.X, pady=(0, 6))
        
        self.progress_text = tk.Label(self.progress_frame, text="", font=("Microsoft YaHei", 9), bg='#F2F2F2', fg='#666666')
        self.progress_text.pack()
        
        # 右侧: 按钮区域
        action_frame = tk.Frame(btn_group, bg='#F2F2F2')
        action_frame.pack(side=tk.RIGHT, padx=16)
        
        # 合并按钮 (蓝色圆角效果 - 使用突出效果代替)
        self.merge_btn = tk.Button(action_frame, text="开始合并", command=self._merge,
                        font=("Microsoft YaHei", 10, "bold"), bg='#3498DB', fg='white',
                        relief='flat', bd=0, padx=32, pady=10, cursor='hand2')
        self.merge_btn.pack(side=tk.LEFT, padx=6)
        
        # 打印按钮 (白色边框圆角效果)
        self.print_btn = tk.Button(action_frame, text="打印PDF", command=self._print_pdf,
                        font=("Microsoft YaHei", 10), bg='white', fg='#666666',
                        relief='solid', bd=1, padx=24, pady=10, cursor='hand2',
                        state=tk.DISABLED)
        self.print_btn.bind('<Enter>', lambda e: self.print_btn.config(bg='#E8E8E8') if self.print_btn['state'] == 'normal' else None)
        self.print_btn.bind('<Leave>', lambda e: self.print_btn.config(bg='white'))
        self.print_btn.pack(side=tk.LEFT, padx=6)
    
    def _update_status(self):
        """更新状态栏显示的信息
        
        更新文件数量和总金额统计
        """
        self.status.config(text=f"{len(self.pdf_files)} 个文件")
        total = sum(info.amount for info in self.pdf_infos.values() if info)
        self.total.config(text=f"总金额(元): {total:.3f}")
    
    def _add_pdf(self, path: str):
        """添加单个PDF文件到列表
        
        Args:
            path: PDF文件的完整路径
        """
        if path not in self.pdf_files:
            self.pdf_files.append(path)
            info = extract_pdf_info(path)
            self.pdf_infos[path] = info
            self.tree.insert('', tk.END, values=(
                path, info.invoice_no, info.buyer, info.date,
                info.seller, f"{info.amount:.3f}", info.remark[:100]
            ))
    
    def _select_files(self):
        """打开文件选择对话框,选择多个PDF文件"""
        files = filedialog.askopenfilenames(title="选择PDF", filetypes=[("PDF", "*.pdf")])
        for f in files:
            self._add_pdf(f)
        self._update_status()
    
    def _select_folder(self):
        """打开文件夹选择对话框,添加文件夹中所有PDF文件"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            self.working_dir = folder
            files = sorted([os.path.join(folder, f) for f in os.listdir(folder) 
                          if f.lower().endswith('.pdf')])
            for f in files:
                self._add_pdf(f)
            self._update_status()
    
    def _clear(self):
        """清空所有已添加的文件"""
        self.pdf_files.clear()
        self.pdf_infos.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_status()
    
    def _remove_selected(self):
        """移除表格中选中的文件"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选中要移除的发票")
            return
        
        for item in selection:
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
                if path in self.pdf_files:
                    self.pdf_files.remove(path)
                if path in self.pdf_infos:
                    del self.pdf_infos[path]
                self.tree.delete(item)
        
        self._update_status()
    
    def _select_output(self):
        """打开保存对话框,选择输出文件路径"""
        default = f"合并发票_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        fn = filedialog.asksaveasfilename(
            title="保存", 
            defaultextension=".pdf", 
            initialfile=default, 
            initialdir=self.working_dir
        )
        if fn:
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, fn)
    
    def _merge(self):
        """开始合并PDF文件
        
        检查输入有效性,在后台线程执行合并操作
        """
        if self.is_working:
            messagebox.showwarning("提示", "正在处理中，请稍后")
            return
        
        if not self.pdf_files:
            messagebox.showwarning("提示", "请先添加文件")
            return
        
        output = self.out_entry.get().strip()
        if not output:
            output = os.path.join(self.working_dir, f"合并发票_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        # 去重处理
        files_to_merge = self._apply_deduplication(self.pdf_files.copy())
        
        if not files_to_merge:
            messagebox.showwarning("提示", "没有需要合并的文件")
            return
        
        self.is_working = True
        self.merge_btn.config(state=tk.DISABLED, bg='#BDC3C7')
        
        # 显示进度条区域
        self.progress_frame.pack(fill=tk.X, padx=16, pady=(8, 12))
        
        self.progress['maximum'] = len(files_to_merge)
        self.progress['value'] = 0
        self.progress_text.config(text="开始合并...")
        
        # 启动合并线程
        thread = threading.Thread(
            target=self._merge_worker,
            args=(files_to_merge, output),
            daemon=True
        )
        thread.start()
    
    def _apply_deduplication(self, files: List[str]) -> List[str]:
        """根据发票号码应用去重规则
        
        Args:
            files: 原始文件列表
        
        Returns:
            去重后的文件列表
        """
        if not self.deduplicate.get():
            return files
        
        seen = set()
        unique_files = []
        for f in files:
            info = self.pdf_infos.get(f)
            if info and info.invoice_no:
                if info.invoice_no not in seen:
                    seen.add(info.invoice_no)
                    unique_files.append(f)
            else:
                # 没有发票号码的文件也保留
                unique_files.append(f)
        
        return unique_files
    
    def _merge_worker(self, files: List[str], output: str):
        """合并工作线程
        
        在后台线程中执行PDF合并操作
        
        Args:
            files: 要合并的文件路径列表
            output: 输出文件路径
        """
        try:
            selected_layout = self.layout.get()
            
            if selected_layout == PageLayout.ONE_PER_PAGE:
                # 标准合并
                merged = fitz.open()
                total_pages = 0
                
                for i, pdf_path in enumerate(files, 1):
                    try:
                        doc = fitz.open(pdf_path)
                        merged.insert_pdf(doc)
                        total_pages += len(doc)
                        doc.close()
                        self.root.after(0, self._update_progress, i, len(files))
                    except Exception as e:
                        logger.error(f"合并文件失败 {pdf_path}: {e}")
                        continue
                
                merged.save(output)
                merged.close()
                self.root.after(0, self._merge_complete, True, f"合并完成: {len(files)}个文件, {total_pages}页", output)
            else:
                # 使用布局合并
                count, pages = merge_pdfs_with_layout(files, output, selected_layout)
                self.root.after(0, self._update_progress, len(files), len(files))
                self.root.after(0, self._merge_complete, True, f"合并完成: {count}个文件, {pages}页", output)
                
        except Exception as e:
            logger.error(f"合并失败: {e}", exc_info=True)
            self.root.after(0, self._merge_complete, False, f"合并失败: {str(e)}", '')
    
    def _update_progress(self, current: int, total: int):
        """更新进度条显示
        
        Args:
            current: 当前处理数量
            total: 总数量
        """
        self.progress['value'] = current
        self.progress_text.config(text=f"处理中: {current}/{total}")
        self.root.update_idletasks()
    
    def _merge_complete(self, success: bool, msg: str, output: str = ''):
        """合并完成回调
        
        更新UI状态,启用打印按钮
        
        Args:
            success: 是否合并成功
            msg: 状态消息
            output: 输出的文件路径(成功时有效)
        """
        self.is_working = False
        self.merge_btn.config(state=tk.NORMAL, bg=self.accent)
        
        if success:
            self.last_output = output
            self.print_btn.config(state=tk.NORMAL, bg='#ffffff')
            messagebox.showinfo("完成", msg)
        else:
            messagebox.showerror("错误", msg)
    
    def _print_pdf(self):
        """使用系统默认程序打开PDF文件,让用户自行打印"""
        if not self.last_output or not os.path.exists(self.last_output):
            messagebox.showwarning("提示", "请先合并PDF文件")
            return
        
        try:
            import subprocess
            import sys
            
            if sys.platform == 'win32':
                os.startfile(self.last_output)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.last_output])
            else:
                subprocess.run(['xdg-open', self.last_output])
            
            messagebox.showinfo("提示", "已打开PDF文件，请在打开的窗口中点击打印")
        except Exception as e:
            logger.error(f"打开PDF失败: {e}")
            messagebox.showerror("错误", f"无法打开PDF: {e}")
    
    def _on_double_click(self, event):
        """处理表格双击事件
        
        显示选中行的发票详细信息
        
        Args:
            event: tkinter事件对象
        """
        item = self.tree.identify_row(event.y)
        if item:
            values = self.tree.item(item, 'values')
            if values:
                self._show_detail_dialog(values)
    
    def _show_detail_dialog(self, values):
        """显示发票详情对话框
        
        Args:
            values: 发票信息元组
        """
        win = tk.Toplevel(self.root)
        win.title("发票详情")
        win.geometry("500x440")
        win.resizable(False, False)
        win.configure(bg='white')
        win.transient(self.root)
        win.grab_set()
        
        # 标题栏
        titlebar = tk.Frame(win, bg='#3498DB', height=48)
        titlebar.pack(fill=tk.X)
        
        tk.Label(titlebar, text="发票详情", font=("Microsoft YaHei", 13, "bold"), 
                bg='#3498DB', fg='white').pack(pady=11)
        
        # 内容区域
        content = tk.Frame(win, bg='white')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)
        
        fields = ['文件路径', '发票号码', '购买方', '开票日期', '销售方', '金额', '备注']
        
        # 详细信息
        for field, value in zip(fields, values):
            row = tk.Frame(content, bg='white')
            row.pack(fill=tk.X, pady=6)
            
            label = tk.Label(row, text=field, font=("Microsoft YaHei", 9), 
                           bg='white', fg='#3498DB', width=10, anchor='w')
            label.pack(side=tk.LEFT)
            
            value_label = tk.Label(row, text=value if value else '-', font=("Microsoft YaHei", 9), 
                                  bg='white', fg='#333333', wraplength=310, justify='left', anchor='w')
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        
        # 按钮区域
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(pady=(20, 0), fill=tk.X)
        
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        tk.Button(btn_frame, text="复制全部", command=lambda: self._copy_detail(values, fields), 
                 font=("Microsoft YaHei", 9), bg='#3498DB', fg='white', 
                 relief='flat', bd=0, padx=24, pady=8, cursor='hand2').grid(row=0, column=0, padx=4)
        
        tk.Button(btn_frame, text="关闭", command=win.destroy, font=("Microsoft YaHei", 9),
                 bg='#F0F0F0', fg='#666666', relief='flat', bd=0, padx=24, pady=8, cursor='hand2').grid(row=0, column=1, padx=4)
    
    def _copy_detail(self, values, fields):
        """复制详情到剪贴板"""
        text = '\n'.join([f"{fields[i]}: {values[i]}" for i in range(len(fields))])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("提示", "已复制到剪贴板")


def main():
    """主程序入口"""
    root = tk.Tk()
    app = PDFMergeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()