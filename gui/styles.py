# -*- coding: utf-8 -*-
"""
现代化高质感极简设计风格 (Soybean Admin / Tailwind 现代设计规范)
主色: #2563EB (科技蓝) | 成功: #10B981 | 警告: #F59E0B | 危险: #EF4444 | 底色: #F8FAFC
特点: 极简纯净、10-12px 现代圆角、层次卡片、防视觉疲劳、数据表格零卡顿
"""

LIGHT_STYLE = """
/* 全局基础设置与抗锯齿字体族 */
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
    font-size: 13px;
    color: #1E293B;
    outline: none;
}

QWidget {
    background-color: #F8FAFC;
}

/* 顶部综合状态 Header */
#header_bar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    min-height: 56px;
    max-height: 56px;
    padding: 0 20px;
}

#header_title {
    font-size: 15px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.2px;
}

#header_subtitle {
    font-size: 12px;
    color: #64748B;
    margin-left: 8px;
}

/* 侧边导航栏 (Soybean 浅色经典侧边栏) */
#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
    min-width: 220px;
    max-width: 220px;
}

#sidebar_brand {
    padding: 20px 18px 16px 18px;
    border-bottom: 1px solid #F1F5F9;
}

#sidebar_title {
    font-size: 16px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.4px;
}

#sidebar_subtitle {
    font-size: 11px;
    color: #64748B;
    font-weight: 500;
    margin-top: 4px;
}

/* 侧边栏胶囊导航按钮 */
QPushButton.nav_btn {
    text-align: left;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    margin: 4px 12px;
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
    border-left: 3.5px solid #2563EB;
    border-radius: 6px;
}

/* 现代化卡片容器 (纯白背景 + 细腻微描边 + 优雅圆角) */
QFrame.card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
}

QFrame.card_subtle {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px;
}

/* 现代化核心指标统计卡片 */
QFrame.stat_card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
}

QLabel.stat_title {
    font-size: 12px;
    color: #64748B;
    font-weight: 600;
    letter-spacing: 0.1px;
}

QLabel.stat_value {
    font-size: 26px;
    font-weight: 800;
    color: #0F172A;
    margin-top: 6px;
    letter-spacing: -0.6px;
}

/* 状态徽章 (Badges) */
QLabel.badge_success {
    background-color: #DCFCE7;
    color: #15803D;
    font-size: 11px;
    font-weight: 700;
    border-radius: 4px;
    padding: 3px 8px;
}

QLabel.badge_warning {
    background-color: #FEF3C7;
    color: #B45309;
    font-size: 11px;
    font-weight: 700;
    border-radius: 4px;
    padding: 3px 8px;
}

QLabel.badge_danger {
    background-color: #FEE2E2;
    color: #B91C1C;
    font-size: 11px;
    font-weight: 700;
    border-radius: 4px;
    padding: 3px 8px;
}

QLabel.badge_info {
    background-color: #EFF6FF;
    color: #1D4ED8;
    font-size: 11px;
    font-weight: 700;
    border-radius: 4px;
    padding: 3px 8px;
}

QLabel.badge_gray {
    background-color: #F1F5F9;
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    border-radius: 4px;
    padding: 3px 8px;
}

/* 现代化操作按钮 */
QPushButton {
    padding: 7px 16px;
    border-radius: 8px;
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

QPushButton.btn_ghost {
    background-color: transparent;
    border: none;
    color: #64748B;
    padding: 4px 8px;
}

QPushButton.btn_ghost:hover {
    background-color: #F1F5F9;
    color: #0F172A;
}

/* 输入框与下拉选择框 */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 12px;
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
    padding-right: 10px;
}

/* 表格优化 (极其流畅、无卡顿、高屏占比现代数据看板) */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: #F1F5F9;
    alternate-background-color: #F8FAFC;
    outline: none;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #EFF6FF;
    color: #1E40AF;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    font-weight: 700;
    font-size: 12px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 10px 12px;
}

/* 列表框 */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    outline: none;
    padding: 6px;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 3px;
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

/* 现代化分组框 (GroupBox) */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 14px;
    font-weight: 700;
    font-size: 13px;
    padding-top: 18px;
    padding-left: 14px;
    padding-right: 14px;
    padding-bottom: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
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
