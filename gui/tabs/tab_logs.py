# -*- coding: utf-8 -*-
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit
)

class TabLogs(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        title = QLabel("📜 系统运行日志与事件追踪")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        btn_clear = QPushButton("清空日志")
        btn_clear.setProperty("class", "btn_outline")
        btn_clear.clicked.connect(self.clear_logs)
        top_layout.addWidget(btn_clear)

        layout.addLayout(top_layout)

        self.text_logs = QPlainTextEdit()
        self.text_logs.setReadOnly(True)
        self.text_logs.setStyleSheet("""
            background-color: #0F172A;
            color: #E2E8F0;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            border-radius: 6px;
            padding: 10px;
        """)
        layout.addWidget(self.text_logs)

        self.append_log("[系统] QQ 群消息智能体客户端控制台初始化完毕。")

    def append_log(self, text: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        line = f"[{now_str}] {text}"
        self.text_logs.appendPlainText(line)

    def clear_logs(self):
        self.text_logs.clear()
