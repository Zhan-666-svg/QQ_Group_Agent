# -*- coding: utf-8 -*-
import os
import sqlite3
import csv
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QComboBox, QAbstractItemView, QDialog,
    QFrame, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class OrderDetailDialog(QDialog):
    """发货订单与提取详情弹窗"""
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("发货订单详情与结构化数据")
        self.resize(580, 520)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        g_title = data.get("group_name") or f"群_{data.get('group_id')}"
        title = QLabel(f"📦 订单发货详情 — 来自【{g_title}】")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        layout.addWidget(title)

        # 结构化字段卡片
        info_box = QFrame()
        info_box.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px;")
        info_layout = QVBoxLayout(info_box)
        info_layout.setSpacing(8)

        entities = data.get("entities", {})
        
        info_layout.addWidget(QLabel(f"<b>抓取时间:</b> {data.get('time')}"))
        info_layout.addWidget(QLabel(f"<b>来源QQ群:</b> {g_title} (群号: {data.get('group_id')})"))
        info_layout.addWidget(QLabel(f"<b>发言人:</b> {data.get('sender_name')} (QQ: {data.get('user_id')})"))
        
        order_no = entities.get("order_id") or "无单独订单号"
        info_layout.addWidget(QLabel(f"<b>电商订单号:</b> <font color='#2080F0'><b>{order_no}</b></font>"))

        recipient = entities.get("recipient") or "未识别"
        phone = entities.get("phone") or "未识别"
        info_layout.addWidget(QLabel(f"<b>收件人:</b> {recipient} &nbsp;&nbsp;&nbsp;&nbsp; <b>联系电话:</b> <font color='#10B981'><b>{phone}</b></font>"))

        spec = entities.get("product_spec") or "无"
        remark = entities.get("remark") or "无"
        info_layout.addWidget(QLabel(f"<b>商品规格型号:</b> <font color='#D97706'><b>{spec}</b></font>"))
        if remark and remark != "无":
            info_layout.addWidget(QLabel(f"<b>发货备注:</b> <font color='#EF4444'><b>{remark}</b></font>"))

        addr = entities.get("address") or "未识别"
        info_layout.addWidget(QLabel(f"<b>收货详细地址:</b> {addr}"))

        layout.addWidget(info_box)

        # 原始消息
        raw_label = QLabel("💬 <b>群内原始消息:</b>")
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


class TabHistory(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.current_rows = []
        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 头部与过滤栏
        top_layout = QHBoxLayout()
        title = QLabel("📂 抓取数据沉淀与订单导出")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        btn_refresh = QPushButton("🔄 刷新数据")
        btn_refresh.setProperty("class", "btn_outline")
        btn_refresh.clicked.connect(self.load_history)
        top_layout.addWidget(btn_refresh)

        btn_export_excel = QPushButton("📊 导出发货 Excel (.xlsx)")
        btn_export_excel.setProperty("class", "btn_primary")
        btn_export_excel.clicked.connect(self.export_excel)
        top_layout.addWidget(btn_export_excel)

        btn_export_csv = QPushButton("📑 导出 CSV")
        btn_export_csv.setProperty("class", "btn_outline")
        btn_export_csv.clicked.connect(self.export_csv)
        top_layout.addWidget(btn_export_csv)

        btn_clear = QPushButton("🗑 清空历史")
        btn_clear.setProperty("class", "btn_danger")
        btn_clear.clicked.connect(self.clear_database)
        top_layout.addWidget(btn_clear)

        layout.addLayout(top_layout)

        # 搜索与过滤筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.input_search_kw = QLineEdit()
        self.input_search_kw.setPlaceholderText("搜索人名/手机号/商品型号/地址关键词...")
        self.input_search_kw.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.input_search_kw)

        self.input_search_group = QLineEdit()
        self.input_search_group.setPlaceholderText("按QQ群名称或群号筛选...")
        self.input_search_group.setFixedWidth(180)
        self.input_search_group.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.input_search_group)

        self.combo_urgency = QComboBox()
        self.combo_urgency.addItems(["全部分类", "订单发货", "商品咨询", "求购需求", "客诉反馈"])
        self.combo_urgency.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.combo_urgency)

        self.label_total_count = QLabel("共 0 条发货/线索记录")
        self.label_total_count.setStyleSheet("color: #64748B; font-weight: 500;")
        filter_layout.addWidget(self.label_total_count)

        layout.addLayout(filter_layout)

        # 历史记录表格：将原群号展示改成【QQ群名称】，并新增订单号、收件人、电话、商品规格、地址等列
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "抓取时间", "QQ群名称", "订单号", "商品规格型号", "收件人", "手机/虚拟号", "收件地址", "备注", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch) # 地址自适应拉伸
        self.table.setColumnWidth(0, 85)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 160)
        self.table.setColumnWidth(4, 75)
        self.table.setColumnWidth(5, 125)
        self.table.setColumnWidth(7, 75)
        self.table.setColumnWidth(8, 70)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

    def load_history(self):
        db_path = os.path.join(self.main_win.base_dir, "data", "captured_messages.db")
        if not os.path.exists(db_path):
            self.current_rows = []
            self.apply_filter()
            return

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM captured_messages ORDER BY id DESC LIMIT 500")
            rows = cursor.fetchall()
            
            parsed_rows = []
            for r in rows:
                row_dict = dict(r)
                try:
                    ent = json.loads(row_dict.get("entities") or "{}")
                except Exception:
                    ent = {}
                row_dict["parsed_entities"] = ent
                parsed_rows.append(row_dict)
            self.current_rows = parsed_rows

        self.apply_filter()

    def apply_filter(self):
        kw = self.input_search_kw.text().strip().lower()
        g_filter = self.input_search_group.text().strip().lower()
        intent_filter = self.combo_urgency.currentText()

        filtered = []
        for r in self.current_rows:
            ent = r.get("parsed_entities", {})
            raw_msg = str(r.get("raw_message", "")).lower()
            summary = str(r.get("summary", "")).lower()
            g_name = str(r.get("group_name") or r.get("group_id", "")).lower()
            g_id = str(r.get("group_id", "")).lower()

            if kw:
                ent_str = " ".join([str(v) for v in ent.values()]).lower()
                if kw not in raw_msg and kw not in summary and kw not in ent_str:
                    continue

            if g_filter:
                if g_filter not in g_name and g_filter not in g_id:
                    continue

            if intent_filter != "全部分类" and r.get("intent") != intent_filter:
                continue

            filtered.append(r)

        self.table.setRowCount(len(filtered))
        self.label_total_count.setText(f"共 {len(filtered)} 条记录")

        for row_idx, item in enumerate(filtered):
            ent = item.get("parsed_entities", {})
            
            # 时间（只显时分秒）
            t_full = str(item.get("timestamp", ""))
            t_display = t_full.split(" ")[-1] if " " in t_full else t_full
            self.table.setItem(row_idx, 0, QTableWidgetItem(t_display))
            
            # QQ群名称（优先展示群名，若无则展示群号）
            group_disp = item.get("group_name") or f"群_{item.get('group_id')}"
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(group_disp)))

            # 订单号
            order_no = ent.get("order_id", "")
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(order_no)))

            # 商品规格型号
            spec = ent.get("product_spec") or item.get("summary", "")
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(spec)))

            # 收件人
            rec = ent.get("recipient", "")
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(rec)))

            # 手机号/隐私分机号
            phone = ent.get("phone", "")
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(phone)))

            # 详细地址
            addr = ent.get("address", "")
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(addr)))

            # 备注 (如发顺丰)
            remark = ent.get("remark", "")
            rmk_item = QTableWidgetItem(str(remark))
            if "顺丰" in remark or "加急" in remark:
                rmk_item.setForeground(QColor("#EF4444"))
            self.table.setItem(row_idx, 7, rmk_item)

            # 操作按钮
            btn_view = QPushButton("详情")
            btn_view.setProperty("class", "btn_outline")
            btn_view.setFixedHeight(24)
            btn_view.clicked.connect(lambda _, it=item: self.show_detail(it))
            self.table.setCellWidget(row_idx, 8, btn_view)

    def on_row_double_clicked(self, row, col):
        btn = self.table.cellWidget(row, 8)
        if btn:
            btn.click()

    def show_detail(self, item: dict):
        dialog_data = {
            "time": item.get("timestamp"),
            "group_id": item.get("group_id"),
            "group_name": item.get("group_name") or f"群_{item.get('group_id')}",
            "user_id": item.get("user_id"),
            "sender_name": item.get("sender_name"),
            "intent": item.get("intent"),
            "urgency": item.get("urgency"),
            "summary": item.get("summary"),
            "raw_message": item.get("raw_message"),
            "entities": item.get("parsed_entities", {})
        }
        dialog = OrderDetailDialog(dialog_data, self)
        dialog.exec()

    def export_excel(self):
        if not self.current_rows:
            QMessageBox.information(self, "提示", "当前没有历史数据可导出。")
            return

        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        path, _ = QFileDialog.getSaveFileName(self, "导出发货 Excel", f"QQ群发货订单_{now_str}.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "发货订单列表"

            # 按照电商标准发货列导出
            headers = [
                "序号", "抓取时间", "QQ群名称", "QQ群号", "电商订单号", "商品规格型号",
                "收件人", "手机/虚拟分机号", "省份", "城市", "区县", "完整收件地址", "发货备注", "发言人", "发言人QQ", "原始文本"
            ]
            ws.append(headers)

            for idx, r in enumerate(self.current_rows, 1):
                ent = r.get("parsed_entities", {})
                g_name = r.get("group_name") or f"群_{r.get('group_id')}"
                ws.append([
                    idx,
                    r.get("timestamp"),
                    g_name,
                    r.get("group_id"),
                    ent.get("order_id", ""),
                    ent.get("product_spec", ""),
                    ent.get("recipient", ""),
                    ent.get("phone", ""),
                    ent.get("province", ""),
                    ent.get("city", ""),
                    ent.get("district", ""),
                    ent.get("address", ""),
                    ent.get("remark", ""),
                    r.get("sender_name", ""),
                    r.get("user_id", ""),
                    r.get("raw_message", "")
                ])

            wb.save(path)
            QMessageBox.information(self, "导出成功", f"🎉 发货订单已成功导出至:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出 Excel 出现异常: {e}")

    def export_csv(self):
        if not self.current_rows:
            QMessageBox.information(self, "提示", "当前没有历史数据可导出。")
            return

        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        path, _ = QFileDialog.getSaveFileName(self, "导出发货 CSV", f"QQ群发货订单_{now_str}.csv", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                headers = [
                    "序号", "抓取时间", "QQ群名称", "QQ群号", "电商订单号", "商品规格型号",
                    "收件人", "手机/虚拟分机号", "省份", "城市", "区县", "完整收件地址", "发货备注", "发言人", "发言人QQ", "原始文本"
                ]
                writer.writerow(headers)
                for idx, r in enumerate(self.current_rows, 1):
                    ent = r.get("parsed_entities", {})
                    g_name = r.get("group_name") or f"群_{r.get('group_id')}"
                    writer.writerow([
                        idx,
                        r.get("timestamp"),
                        g_name,
                        r.get("group_id"),
                        ent.get("order_id", ""),
                        ent.get("product_spec", ""),
                        ent.get("recipient", ""),
                        ent.get("phone", ""),
                        ent.get("province", ""),
                        ent.get("city", ""),
                        ent.get("district", ""),
                        ent.get("address", ""),
                        ent.get("remark", ""),
                        r.get("sender_name", ""),
                        r.get("user_id", ""),
                        r.get("raw_message", "")
                    ])
            QMessageBox.information(self, "导出成功", f"🎉 发货订单已成功导出至:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出 CSV 出现异常: {e}")

    def clear_database(self):
        ret = QMessageBox.question(self, "确认清空", "确定要永久清空本地所有历史抓取数据吗？该操作不可撤销！", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            db_path = os.path.join(self.main_win.base_dir, "data", "captured_messages.db")
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    conn.execute("DELETE FROM captured_messages")
                    conn.commit()
            self.load_history()
            QMessageBox.information(self, "清空完成", "本地历史记录已清空。")
