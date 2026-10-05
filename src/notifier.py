import httpx
from datetime import datetime
try:
    from database import save_captured_message
except ImportError:
    from src.database import save_captured_message

class Notifier:
    def __init__(self, config: dict):
        self.config = config
        self.noti_cfg = config.get("notifications", {})
        self.onebot_http = config.get("onebot", {}).get("http_url", "http://127.0.0.1:3000").rstrip("/")
        self.token = config.get("onebot", {}).get("access_token", "")

    async def notify(
        self,
        group_id: int,
        user_id: int,
        sender_name: str,
        group_name: str,
        raw_message: str,
        analysis: dict
    ):
        intent = analysis.get("intent", "未分类")
        urgency = analysis.get("urgency", "普通")
        summary = analysis.get("summary", raw_message[:60])
        entities = analysis.get("entities", {})
        fallback = analysis.get("fallback_mode", False)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. 控制台结构化输出
        if self.noti_cfg.get("console_output", True):
            print("\n" + "=" * 65)
            print(f"🎯 [抓取到目标群消息] {now_str}")
            print(f"📌 群号: {group_id} ({group_name or '群聊'})")
            print(f"👤 发言人: {sender_name} (QQ: {user_id})")
            print(f"🏷️  意图类别: {intent} | 紧迫度: {urgency} {'(纯规则模式)' if fallback else '(AI语义研判)'}")
            print(f"💡 智能摘要: {summary}")
            if any(entities.values()):
                print("📦 关键要素提取:")
                for k, v in entities.items():
                    if v:
                        print(f"   • {k}: {v}")
            print(f"💬 原始消息: {raw_message.strip()}")
            print("=" * 65 + "\n")

        # 2. 本地 SQLite 持久化
        if self.noti_cfg.get("sqlite_storage", True):
            save_captured_message(
                group_id=group_id,
                user_id=user_id,
                raw_message=raw_message,
                sender_name=sender_name,
                group_name=group_name,
                is_target=True,
                intent=intent,
                urgency=urgency,
                summary=summary,
                entities=entities
            )

        # 3. 飞书机器人 Webhook 推送
        feishu_url = self.noti_cfg.get("feishu_webhook")
        if feishu_url:
            await self._push_feishu(feishu_url, group_id, sender_name, summary, raw_message)

        # 4. 企业微信机器人 Webhook 推送
        wecom_url = self.noti_cfg.get("wecom_webhook")
        if wecom_url:
            await self._push_wecom(wecom_url, group_id, sender_name, summary, raw_message)

        # 5. 钉钉机器人 Webhook 推送
        dingtalk_url = self.noti_cfg.get("dingtalk_webhook")
        if dingtalk_url:
            await self._push_dingtalk(dingtalk_url, group_id, sender_name, summary, raw_message)

        # 6. 自定义 Webhook 推送
        custom_url = self.noti_cfg.get("custom_webhook")
        if custom_url:
            await self._push_custom(custom_url, {
                "group_id": group_id,
                "user_id": user_id,
                "sender_name": sender_name,
                "summary": summary,
                "intent": intent,
                "urgency": urgency,
                "raw_message": raw_message,
                "entities": entities,
                "timestamp": now_str
            })

        # 7. 可选 QQ 私聊通知管理员
        admin_qq = self.noti_cfg.get("admin_qq", 0)
        if admin_qq and admin_qq > 10000:
            await self._push_qq_private(admin_qq, f"【监控提醒】群{group_id}线索:\n{summary}\n发信人:{sender_name}({user_id})")

    async def _push_feishu(self, url: str, group_id: int, sender: str, summary: str, raw: str):
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"【QQ群消息监听提醒】\n群号: {group_id}\n发言人: {sender}\n核心内容: {summary}\n原始消息: {raw[:150]}"
            }
        }
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"[Notifier] 飞书推送失败: {e}")

    async def _push_wecom(self, url: str, group_id: int, sender: str, summary: str, raw: str):
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"【QQ群监控】群: {group_id} | 发言: {sender}\n摘要: {summary}\n原文: {raw[:150]}"
            }
        }
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"[Notifier] 企微推送失败: {e}")

    async def _push_dingtalk(self, url: str, group_id: int, sender: str, summary: str, raw: str):
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"【QQ群监控】群: {group_id}\n发言人: {sender}\n提炼: {summary}"
            }
        }
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"[Notifier] 钉钉推送失败: {e}")

    async def _push_custom(self, url: str, data: dict):
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(url, json=data)
            except Exception as e:
                print(f"[Notifier] 自定义Webhook推送失败: {e}")

    async def _push_qq_private(self, admin_qq: int, message: str):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(
                    f"{self.onebot_http}/send_private_msg",
                    headers=headers,
                    json={"user_id": admin_qq, "message": message}
                )
            except Exception as e:
                print(f"[Notifier] QQ私聊发送失败: {e}")
