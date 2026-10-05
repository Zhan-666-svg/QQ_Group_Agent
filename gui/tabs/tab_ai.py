# -*- coding: utf-8 -*-
import yaml
import asyncio
import httpx
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QGroupBox, QMessageBox, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt

class TabAI(QWidget):
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
        title = QLabel("🤖 大模型智能体与多通道推送设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_save = QPushButton("💾 保存配置并即时生效")
        btn_save.setProperty("class", "btn_primary")
        btn_save.clicked.connect(self.save_settings)
        header_layout.addWidget(btn_save)
        layout.addLayout(header_layout)

        # 1. 大模型研判设置
        ai_box = QGroupBox("🧠 智能体大模型引擎 (用于语义研判与关键信息提取)")
        ai_layout = QVBoxLayout(ai_box)
        ai_layout.setSpacing(10)

        # 预设模型快速填充
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("常用服务商预设:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItems([
            "DeepSeek (官方 API)",
            "阿里通义千问 (DashScope)",
            "OpenAI (ChatGPT)",
            "自定义 OpenAI-Compatible 接口"
        ])
        self.combo_presets.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.combo_presets)
        preset_layout.addStretch()
        ai_layout.addLayout(preset_layout)

        # Base URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("接口地址 (Base URL):"))
        self.input_base_url = QLineEdit()
        self.input_base_url.setPlaceholderText("https://api.deepseek.com/v1")
        url_layout.addWidget(self.input_base_url)
        ai_layout.addLayout(url_layout)

        # API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key (密钥凭证):"))
        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.Password)
        self.input_api_key.setPlaceholderText("sk-xxxxxxxxxxxxxxxxxxxxxxxx")
        
        self.check_show_key = QCheckBox("显示明文")
        self.check_show_key.toggled.connect(lambda v: self.input_api_key.setEchoMode(QLineEdit.Normal if v else QLineEdit.Password))
        
        btn_test_ai = QPushButton("🔍 测试大模型连通性")
        btn_test_ai.setProperty("class", "btn_outline")
        btn_test_ai.clicked.connect(self.test_ai_connection)

        key_layout.addWidget(self.input_api_key)
        key_layout.addWidget(self.check_show_key)
        key_layout.addWidget(btn_test_ai)
        ai_layout.addLayout(key_layout)

        # 模型名称
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型名称 (Model):"))
        self.input_model = QLineEdit()
        self.input_model.setPlaceholderText("deepseek-chat")
        model_layout.addWidget(self.input_model)
        
        self.label_ai_status = QLabel("状态: 待检测")
        self.label_ai_status.setStyleSheet("color: #64748B; font-weight: bold; margin-left: 10px;")
        model_layout.addWidget(self.label_ai_status)
        model_layout.addStretch()
        ai_layout.addLayout(model_layout)

        layout.addWidget(ai_box)

        # 2. 外部通知推送渠道
        noti_box = QGroupBox("📢 抓取命中后外部推送通知渠道 (任选其一或多选)")
        noti_layout = QVBoxLayout(noti_box)
        noti_layout.setSpacing(10)

        # 飞书 Webhook
        fs_layout = QHBoxLayout()
        fs_layout.addWidget(QLabel("飞书群机器人 Webhook:"))
        self.input_feishu = QLineEdit()
        self.input_feishu.setPlaceholderText("https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx")
        fs_layout.addWidget(self.input_feishu)
        noti_layout.addLayout(fs_layout)

        # 企业微信 Webhook
        wecom_layout = QHBoxLayout()
        wecom_layout.addWidget(QLabel("企业微信群机器人 Webhook:"))
        self.input_wecom = QLineEdit()
        self.input_wecom.setPlaceholderText("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx")
        wecom_layout.addWidget(self.input_wecom)
        noti_layout.addLayout(wecom_layout)

        # 钉钉 Webhook
        ding_layout = QHBoxLayout()
        ding_layout.addWidget(QLabel("钉钉群机器人 Webhook:"))
        self.input_dingtalk = QLineEdit()
        self.input_dingtalk.setPlaceholderText("https://oapi.dingtalk.com/robot/send?access_token=xxxxxx")
        ding_layout.addWidget(self.input_dingtalk)
        noti_layout.addLayout(ding_layout)

        # 自定义 Webhook
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("通用自定义 Webhook:"))
        self.input_custom = QLineEdit()
        self.input_custom.setPlaceholderText("https://sctapi.ftqq.com/xxxx.send (Server酱/PushDeer/个人接口)")
        custom_layout.addWidget(self.input_custom)
        noti_layout.addLayout(custom_layout)

        # 管理员私聊
        admin_layout = QHBoxLayout()
        admin_layout.addWidget(QLabel("管理员 QQ 私聊通知:"))
        self.input_admin_qq = QLineEdit()
        self.input_admin_qq.setPlaceholderText("输入接收私聊通知的管理 QQ 号 (填 0 表示不使用，避免频繁发送风控)")
        admin_layout.addWidget(self.input_admin_qq)

        btn_test_noti = QPushButton("🔔 发送测试通知")
        btn_test_noti.setProperty("class", "btn_outline")
        btn_test_noti.clicked.connect(self.test_notification)
        admin_layout.addWidget(btn_test_noti)

        noti_layout.addLayout(admin_layout)
        layout.addWidget(noti_box)

        layout.addStretch()

    def on_preset_changed(self, idx: int):
        if idx == 0:
            self.input_base_url.setText("https://api.deepseek.com/v1")
            self.input_model.setText("deepseek-chat")
        elif idx == 1:
            self.input_base_url.setText("https://dashscope.aliyuncs.com/compatible-mode/v1")
            self.input_model.setText("qwen-plus")
        elif idx == 2:
            self.input_base_url.setText("https://api.openai.com/v1")
            self.input_model.setText("gpt-4o-mini")

    def load_current_settings(self):
        cfg = self.main_win.config
        agent_cfg = cfg.get("agent", {})
        self.input_base_url.setText(agent_cfg.get("base_url", "https://api.deepseek.com/v1"))
        self.input_api_key.setText(agent_cfg.get("api_key", ""))
        self.input_model.setText(agent_cfg.get("model", "deepseek-chat"))

        noti_cfg = cfg.get("notifications", {})
        self.input_feishu.setText(noti_cfg.get("feishu_webhook", ""))
        self.input_wecom.setText(noti_cfg.get("wecom_webhook", ""))
        self.input_dingtalk.setText(noti_cfg.get("dingtalk_webhook", ""))
        self.input_custom.setText(noti_cfg.get("custom_webhook", ""))
        self.input_admin_qq.setText(str(noti_cfg.get("admin_qq", 0)))

        if self.input_api_key.text().strip():
            self.label_ai_status.setText("状态: 凭证已配置 (点击按钮可测连通性)")
            self.label_ai_status.setStyleSheet("color: #10B981; font-weight: bold;")
        else:
            self.label_ai_status.setText("状态: 未配置密钥 (当前运行纯规则模式)")
            self.label_ai_status.setStyleSheet("color: #64748B; font-weight: bold;")

    def test_ai_connection(self):
        base_url = self.input_base_url.text().strip().rstrip("/")
        api_key = self.input_api_key.text().strip()
        model = self.input_model.text().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请先填入 API Key 密钥凭证！")
            return

        self.label_ai_status.setText("状态: 正在测试连通性...")
        self.label_ai_status.setStyleSheet("color: #F59E0B; font-weight: bold;")

        async def do_test():
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 10
            }
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    res = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        return True, "API 凭证有效，连接大模型成功！"
                    else:
                        return False, f"HTTP {res.status_code}: {res.text[:100]}"
                except Exception as e:
                    return False, f"请求异常: {str(e)}"

        try:
            ok, msg = asyncio.run(do_test())
            if ok:
                self.label_ai_status.setText("状态: 凭证有效 正常连接")
                self.label_ai_status.setStyleSheet("color: #10B981; font-weight: bold;")
                QMessageBox.information(self, "测试成功", f"🎉 大模型连通性检测通过！\n\n{msg}")
            else:
                self.label_ai_status.setText("状态: 连接失败")
                self.label_ai_status.setStyleSheet("color: #EF4444; font-weight: bold;")
                QMessageBox.critical(self, "测试失败", f"❌ 大模型测试失败：\n\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "异常", f"检测发生意外错误: {e}")

    def test_notification(self):
        # 简单发送测试
        test_text = "【测试通知】QQ群监控智能体推送通道联调测试正常！"
        feishu = self.input_feishu.text().strip()
        wecom = self.input_wecom.text().strip()
        dingtalk = self.input_dingtalk.text().strip()
        custom = self.input_custom.text().strip()

        if not any([feishu, wecom, dingtalk, custom]):
            QMessageBox.warning(self, "提示", "请至少填入一个 Webhook 地址再进行测试！")
            return

        async def do_push():
            results = []
            async with httpx.AsyncClient(timeout=5) as client:
                if feishu:
                    try:
                        r = await client.post(feishu, json={"msg_type": "text", "content": {"text": test_text}})
                        results.append(f"飞书: {'成功' if r.status_code==200 else '失败('+str(r.status_code)+')'}")
                    except Exception as e:
                        results.append(f"飞书: 异常({e})")
                if wecom:
                    try:
                        r = await client.post(wecom, json={"msgtype": "text", "text": {"content": test_text}})
                        results.append(f"企微: {'成功' if r.status_code==200 else '失败('+str(r.status_code)+')'}")
                    except Exception as e:
                        results.append(f"企微: 异常({e})")
                if dingtalk:
                    try:
                        r = await client.post(dingtalk, json={"msgtype": "text", "text": {"content": test_text}})
                        results.append(f"钉钉: {'成功' if r.status_code==200 else '失败('+str(r.status_code)+')'}")
                    except Exception as e:
                        results.append(f"钉钉: 异常({e})")
                if custom:
                    try:
                        r = await client.post(custom, json={"message": test_text})
                        results.append(f"自定义: {'成功' if r.status_code==200 else '状态码'+str(r.status_code)}")
                    except Exception as e:
                        results.append(f"自定义: 异常({e})")
            return "\n".join(results)

        try:
            report = asyncio.run(do_push())
            QMessageBox.information(self, "推送测试结果", report)
        except Exception as e:
            QMessageBox.critical(self, "测试失败", str(e))

    def save_settings(self):
        cfg = self.main_win.config
        cfg.setdefault("agent", {})
        cfg["agent"]["base_url"] = self.input_base_url.text().strip()
        cfg["agent"]["api_key"] = self.input_api_key.text().strip()
        cfg["agent"]["model"] = self.input_model.text().strip()

        cfg.setdefault("notifications", {})
        cfg["notifications"]["feishu_webhook"] = self.input_feishu.text().strip()
        cfg["notifications"]["wecom_webhook"] = self.input_wecom.text().strip()
        cfg["notifications"]["dingtalk_webhook"] = self.input_dingtalk.text().strip()
        cfg["notifications"]["custom_webhook"] = self.input_custom.text().strip()
        
        adm_qq = self.input_admin_qq.text().strip()
        cfg["notifications"]["admin_qq"] = int(adm_qq) if adm_qq.isdigit() else 0

        try:
            with open(self.main_win.config_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)
            self.main_win.reload_engines()
            self.main_win.tab_monitor.refresh_stats()
            self.main_win.tab_logs.append_log("[设置] 大模型与推送通道配置已保存并即时生效。")
            QMessageBox.information(self, "保存成功", "大模型与推送通道配置已保存并即刻生效！")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法写入配置: {e}")
