# -*- coding: utf-8 -*-
import os
import json
import webbrowser
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QTextEdit,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

class ListenerWorker(QThread):
    """后台 WebSocket 监听线程"""
    message_received = Signal(dict)
    log_signal = Signal(str)
    status_signal = Signal(str, bool) # (type, is_running)

    def __init__(self, config_getter, rules_getter, agent_getter, notifier_getter):
        super().__init__()
        self.config_getter = config_getter
        self.rules_getter = rules_getter
        self.agent_getter = agent_getter
        self.notifier_getter = notifier_getter
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        import asyncio
        import websockets

        async def inner_loop():
            self.status_signal.emit("listener", True)
            self.log_signal.emit("[智能体] 监听服务工作线程已启动。")

            while self._is_running:
                config = self.config_getter()
                rules = self.rules_getter()
                agent = self.agent_getter()
                notifier = self.notifier_getter()

                ws_url = config.get("onebot", {}).get("ws_url", "ws://127.0.0.1:3001")
                token = config.get("onebot", {}).get("access_token", "")
                reconnect_sec = config.get("onebot", {}).get("reconnect_interval_sec", 5)

                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                try:
                    self.log_signal.emit(f"[*] 正在连接 NapCat 网关: {ws_url} ...")
                    async with websockets.connect(
                        ws_url,
                        additional_headers=headers if headers else None,
                        ping_interval=30,
                        ping_timeout=10
                    ) as ws:
                        self.status_signal.emit("gateway", True)
                        self.log_signal.emit("[✔] 成功连接 NapCat OneBot 网关，开始实时监控群聊...")

                        while self._is_running:
                            try:
                                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                                event = json.loads(msg)
                                
                                if event.get("post_type") == "message" and event.get("message_type") == "group":
                                    group_id = event.get("group_id", 0)
                                    user_id = event.get("user_id", 0)
                                    sender = event.get("sender", {})
                                    sender_name = sender.get("card") or sender.get("nickname") or f"用户_{user_id}"
                                    raw_text = event.get("raw_message", "")

                                    should_analyze, reason = rules.should_analyze(group_id, user_id, raw_text)
                                    if should_analyze:
                                        # 解析 QQ 群名称
                                        http_url = config.get("onebot", {}).get("http_url", "http://127.0.0.1:3000")
                                        try:
                                            from src.group_service import get_group_name
                                        except ImportError:
                                            from group_service import get_group_name
                                        g_name = get_group_name(group_id, http_url, token)

                                        self.log_signal.emit(f"[*] 命中粗筛 [{reason}] 来自【{g_name}】的 {sender_name}")
                                        analysis = await agent.analyze(sender_name, group_id, raw_text, reason)
                                        
                                        if analysis.get("is_target", True):
                                            item_data = {
                                                "time": datetime.now().strftime("%H:%M:%S"),
                                                "group_id": group_id,
                                                "group_name": g_name,
                                                "user_id": user_id,
                                                "sender_name": sender_name,
                                                "raw_message": raw_text,
                                                "intent": analysis.get("intent", "目标消息"),
                                                "urgency": analysis.get("urgency", "中"),
                                                "summary": analysis.get("summary", raw_text[:60]),
                                                "entities": analysis.get("entities", {})
                                            }
                                            self.message_received.emit(item_data)
                                            # 执行存储与通知
                                            await notifier.notify(
                                                group_id=group_id,
                                                user_id=user_id,
                                                sender_name=sender_name,
                                                group_name=g_name,
                                                raw_message=raw_text,
                                                analysis=analysis
                                            )
                            except asyncio.TimeoutError:
                                continue
                            except Exception as parse_e:
                                if self._is_running:
                                    self.log_signal.emit(f"[!] 处理消息异常: {parse_e}")
                except Exception as net_e:
                    self.status_signal.emit("gateway", False)
                    if self._is_running:
                        self.log_signal.emit(f"[!] 网关未启动或已断开 ({net_e})，{reconnect_sec} 秒后重试...")
                        await asyncio.sleep(reconnect_sec)

            self.status_signal.emit("listener", False)
            self.status_signal.emit("gateway", False)
            self.log_signal.emit("[*] 智能体监听服务已安全停止。")

        asyncio.run(inner_loop())


class MessageDetailDialog(QDialog):
    """消息详情弹窗"""
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("群消息详情与AI解析")
        self.resize(550, 480)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        g_disp = data.get("group_name") or f"群_{data.get('group_id')}"
        title = QLabel(f"🎯 消息线索详情 — 来自【{g_disp}】({data.get('group_id')}) · {data.get('sender_name')}")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        layout.addWidget(title)

        info_box = QFrame()
        info_box.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px;")
        info_layout = QVBoxLayout(info_box)
        info_layout.setSpacing(6)
        info_layout.addWidget(QLabel(f"<b>抓取时间:</b> {data.get('time')}"))
        info_layout.addWidget(QLabel(f"<b>发信账号:</b> {data.get('sender_name')} (QQ: {data.get('user_id')})"))
        info_layout.addWidget(QLabel(f"<b>意图类型:</b> {data.get('intent')} | <b>紧迫度:</b> {data.get('urgency')}"))
        info_layout.addWidget(QLabel(f"<b>核心摘要:</b> {data.get('summary')}"))
        layout.addWidget(info_box)

        # 关键要素
        entities = data.get("entities", {})
        if entities:
            ent_label = QLabel("📦 <b>结构化提取要素:</b>")
            layout.addWidget(ent_label)
            ent_box = QFrame()
            ent_box.setStyleSheet("background-color: #F1F5F9; border-radius: 6px; padding: 8px;")
            ent_layout = QVBoxLayout(ent_box)
            for k, v in entities.items():
                if v:
                    ent_layout.addWidget(QLabel(f"• <b>{k}</b>: {v}"))
            layout.addWidget(ent_box)

        # 原始消息
        raw_label = QLabel("💬 <b>原始聊天消息:</b>")
        layout.addWidget(raw_label)
        raw_edit = QTextEdit()
        raw_edit.setPlainText(data.get("raw_message", ""))
        raw_edit.setReadOnly(True)
        raw_edit.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px;")
        layout.addWidget(raw_edit)

        close_btn = QPushButton("关闭")
        close_btn.setProperty("class", "btn_primary")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)


class TabMonitor(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.napcat_process = None
        self.listener_worker = None

        self.captured_count = 0
        self.today_received_count = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. 顶部指标卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.card_captured = self._create_stat_card("今日抓取线索", "0 条", "#2080F0")
        self.card_groups = self._create_stat_card("指定监听群数", "0 个", "#10B981")
        self.card_gateway = self._create_stat_card("QQ 网关状态", "未连接", "#EF4444")
        self.card_agent = self._create_stat_card("AI 研判模式", "纯规则模式", "#64748B")

        stats_layout.addWidget(self.card_captured)
        stats_layout.addWidget(self.card_groups)
        stats_layout.addWidget(self.card_gateway)
        stats_layout.addWidget(self.card_agent)
        layout.addLayout(stats_layout)

        # 2. 控制操作栏
        control_frame = QFrame()
        control_frame.setProperty("class", "card")
        ctrl_layout = QHBoxLayout(control_frame)
        ctrl_layout.setContentsMargins(14, 10, 14, 10)
        ctrl_layout.setSpacing(12)

        self.btn_toggle_listener = QPushButton("▶ 启动智能体监听")
        self.btn_toggle_listener.setProperty("class", "btn_primary")
        self.btn_toggle_listener.clicked.connect(self.toggle_listener)

        self.btn_toggle_napcat = QPushButton("⚡ 启动 NapCat 网关")
        self.btn_toggle_napcat.setProperty("class", "btn_outline")
        self.btn_toggle_napcat.clicked.connect(self.toggle_napcat)

        self.btn_open_webui = QPushButton("🌐 打开扫码登录控制台")
        self.btn_open_webui.setProperty("class", "btn_outline")
        self.btn_open_webui.clicked.connect(self.open_webui)

        self.btn_clear_table = QPushButton("清空看板列表")
        self.btn_clear_table.setProperty("class", "btn_outline")
        self.btn_clear_table.clicked.connect(self.clear_table)

        ctrl_layout.addWidget(self.btn_toggle_listener)
        ctrl_layout.addWidget(self.btn_toggle_napcat)
        ctrl_layout.addWidget(self.btn_open_webui)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_clear_table)
        layout.addWidget(control_frame)

        # 3. 实时消息流表格
        table_label = QLabel("📋 实时群消息抓取与意图研判流")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["时间", "QQ群名称", "发言人", "意图分类", "紧迫度", "智能核心摘要", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 85)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(6, 75)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        self.refresh_stats()

    def _create_stat_card(self, title: str, value: str, val_color: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 12, 14, 12)
        l.setSpacing(4)
        t_label = QLabel(title)
        t_label.setProperty("class", "stat_title")
        v_label = QLabel(value)
        v_label.setProperty("class", "stat_value")
        v_label.setStyleSheet(f"color: {val_color};")
        l.addWidget(t_label)
        l.addWidget(v_label)
        card.value_label = v_label
        return card

    def refresh_stats(self):
        cfg = self.main_win.config
        tg = cfg.get("monitoring", {}).get("target_groups", [])
        if tg:
            self.card_groups.value_label.setText(f"{len(tg)} 个群")
            self.card_groups.value_label.setStyleSheet("color: #10B981;")
        else:
            self.card_groups.value_label.setText("全部群聊")
            self.card_groups.value_label.setStyleSheet("color: #64748B;")

        api_key = cfg.get("agent", {}).get("api_key", "").strip()
        if api_key:
            self.card_agent.value_label.setText("凭证有效")
            self.card_agent.value_label.setStyleSheet("color: #10B981;")
        else:
            self.card_agent.value_label.setText("纯规则模式")
            self.card_agent.value_label.setStyleSheet("color: #64748B;")

    def toggle_listener(self):
        if self.listener_worker and self.listener_worker.isRunning():
            self.listener_worker.stop()
            self.listener_worker.wait(2000)
            self.btn_toggle_listener.setText("▶ 启动智能体监听")
            self.btn_toggle_listener.setProperty("class", "btn_primary")
            self.btn_toggle_listener.style().unpolish(self.btn_toggle_listener)
            self.btn_toggle_listener.style().polish(self.btn_toggle_listener)
            self.card_gateway.value_label.setText("未连接")
            self.card_gateway.value_label.setStyleSheet("color: #EF4444;")
        else:
            self.listener_worker = ListenerWorker(
                config_getter=lambda: self.main_win.config,
                rules_getter=lambda: self.main_win.rules_engine,
                agent_getter=lambda: self.main_win.agent_engine,
                notifier_getter=lambda: self.main_win.notifier
            )
            self.listener_worker.message_received.connect(self.on_message_captured)
            self.listener_worker.log_signal.connect(self.main_win.tab_logs.append_log)
            self.listener_worker.status_signal.connect(self.on_status_changed)
            self.listener_worker.start()

            self.btn_toggle_listener.setText("⏹ 停止智能体监听")
            self.btn_toggle_listener.setProperty("class", "btn_danger")
            self.btn_toggle_listener.style().unpolish(self.btn_toggle_listener)
            self.btn_toggle_listener.style().polish(self.btn_toggle_listener)

    def on_status_changed(self, component: str, is_active: bool):
        if component == "gateway":
            if is_active:
                self.card_gateway.value_label.setText("状态正常")
                self.card_gateway.value_label.setStyleSheet("color: #10B981;")
            else:
                self.card_gateway.value_label.setText("未连接")
                self.card_gateway.value_label.setStyleSheet("color: #EF4444;")

    def on_message_captured(self, item: dict):
        self.captured_count += 1
        self.card_captured.value_label.setText(f"{self.captured_count} 条")

        row = 0
        self.table.insertRow(row)

        g_disp = item.get("group_name") or f"群_{item.get('group_id')}"
        self.table.setItem(row, 0, QTableWidgetItem(item.get("time", "")))
        self.table.setItem(row, 1, QTableWidgetItem(str(g_disp)))
        self.table.setItem(row, 2, QTableWidgetItem(str(item.get("sender_name"))))
        
        intent_item = QTableWidgetItem(str(item.get("intent")))
        self.table.setItem(row, 3, intent_item)

        urgency_item = QTableWidgetItem(str(item.get("urgency")))
        if item.get("urgency") == "高":
            urgency_item.setForeground(QColor("#EF4444"))
        elif item.get("urgency") == "中":
            urgency_item.setForeground(QColor("#D97706"))
        else:
            urgency_item.setForeground(QColor("#059669"))
        self.table.setItem(row, 4, urgency_item)

        summary_item = QTableWidgetItem(str(item.get("summary")))
        self.table.setItem(row, 5, summary_item)

        btn_detail = QPushButton("查看")
        btn_detail.setProperty("class", "btn_outline")
        btn_detail.setFixedHeight(26)
        btn_detail.clicked.connect(lambda _, d=item: self.show_detail(d))
        self.table.setCellWidget(row, 6, btn_detail)

    def on_row_double_clicked(self, row, col):
        btn = self.table.cellWidget(row, 6)
        if btn:
            btn.click()

    def show_detail(self, data: dict):
        dialog = MessageDetailDialog(data, self)
        dialog.exec()

    def clear_table(self):
        self.table.setRowCount(0)

    def toggle_napcat(self):
        bat_path = os.path.join(self.main_win.base_dir, "scripts", "start_napcat.bat")
        if not os.path.exists(bat_path):
            QMessageBox.critical(self, "错误", f"找不到启动脚本: {bat_path}")
            return

        try:
            # 独立窗口运行
            subprocess.Popen(f'start "" "{bat_path}"', shell=True)
            self.main_win.tab_logs.append_log("[NapCat] 已调起 NapCat 网关终端窗口。")
            QMessageBox.information(self, "提示", "已启动 NapCat 网关终端窗口！\n如尚未登录小号，请在弹出的黑色窗口中扫码，或点击【打开扫码登录控制台】。")
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"无法调起进程: {e}")

    def open_webui(self):
        webbrowser.open("http://127.0.0.1:6099/webui")
        self.main_win.tab_logs.append_log("[WebUI] 正在打开浏览器访问 http://127.0.0.1:6099/webui (预设密码: admin123)")
