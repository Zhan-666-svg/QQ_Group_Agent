# -*- coding: utf-8 -*-
"""
现代化高质感极简风格 QSS 样式表 (基于 Tailwind / Soybean Admin 设计语言)
主色: #2563EB (现代科技蓝) | 成功: #10B981 | 警告: #F59E0B | 危险: #EF4444 | 背景: #F8FAFC
特点: 扁平无边框质感、圆角卡片、微交互状态、清爽抗疲劳
"""

LIGHT_STYLE = """
/* 全局基础设置与抗锯齿字体 */
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    color: #1E293B;
    outline: none;
}

QWidget {
    background-color: #F8FAFC;
}

/* 侧边导航栏 */
#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
    min-width: 220px;
    max-width: 220px;
}

#sidebar_brand {
    padding: 22px 18px 14px 18px;
}

#sidebar_title {
    font-size: 16px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.3px;
}

#sidebar_subtitle {
    font-size: 11px;
    color: #64748B;
    font-weight: 500;
    margin-top: 3px;
}

/* 侧边栏按钮 (现代胶囊态) */
QPushButton.nav_btn {
    text-align: left;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    margin: 3px 12px;
    background-color: transparent;
    color: #475569;
}

QPushButton.nav_btn:hover {
    background-color: #F1F5F9;
    color: #2563EB;
}

QPushButton.nav_btn:checked {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 700;
    border-left: 3px solid #2563EB;
    border-radius: 6px;
}

/* 现代化卡片容器 */
QFrame.card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px;
}

/* 现代化统计卡片 */
QFrame.stat_card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 18px;
}

QLabel.stat_title {
    font-size: 12px;
    color: #64748B;
    font-weight: 600;
}

QLabel.stat_value {
    font-size: 24px;
    font-weight: 800;
    color: #0F172A;
    margin-top: 4px;
    letter-spacing: -0.5px;
}

/* 按钮通用风格 (微圆角扁平) */
QPushButton {
    padding: 7px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid transparent;
}

QPushButton.btn_primary {
    background-color: #2563EB;
    color: #FFFFFF;
}

QPushButton.btn_primary:hover {
    background-color: #1D4ED8;
}

QPushButton.btn_primary:pressed {
    background-color: #1E40AF;
}

QPushButton.btn_primary:disabled {
    background-color: #93C5FD;
    color: #FFFFFF;
}

QPushButton.btn_success {
    background-color: #10B981;
    color: #FFFFFF;
}

QPushButton.btn_success:hover {
    background-color: #059669;
}

QPushButton.btn_danger {
    background-color: #EF4444;
    color: #FFFFFF;
}

QPushButton.btn_danger:hover {
    background-color: #DC2626;
}

QPushButton.btn_outline {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #334155;
}

QPushButton.btn_outline:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
    color: #0F172A;
}

/* 输入框与下拉选择框 */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 12px;
    color: #0F172A;
    font-size: 13px;
}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover {
    border-color: #94A3B8;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1.5px solid #2563EB;
    background-color: #FFFFFF;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* 表格优化 (高性能、完全不卡顿、现代化无框交替行风格) */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    outline: none;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #EFF6FF;
    color: #1E40AF;
    font-weight: 500;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 700;
    font-size: 12px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 9px 10px;
}

/* 列表框 */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    padding: 7px 10px;
    border-radius: 6px;
    margin-bottom: 2px;
}

QListWidget::item:hover {
    background-color: #F1F5F9;
}

QListWidget::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 600;
}

/* 现代化极细滚动条 (极致平滑、不遮挡内容) */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 28px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    min-width: 28px;
    border-radius: 3px;
}

/* 现代化分组框 */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 14px;
    font-weight: 700;
    font-size: 13px;
    padding-top: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #0F172A;
}

/* 单选框与复选框 */
QRadioButton, QCheckBox {
    spacing: 8px;
    font-weight: 500;
    color: #334155;
}

QRadioButton::indicator, QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""
