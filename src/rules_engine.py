import json
import re
import os

class RulesEngine:
    def __init__(self, rules_path: str, config: dict):
        self.rules_path = rules_path
        self.config = config
        self.target_groups = set(config.get("monitoring", {}).get("target_groups", []))
        self.ignore_users = set(config.get("monitoring", {}).get("ignore_users", []))
        
        self.include_keywords = []
        self.exclude_keywords = []
        self.regex_patterns = []
        
        self.load_rules()

    def load_rules(self):
        if not os.path.exists(self.rules_path):
            return
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                rules = data.get("rules", {})
                self.include_keywords = rules.get("include_keywords", [])
                self.exclude_keywords = rules.get("exclude_keywords", [])
                patterns = rules.get("regex_patterns", [])
                self.regex_patterns = [re.compile(p, re.IGNORECASE) for p in patterns if p]
        except Exception as e:
            print(f"[RulesEngine] 加载规则文件失败: {e}")

    def should_analyze(self, group_id: int, user_id: int, message_text: str) -> tuple[bool, str]:
        """
        L1 粗筛过滤
        返回 (是否进入下一层分析, 命中原因或排除原因)
        """
        # 1. 发信人黑名单过滤
        if user_id in self.ignore_users:
            return False, f"发信人 {user_id} 处于黑名单"

        # 2. 群白名单过滤
        if self.target_groups and group_id not in self.target_groups:
            return False, f"群号 {group_id} 不在监控白名单"

        # 3. 消息为空过滤
        text = (message_text or "").strip()
        if not text:
            return False, "消息为空"

        # 4. 排除关键词快速剪枝 (例如日常打卡、退群等)
        for kw in self.exclude_keywords:
            if kw in text:
                return False, f"命中排除关键词: {kw}"

        # 5. 如果没有配置任何包含关键词，则默认全部进入分析
        if not self.include_keywords and not self.regex_patterns:
            return True, "全量监听"

        # 6. 命中关键词
        for kw in self.include_keywords:
            if kw.lower() in text.lower():
                return True, f"命中关键词: {kw}"

        # 7. 命中正则特征 (如手机号/微信号等联系方式)
        for pattern in self.regex_patterns:
            if pattern.search(text):
                return True, f"命中正则规则: {pattern.pattern}"

        return False, "未命中任何粗筛特征"
