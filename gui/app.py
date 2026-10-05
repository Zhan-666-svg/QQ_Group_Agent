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
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

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
        self.resize(1180, 780)
        self.setMinimumSize(980, 640)

        # 根目录与配置路径
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, "config", "config.yaml")
        self.rules_path = os.path.join(self.base_dir, "config", "rules.json")

        self.load_configs()
        self.init_engines()
        init_db()

        self.init_ui()

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
        self.rules_engine = RulesEngine(self.rules_path, self.config)
        self.agent_engine = AgentEngine(self.config)
        self.notifier = Notifier(self.config)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 侧边导航栏 (Soybean Admin 风格)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(4)

        title_label = QLabel("QQ 智能体中台")
        title_label.setObjectName("sidebar_title")
        sub_label = QLabel("社群情报抓取与AI研判")
        sub_label.setObjectName("sidebar_subtitle")
        sb_layout.addWidget(title_label)
        sb_layout.addWidget(sub_label)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_nav_monitor = self._create_nav_btn("📊 实时监控看板", 0, True)
        self.btn_nav_rules = self._create_nav_btn("🎯 监听群聊与规则", 1)
        self.btn_nav_ai = self._create_nav_btn("🤖 大模型与推送", 2)
        self.btn_nav_history = self._create_nav_btn("📂 历史抓取数据", 3)
        self.btn_nav_logs = self._create_nav_btn("📜 运行日志追踪", 4)

        sb_layout.addWidget(self.btn_nav_monitor)
        sb_layout.addWidget(self.btn_nav_rules)
        sb_layout.addWidget(self.btn_nav_ai)
        sb_layout.addWidget(self.btn_nav_history)
        sb_layout.addWidget(self.btn_nav_logs)
        sb_layout.addStretch()

        version_label = QLabel("v1.0.0 (Native GUI)")
        version_label.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 12px;")
        sb_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        # 2. 右侧多页面 StackedWidget
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

        main_layout.addWidget(self.pages_stack)

    def _create_nav_btn(self, text: str, index: int, is_checked: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("class", "nav_btn")
        btn.setCheckable(True)
        btn.setChecked(is_checked)
        self.nav_group.addButton(btn, index)
        btn.clicked.connect(lambda: self.switch_page(index))
        return btn

    def switch_page(self, index: int):
        self.pages_stack.setCurrentIndex(index)
        if index == 3:
            self.tab_history.load_history()

def main():
    # 高 DPI 缩放适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
