import json
import httpx
import re

AGENT_SYSTEM_PROMPT = """你是一个专业的电商订单与社群情报分析专家。
你的任务是从QQ群聊天消息中，研判并精准结构化提取“电商订单号”、“收件人”、“手机号/隐私分机号”、“省市区收件地址”、“商品规格/型号”、“物流备注”。

请输出合法的 JSON 格式，字段定义如下：
{
  "is_target": true 或 false (是否属于目标高价值消息，如订单/发货地址/求购线索),
  "intent": "订单发货 / 求购需求 / 报价合作 / 客诉反馈 / 日常闲聊",
  "urgency": "高 / 中 / 低",
  "summary": "一句话精准摘要，例如：李先生(138xxxx) 购买 小鸭KA WBH30339 发西宁市",
  "entities": {
    "order_id": "提取到的订单号 (通常为15-25位数字)，无则填空",
    "recipient": "收件人姓名，无则填空",
    "phone": "收件人电话或虚拟分机号，无则填空",
    "address": "完整收件地址 (含省市县街道小区门牌)，无则填空",
    "product_spec": "商品型号/规格/颜色/数量，无则填空",
    "remark": "物流或特殊发货备注 (如 发顺丰)，无则填空"
  }
}
只输出合法 JSON，严禁输出任何 markdown 格式或额外解释说明。
"""

class AgentEngine:
    def __init__(self, config: dict):
        agent_cfg = config.get("agent", {})
        self.enabled = agent_cfg.get("enabled", True)
        self.base_url = agent_cfg.get("base_url", "https://api.deepseek.com/v1").rstrip("/")
        self.api_key = agent_cfg.get("api_key", "").strip()
        self.model = agent_cfg.get("model", "deepseek-chat")
        self.temperature = agent_cfg.get("temperature", 0.1)
        self.timeout_sec = agent_cfg.get("timeout_sec", 15)

    async def analyze(self, sender_name: str, group_id: int, message_text: str, hit_reason: str) -> dict:
        """
        调用大模型或降级规则分析群消息
        """
        try:
            from src.order_parser import parse_ecommerce_order
        except ImportError:
            from order_parser import parse_ecommerce_order
        rule_parsed = parse_ecommerce_order(message_text)

        if not self.enabled or not self.api_key:
            # 降级模式：纯规则精准提取电商订单
            summary_parts = []
            if rule_parsed.get("recipient"):
                summary_parts.append(f"{rule_parsed['recipient']}({rule_parsed.get('phone', '')})")
            if rule_parsed.get("product_spec"):
                summary_parts.append(f"规格:{rule_parsed['product_spec']}")
            if rule_parsed.get("address"):
                summary_parts.append(f"发往:{rule_parsed['address'][:25]}...")
            
            auto_summary = " | ".join(summary_parts) if summary_parts else f"[{hit_reason}] {message_text[:60]}"
            intent_val = "订单发货" if (rule_parsed.get("phone") or rule_parsed.get("order_id")) else "商品咨询"

            return {
                "is_target": True,
                "intent": intent_val,
                "urgency": "高" if rule_parsed.get("phone") else "中",
                "summary": auto_summary,
                "entities": rule_parsed,
                "fallback_mode": True
            }

        user_content = f"群号: {group_id}\n发言人: {sender_name}\n粗筛触发: {hit_reason}\n原始消息内容:\n{message_text}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"} if "deepseek" in self.model or "gpt" in self.model else None
        }
        # 清理 None 值
        payload = {k: v for k, v in payload.items() if v is not None}

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            try:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_reply = data["choices"][0]["message"]["content"].strip()
                
                # 清洗可能的 markdown 包裹
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_reply, flags=re.MULTILINE)
                cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()
                
                result = json.loads(cleaned)
                result["fallback_mode"] = False
                return result
            except Exception as e:
                # 异常时保底降级为纯规则精准提取，不阻断系统运行
                summary_parts = []
                if rule_parsed.get("recipient"):
                    summary_parts.append(f"{rule_parsed['recipient']}({rule_parsed.get('phone', '')})")
                if rule_parsed.get("product_spec"):
                    summary_parts.append(f"规格:{rule_parsed['product_spec']}")
                if rule_parsed.get("address"):
                    summary_parts.append(f"发往:{rule_parsed['address'][:25]}...")
                
                auto_summary = " | ".join(summary_parts) if summary_parts else f"[{hit_reason}] {message_text[:60]}"
                intent_val = "订单发货" if (rule_parsed.get("phone") or rule_parsed.get("order_id")) else "商品咨询"

                return {
                    "is_target": True,
                    "intent": intent_val,
                    "urgency": "高" if rule_parsed.get("phone") else "中",
                    "summary": auto_summary,
                    "entities": rule_parsed,
                    "fallback_mode": True
                }
