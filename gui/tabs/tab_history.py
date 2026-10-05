# -*- coding: utf-8 -*-
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QLineEdit, QDialog, QTextEdit, QApplication
)
from PySide6.QtCore import Qt

class OrderDetailDialog(QDialog):
    """现代化电商订单详情卡片"""
    def __init__(self, row_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("发货订单与解析要素详情")
        self.resize(600, 520)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        g_name = row_data.get("group_name") or f"群_{row_data.get('group_id')}"
        title = QLabel(f"📦 电商订单 —【{g_name}】")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F172A;")
        layout.addWidget(title)

        info_box = QFrame()
        info_box.setProperty("class", "card_subtle")
        info_layout = QVBoxLayout(info_box)
        info_layout.setSpacing(8)

        info_layout.addWidget(QLabel(f"<b>抓取时间:</b> {row_data.get('captured_at')} &nbsp;&nbsp;&nbsp;&nbsp; <b>来源群聊:</b> {g_name} ({row_data.get('group_id')})"))
        info_layout.addWidget(QLabel(f"<b>发言人:</b> {row_data.get('sender_name')} (QQ: {row_data.get('user_id')})"))
        info_layout.addWidget(QLabel(f"<b>电商订单号:</b> <font color='#2563EB'><b>{row_data.get('order_id') or '未提取到'}</b></font>"))
        info_layout.addWidget(QLabel(f"<b>商品规格型号:</b> <font color='#0F172A'><b>{row_data.get('product_model') or '未提取到'}</b></font>"))
        info_layout.addWidget(QLabel(f"<b>收货人:</b> {row_data.get('recipient_name') or '未提取到'} &nbsp;&nbsp;&nbsp;&nbsp; <b>联系电话:</b> <font color='#10B981'><b>{row_data.get('phone') or '未提取到'}</b></font>"))
        info_layout.addWidget(QLabel(f"<b>收件详细地址:</b> {row_data.get('address') or '未提取到'}"))
        if row_data.get("remark"):
            info_layout.addWidget(QLabel(f"<b>发货特别备注:</b> <font color='#EF4444'><b>{row_data.get('remark')}</b></font>"))

        layout.addWidget(info_box)

        # 原始消息
        raw_label = QLabel("💬 <b>群聊原始文本:</b>")
        layout.addWidget(raw_label)
        raw_edit = QTextEdit()
        raw_edit.setPlainText(row_data.get("raw_message", ""))
        raw_edit.setReadOnly(True)
        raw_edit.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(raw_edit)

        # 底部操作栏
        btn_layout = QHBoxLayout()
        btn_copy = QPushButton("📋 复制原始文本")
        btn_copy.setProperty("class", "btn_outline")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(row_data.get("raw_message", "")))

        close_btn = QPushButton("关闭")
        close_btn.setProperty("class", "btn_primary")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(btn_copy)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class TabHistory(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.db_path = os.path.join(self.main_win.base_dir, "data", "messages.db")
        self.all_data = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. 顶部检索与过滤卡片
        filter_card = QFrame()
        filter_card.setProperty("class", "card")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(16, 12, 16, 12)
        f_layout.setSpacing(10)

        f_label = QLabel("🔍 智能检索:")
        f_label.setStyleSheet("font-weight: 700; color: #0F172A;")
        f_layout.addWidget(f_label)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("可输入：单号、收件人、手机/虚拟号、规格型号、群名或收件地址实时过滤...")
        self.input_search.textChanged.connect(self._apply_filter)
        f_layout.addWidget(self.input_search, stretch=1)

        self.btn_search_clear = QPushButton("清空筛选")
        self.btn_search_clear.setProperty("class", "btn_outline")
        self.btn_search_clear.setCursor(Qt.PointingHandCursor)
        self.btn_search_clear.clicked.connect(lambda: self.input_search.clear())
        f_layout.addWidget(self.btn_search_clear)

        self.lbl_stats = QLabel("共计: 0 条")
        self.lbl_stats.setStyleSheet("color: #64748B; font-weight: 600; padding: 0 8px;")
        f_layout.addWidget(self.lbl_stats)

        layout.addWidget(filter_card)

        # 2. 表格与操作卡片
        tbl_card = QFrame()
        tbl_card.setProperty("class", "card")
        tbl_card_layout = QVBoxLayout(tbl_card)
        tbl_card_layout.setContentsMargins(14, 14, 14, 14)
        tbl_card_layout.setSpacing(12)

        # 顶部操作栏
        toolbar = QHBoxLayout()
        self.btn_export = QPushButton("📊 导出发货 Excel (.xlsx)")
        self.btn_export.setProperty("class", "btn_primary")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.clicked.connect(self._export_to_excel)

        self.btn_refresh = QPushButton("🔄 刷新数据")
        self.btn_refresh.setProperty("class", "btn_outline")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_history)

        self.btn_clear = QPushButton("🗑 清空历史")
        self.btn_clear.setProperty("class", "btn_danger")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._clear_history)

        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_clear)
        tbl_card_layout.addLayout(toolbar)

        # 结构化发货数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "抓取时间", "QQ群名称", "订单号", "商品规格型号",
            "收件人", "手机/虚拟号", "收件地址", "备注", "操作"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False) # 杜绝折行卡顿
        self.table.verticalHeader().setDefaultSectionSize(40)

        h = self.table.horizontalHeader()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents) # 时间
        h.setSectionResizeMode(1, QHeaderView.Interactive)      # 群名称
        h.setSectionResizeMode(2, QHeaderView.Interactive)      # 订单号
        h.setSectionResizeMode(3, QHeaderView.Stretch)          # 商品规格型号
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents) # 姓名
        h.setSectionResizeMode(5, QHeaderView.Interactive)      # 电话
        h.setSectionResizeMode(6, QHeaderView.Stretch)          # 地址
        h.setSectionResizeMode(7, QHeaderView.Interactive)      # 备注
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents) # 操作

        self.table.setColumnWidth(1, 135)
        self.table.setColumnWidth(2, 175)
        self.table.setColumnWidth(5, 155)
        self.table.setColumnWidth(7, 90)

        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        tbl_card_layout.addWidget(self.table)
        layout.addWidget(tbl_card)

    def load_history(self):
        """从 SQLite 读取所有已抓取消息"""
        if not os.path.exists(self.db_path):
            self.table.setRowCount(0)
            self.lbl_stats.setText("共计: 0 条")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, captured_at, group_id, group_name, user_id, sender_name, 
                       intent, urgency, summary, entities_json, raw_message 
                FROM captured_messages 
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            conn.close()
            return
        conn.close()

        self.all_data = []
        for r in rows:
            ent = {}
            if r[9]:
                try:
                    ent = json.loads(r[9])
                except Exception:
                    pass

            item = {
                "id": r[0],
                "captured_at": r[1],
                "group_id": r[2],
                "group_name": r[3] or f"群_{r[2]}",
                "user_id": r[4],
                "sender_name": r[5],
                "intent": r[6],
                "urgency": r[7],
                "summary": r[8],
                "order_id": ent.get("订单号") or ent.get("order_id", ""),
                "recipient_name": ent.get("姓名") or ent.get("收件人") or ent.get("recipient", ""),
                "phone": ent.get("手机号") or ent.get("联系方式") or ent.get("phone", ""),
                "address": ent.get("收货地址") or ent.get("地址") or ent.get("address", ""),
                "product_model": ent.get("商品规格") or ent.get("规格型号") or ent.get("product_model", ""),
                "remark": ent.get("发货备注") or ent.get("备注") or ent.get("remark", ""),
                "raw_message": r[10]
            }
            self.all_data.append(item)

        self._render_table(self.all_data)

    def _apply_filter(self):
        kw = self.input_search.text().strip().lower()
        if not kw:
            self._render_table(self.all_data)
            return

        filtered = []
        for d in self.all_data:
            match_str = f"{d['group_name']} {d['order_id']} {d['recipient_name']} {d['phone']} {d['address']} {d['product_model']} {d['remark']} {d['raw_message']}".lower()
            if kw in match_str:
                filtered.append(d)
        self._render_table(filtered)

    def _render_table(self, data_list):
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(data_list))
            for row, d in enumerate(data_list):
                self.table.setItem(row, 0, QTableWidgetItem(str(d["captured_at"])))
                self.table.setItem(row, 1, QTableWidgetItem(str(d["group_name"])))
                self.table.setItem(row, 2, QTableWidgetItem(str(d["order_id"])))
                self.table.setItem(row, 3, QTableWidgetItem(str(d["product_model"])))
                self.table.setItem(row, 4, QTableWidgetItem(str(d["recipient_name"])))
                self.table.setItem(row, 5, QTableWidgetItem(str(d["phone"])))
                self.table.setItem(row, 6, QTableWidgetItem(str(d["address"])))
                self.table.setItem(row, 7, QTableWidgetItem(str(d["remark"])))

                btn = QPushButton("查看详情")
                btn.setProperty("class", "btn_outline")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedHeight(26)
                btn.clicked.connect(lambda _, row_dict=d: self._show_detail(row_dict))
                self.table.setCellWidget(row, 8, btn)

            self.lbl_stats.setText(f"共计: {len(data_list)} 条记录")
        finally:
            self.table.setUpdatesEnabled(True)

    def _on_row_double_clicked(self, row, col):
        btn = self.table.cellWidget(row, 8)
        if btn:
            btn.click()

    def _show_detail(self, row_dict):
        dialog = OrderDetailDialog(row_dict, self)
        dialog.exec()

    def _export_to_excel(self):
        if not self.all_data:
            QMessageBox.warning(self, "提示", "当前历史数据为空，无法导出！")
            return

        default_name = f"QQ群发货订单导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出发货 Excel", default_name, "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        export_rows = []
        for d in self.all_data:
            export_rows.append({
                "抓取时间": d["captured_at"],
                "QQ群名称": d["group_name"],
                "QQ群号": d["group_id"],
                "发送人": d["sender_name"],
                "电商订单号": d["order_id"],
                "商品规格型号": d["product_model"],
                "收件人姓名": d["recipient_name"],
                "收件人电话": d["phone"],
                "详细收件地址": d["address"],
                "发货备注": d["remark"],
                "原始发言内容": d["raw_message"]
            })

        df = pd.DataFrame(export_rows)
        try:
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
            else:
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="抓取发货清单")
            QMessageBox.information(self, "导出成功", f"成功导出 {len(export_rows)} 条数据至：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"写入文件时发生错误: {e}")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空", "确定要彻底清空本地数据库中的所有抓取历史吗？\n此操作不可逆！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM captured_messages")
                conn.commit()
                conn.close()
            self.load_history()
