# -*- coding: utf-8 -*-
import json
import yaml
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QListWidget, QGroupBox, QMessageBox, QRadioButton,
    QButtonGroup, QSplitter, QTextEdit
)
from PySide6.QtCore import Qt

class TabRules(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title = QLabel("🎯 监听目标与过滤规则设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_save = QPushButton("💾 保存配置并即时生效")
        btn_save.setProperty("class", "btn_primary")
        btn_save.clicked.connect(self.save_settings)
        header_layout.addWidget(btn_save)
        layout.addLayout(header_layout)

        # 左右双分栏
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)

        # 左侧：群聊白名单与黑名单
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)

        # 1. 目标群聊控制
        group_box = QGroupBox("📍 监控群聊范围")
        gb_layout = QVBoxLayout(group_box)
        gb_layout.setSpacing(8)

        radio_layout = QHBoxLayout()
        self.radio_all = QRadioButton("监听小号所在的所有群聊")
        self.radio_whitelist = QRadioButton("仅监听以下白名单指定的群聊")
        self.bg_group = QButtonGroup()
        self.bg_group.addButton(self.radio_all)
        self.bg_group.addButton(self.radio_whitelist)
        self.radio_all.toggled.connect(self.on_mode_toggled)
        radio_layout.addWidget(self.radio_all)
        radio_layout.addWidget(self.radio_whitelist)
        gb_layout.addLayout(radio_layout)

        # 群号输入与列表
        add_g_layout = QHBoxLayout()
        self.input_group_id = QLineEdit()
        self.input_group_id.setPlaceholderText("输入要接入监控的 QQ 群号 (如 123456789)")
        btn_add_group = QPushButton("添加群号")
        btn_add_group.setProperty("class", "btn_outline")
        btn_add_group.clicked.connect(self.add_group)
        add_g_layout.addWidget(self.input_group_id)
        add_g_layout.addWidget(btn_add_group)
        gb_layout.addLayout(add_g_layout)

        self.list_groups = QListWidget()
        self.list_groups.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        gb_layout.addWidget(self.list_groups)

        btn_del_g_layout = QHBoxLayout()
        btn_del_group = QPushButton("删除选中群号")
        btn_del_group.setProperty("class", "btn_outline")
        btn_del_group.clicked.connect(self.remove_group)
        btn_clear_group = QPushButton("清空列表")
        btn_clear_group.setProperty("class", "btn_outline")
        btn_clear_group.clicked.connect(lambda: self.list_groups.clear())
        btn_del_g_layout.addWidget(btn_del_group)
        btn_del_g_layout.addWidget(btn_clear_group)
        gb_layout.addLayout(btn_del_g_layout)
        left_layout.addWidget(group_box)

        # 2. 发言人黑名单 (过滤管理员或机器人自己)
        ignore_box = QGroupBox("🚫 发言人黑名单 (跳过其发言)")
        ib_layout = QVBoxLayout(ignore_box)
        ib_layout.setSpacing(8)

        add_u_layout = QHBoxLayout()
        self.input_user_id = QLineEdit()
        self.input_user_id.setPlaceholderText("输入忽略的 QQ 号 (如机器人小号自身)")
        btn_add_user = QPushButton("添加QQ")
        btn_add_user.setProperty("class", "btn_outline")
        btn_add_user.clicked.connect(self.add_ignore_user)
        add_u_layout.addWidget(self.input_user_id)
        add_u_layout.addWidget(btn_add_user)
        ib_layout.addLayout(add_u_layout)

        self.list_ignore_users = QListWidget()
        self.list_ignore_users.setFixedHeight(110)
        self.list_ignore_users.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px;")
        ib_layout.addWidget(self.list_ignore_users)

        btn_del_user = QPushButton("删除选中QQ")
        btn_del_user.setProperty("class", "btn_outline")
        btn_del_user.clicked.connect(self.remove_ignore_user)
        ib_layout.addWidget(btn_del_user, alignment=Qt.AlignRight)
        left_layout.addWidget(ignore_box)

        splitter.addWidget(left_widget)

        # 右侧：L1 快速关键词与正则
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(12)

        kw_box = QGroupBox("🔍 L1 触发关键词 (包含其一即触发抓取/研判，换行分隔)")
        kw_layout = QVBoxLayout(kw_box)
        self.text_include_kws = QTextEdit()
        self.text_include_kws.setPlaceholderText("例如：\n求购\n报价\n现货\n多少钱\n需要")
        kw_layout.addWidget(self.text_include_kws)
        
        tpl_layout = QHBoxLayout()
        btn_tpl_biz = QPushButton("载入标准商机/求购模板")
        btn_tpl_biz.setProperty("class", "btn_outline")
        btn_tpl_biz.clicked.connect(self.load_biz_template)
        btn_tpl_service = QPushButton("载入售后客诉模板")
        btn_tpl_service.setProperty("class", "btn_outline")
        btn_tpl_service.clicked.connect(self.load_service_template)
        tpl_layout.addWidget(btn_tpl_biz)
        tpl_layout.addWidget(btn_tpl_service)
        kw_layout.addLayout(tpl_layout)
        right_layout.addWidget(kw_box)

        ex_box = QGroupBox("⛔ 排除关键词 (命中直接丢弃，过滤打卡水群，换行分隔)")
        ex_layout = QVBoxLayout(ex_box)
        self.text_exclude_kws = QTextEdit()
        self.text_exclude_kws.setFixedHeight(100)
        self.text_exclude_kws.setPlaceholderText("例如：\n签到\n打卡\n欢迎新成员")
        ex_layout.addWidget(self.text_exclude_kws)
        right_layout.addWidget(ex_box)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

    def on_mode_toggled(self):
        is_wl = self.radio_whitelist.isChecked()
        self.input_group_id.setEnabled(is_wl)
        self.list_groups.setEnabled(is_wl)

    def add_group(self):
        val = self.input_group_id.text().strip()
        if not val:
            return
        if not val.isdigit():
            QMessageBox.warning(self, "输入错误", "QQ 群号必须为纯数字！")
            return
        # 查重
        for i in range(self.list_groups.count()):
            if self.list_groups.item(i).text() == val:
                QMessageBox.information(self, "提示", "该群号已经在白名单中了。")
                return
        self.list_groups.addItem(val)
        self.input_group_id.clear()

    def remove_group(self):
        row = self.list_groups.currentRow()
        if row >= 0:
            self.list_groups.takeItem(row)

    def add_ignore_user(self):
        val = self.input_user_id.text().strip()
        if not val:
            return
        if not val.isdigit():
            QMessageBox.warning(self, "输入错误", "QQ 号必须为纯数字！")
            return
        for i in range(self.list_ignore_users.count()):
            if self.list_ignore_users.item(i).text() == val:
                return
        self.list_ignore_users.addItem(val)
        self.input_user_id.clear()

    def remove_ignore_user(self):
        row = self.list_ignore_users.currentRow()
        if row >= 0:
            self.list_ignore_users.takeItem(row)

    def load_biz_template(self):
        keywords = ["求购", "收购", "想买", "收一个", "收台", "需要", "寻找", "报价", "多少钱", "预算", "现货", "货源", "批发", "代理", "合作", "对接", "微信", "联系方式"]
        self.text_include_kws.setPlainText("\n".join(keywords))

    def load_service_template(self):
        keywords = ["报错", "故障", "卡顿", "打不开", "客诉", "售后", "投诉", "退款", "人工客服", "退单", "漏发", "损坏"]
        self.text_include_kws.setPlainText("\n".join(keywords))

    def load_current_settings(self):
        cfg = self.main_win.config
        tg = cfg.get("monitoring", {}).get("target_groups", [])
        if tg:
            self.radio_whitelist.setChecked(True)
            self.list_groups.clear()
            for g in tg:
                self.list_groups.addItem(str(g))
        else:
            self.radio_all.setChecked(True)
            self.list_groups.clear()
        self.on_mode_toggled()

        iu = cfg.get("monitoring", {}).get("ignore_users", [])
        self.list_ignore_users.clear()
        for u in iu:
            self.list_ignore_users.addItem(str(u))

        # 读取 rules.json
        rules = self.main_win.rules_dict.get("rules", {})
        inc = rules.get("include_keywords", [])
        self.text_include_kws.setPlainText("\n".join(inc))
        exc = rules.get("exclude_keywords", [])
        self.text_exclude_kws.setPlainText("\n".join(exc))

    def save_settings(self):
        # 1. 整理 target_groups
        if self.radio_whitelist.isChecked():
            tg = []
            for i in range(self.list_groups.count()):
                t = self.list_groups.item(i).text().strip()
                if t.isdigit():
                    tg.append(int(t))
        else:
            tg = []

        # 2. 整理 ignore_users
        iu = []
        for i in range(self.list_ignore_users.count()):
            t = self.list_ignore_users.item(i).text().strip()
            if t.isdigit():
                iu.append(int(t))

        self.main_win.config.setdefault("monitoring", {})
        self.main_win.config["monitoring"]["target_groups"] = tg
        self.main_win.config["monitoring"]["ignore_users"] = iu

        # 写回 config.yaml
        try:
            with open(self.main_win.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.main_win.config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法写入 config.yaml: {e}")
            return

        # 3. 整理 rules.json
        inc_raw = self.text_include_kws.toPlainText().strip().split("\n")
        inc = [k.strip() for k in inc_raw if k.strip()]

        exc_raw = self.text_exclude_kws.toPlainText().strip().split("\n")
        exc = [k.strip() for k in exc_raw if k.strip()]

        self.main_win.rules_dict.setdefault("rules", {})
        self.main_win.rules_dict["rules"]["include_keywords"] = inc
        self.main_win.rules_dict["rules"]["exclude_keywords"] = exc

        try:
            with open(self.main_win.rules_path, "w", encoding="utf-8") as f:
                json.dump(self.main_win.rules_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法写入 rules.json: {e}")
            return

        # 重载引擎
        self.main_win.reload_engines()
        self.main_win.tab_monitor.refresh_stats()
        self.main_win.tab_logs.append_log(f"[设置] 监听群聊与过滤规则已更新保存并即刻生效 (监控群数: {len(tg) if tg else '全部'})。")
        QMessageBox.information(self, "保存成功", "监听群聊与过滤规则已成功保存并即刻生效！")
