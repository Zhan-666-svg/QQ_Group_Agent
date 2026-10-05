# -*- coding: utf-8 -*-
import os
import sys

# 保证根目录与 src 目录在 sys.path 中，防止直接双击或从子目录启动时找不到 gui/src 模块
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
for p in [PROJECT_ROOT, CURRENT_DIR, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import yaml
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QApplication, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer

from gui.styles import LIGHT_STYLE
from gui.tabs.tab_monitor import TabMonitor
from gui.tabs.tab_rules import TabRules
from gui.tabs.tab_ai import TabAI
from gui.tabs.tab_history import TabHistory
from gui.tabs.tab_logs import TabLogs

from src.rules_engine import RulesEngine
from src.agent_engine import AgentEngine
from src.notifier import Notifier
from src.database import init_db

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QQ群情报抓取与AI研判智能体中台")
        self.resize(1220, 800)
        self.setMinimumSize(1020, 680)

        # 根目录与配置路径
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, "config", "config.yaml")
        self.rules_path = os.path.join(self.base_dir, "config", "rules.json")

        self.load_configs()
        self.init_engines()
        init_db()

        self.init_ui()

        # 定时更新顶栏系统状态
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_header_status)
        self.status_timer.start(3000)
        self.update_header_status()

    def load_configs(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        with open(self.rules_path, "r", encoding="utf-8") as f:
            self.rules_dict = json.load(f)

    def init_engines(self):
        self.rules_engine = RulesEngine(self.rules_path, self.config)
        self.agent_engine = AgentEngine(self.config)
        self.notifier = Notifier(self.config)

    def reload_engines(self):
        self.load_configs()
        self.rules_engine = RulesEngine(self.rules_path, self.config)
        self.agent_engine = AgentEngine(self.config)
        self.notifier = Notifier(self.config)
        self.update_header_status()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 侧边导航栏 (Soybean Admin 经典极简浅色风格)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(4)

        # 品牌标识区域
        brand_widget = QWidget()
        brand_widget.setObjectName("sidebar_brand")
        b_layout = QVBoxLayout(brand_widget)
        b_layout.setContentsMargins(18, 18, 18, 14)
        b_layout.setSpacing(2)

        title_label = QLabel("QQ 智能体中台")
        title_label.setObjectName("sidebar_title")
        sub_label = QLabel("社群情报抓取与发货研判")
        sub_label.setObjectName("sidebar_subtitle")
        b_layout.addWidget(title_label)
        b_layout.addWidget(sub_label)
        sb_layout.addWidget(brand_widget)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_nav_monitor = self._create_nav_btn("📊 实时监控看板", 0, True)
        self.btn_nav_rules = self._create_nav_btn("🎯 监听群聊与规则", 1)
        self.btn_nav_ai = self._create_nav_btn("🤖 大模型与推送", 2)
        self.btn_nav_history = self._create_nav_btn("📦 发货数据与导出", 3)
        self.btn_nav_logs = self._create_nav_btn("📜 运行日志追踪", 4)

        sb_layout.addWidget(self.btn_nav_monitor)
        sb_layout.addWidget(self.btn_nav_rules)
        sb_layout.addWidget(self.btn_nav_ai)
        sb_layout.addWidget(self.btn_nav_history)
        sb_layout.addWidget(self.btn_nav_logs)
        sb_layout.addStretch()

        version_label = QLabel("NapCatQQ · OneBot v11\nQQNT 智能抓取中台 v1.2")
        version_label.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 14px 18px; line-height: 1.4;")
        sb_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        # 2. 右侧主工作区 (顶栏 Header + 多页面 StackedWidget)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 顶栏 Header
        header = QWidget()
        header.setObjectName("header_bar")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        h_layout.setSpacing(12)

        self.lbl_page_title = QLabel("实时监控看板")
        self.lbl_page_title.setObjectName("header_title")
        self.lbl_page_desc = QLabel("· 全自动高并发社群情报抓取与实时研判流")
        self.lbl_page_desc.setObjectName("header_subtitle")

        h_layout.addWidget(self.lbl_page_title)
        h_layout.addWidget(self.lbl_page_desc)
        h_layout.addStretch()

        # 顶栏快捷状态徽章
        self.badge_gateway = QLabel("网关: 待连接")
        self.badge_gateway.setProperty("class", "badge_danger")

        self.badge_ai = QLabel("研判: 纯规则降级")
        self.badge_ai.setProperty("class", "badge_gray")

        self.badge_cache = QLabel("已缓存群名: 0 个")
        self.badge_cache.setProperty("class", "badge_info")

        h_layout.addWidget(self.badge_gateway)
        h_layout.addWidget(self.badge_ai)
        h_layout.addWidget(self.badge_cache)

        right_layout.addWidget(header)

        # 多页面 StackedWidget
        self.pages_stack = QStackedWidget()
        
        self.tab_logs = TabLogs(self)
        self.tab_monitor = TabMonitor(self)
        self.tab_rules = TabRules(self)
        self.tab_ai = TabAI(self)
        self.tab_history = TabHistory(self)

        self.pages_stack.addWidget(self.tab_monitor)   # 0
        self.pages_stack.addWidget(self.tab_rules)     # 1
        self.pages_stack.addWidget(self.tab_ai)        # 2
        self.pages_stack.addWidget(self.tab_history)   # 3
        self.pages_stack.addWidget(self.tab_logs)      # 4

        right_layout.addWidget(self.pages_stack)
        main_layout.addWidget(right_container)

    def _create_nav_btn(self, text: str, index: int, is_checked: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("class", "nav_btn")
        btn.setCheckable(True)
        btn.setChecked(is_checked)
        btn.setCursor(Qt.PointingHandCursor)
        self.nav_group.addButton(btn, index)
        btn.clicked.connect(lambda: self.switch_page(index))
        return btn

    def switch_page(self, index: int):
        self.pages_stack.setCurrentIndex(index)
        page_titles = [
            ("实时监控看板", "· 全自动高并发社群情报抓取与实时研判流"),
            ("监听群聊与规则", "· 精准白名单、发言人黑名单与关键词正则策略"),
            ("大模型与推送", "· DeepSeek/通义千问研判引擎与外部通知"),
            ("发货数据与导出", "· 沉淀发货地址要素、多行商品规格与一键导出 Excel"),
            ("运行日志追踪", "· NapCat 协议握手、解析流水与异常审计")
        ]
        if 0 <= index < len(page_titles):
            t, d = page_titles[index]
            self.lbl_page_title.setText(t)
            self.lbl_page_desc.setText(d)

        if index == 3:
            self.tab_history.load_history()

    def update_header_status(self):
        # 1. 网关状态
        is_gw_running = False
        if hasattr(self, "tab_monitor") and self.tab_monitor.listener_worker:
            is_gw_running = self.tab_monitor.listener_worker.isRunning()
        
        if is_gw_running:
            self.badge_gateway.setText("🟢 网关: 运行监控中")
            self.badge_gateway.setProperty("class", "badge_success")
        else:
            self.badge_gateway.setText("⚪ 网关: 未连接")
            self.badge_gateway.setProperty("class", "badge_danger")
        self.badge_gateway.style().unpolish(self.badge_gateway)
        self.badge_gateway.style().polish(self.badge_gateway)

        # 2. AI 研判状态
        api_key = self.config.get("agent", {}).get("api_key", "").strip()
        if api_key:
            model = self.config.get("agent", {}).get("model", "AI")
            self.badge_ai.setText(f"🤖 研判: {model}")
            self.badge_ai.setProperty("class", "badge_info")
        else:
            self.badge_ai.setText("⚡ 研判: 本地规则降级")
            self.badge_ai.setProperty("class", "badge_gray")
        self.badge_ai.style().unpolish(self.badge_ai)
        self.badge_ai.style().polish(self.badge_ai)

        # 3. 缓存群名数
        cache_path = os.path.join(self.base_dir, "data", "group_cache.json")
        count = 0
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    c = json.load(f)
                    count = len(c)
            except Exception:
                pass
        self.badge_cache.setText(f"👥 已映射群名: {count} 个")
        self.badge_cache.style().unpolish(self.badge_cache)
        self.badge_cache.style().polish(self.badge_cache)

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
