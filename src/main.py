import asyncio
import json
import os
import sys
import yaml
import websockets

# 路径常量与模块路径注入
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from rules_engine import RulesEngine
from agent_engine import AgentEngine
from notifier import Notifier
from database import init_db

# 路径常量
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")
RULES_PATH = os.path.join(BASE_DIR, "config", "rules.json")

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] 找不到配置文件: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def handle_event(event: dict, rules: RulesEngine, agent: AgentEngine, notifier: Notifier):
    post_type = event.get("post_type")
    
    # 仅处理群消息事件
    if post_type != "message":
        return

    message_type = event.get("message_type")
    if message_type != "group":
        return

    group_id = event.get("group_id", 0)
    user_id = event.get("user_id", 0)
    sender = event.get("sender", {})
    sender_name = sender.get("card") or sender.get("nickname") or f"用户_{user_id}"
    raw_message = event.get("raw_message", "")

    # L1 快速规则筛选
    should_analyze, reason = rules.should_analyze(group_id, user_id, raw_message)
    if not should_analyze:
        return

    # 解析获取群名称
    onebot_cfg = config.get("onebot", {})
    http_url = onebot_cfg.get("http_url", "http://127.0.0.1:3000")
    token = onebot_cfg.get("access_token", "")
    try:
        from src.group_service import get_group_name
    except ImportError:
        from group_service import get_group_name
    g_name = get_group_name(group_id, http_url, token)

    print(f"[*] 命中粗筛规则 [{reason}] 来自【{g_name}】({group_id}) 的 {sender_name}: {raw_message[:50]}...")

    # L2 智能体深度语义研判
    try:
        analysis = await agent.analyze(
            sender_name=sender_name,
            group_id=group_id,
            message_text=raw_message,
            hit_reason=reason
        )
        
        # 判断大模型或规则引擎是否判定为目标高价值消息
        if analysis.get("is_target", True):
            await notifier.notify(
                group_id=group_id,
                user_id=user_id,
                sender_name=sender_name,
                group_name=g_name,
                raw_message=raw_message,
                analysis=analysis
            )
        else:
            print(f"[-] AI研判为非目标消息/日常闲聊，已自动忽略。")
    except Exception as e:
        print(f"[!] 分析消息流程出现异常: {e}")

async def run_listener():
    config = load_config()
    init_db()

    rules = RulesEngine(RULES_PATH, config)
    agent = AgentEngine(config)
    notifier = Notifier(config)

    onebot_cfg = config.get("onebot", {})
    ws_url = onebot_cfg.get("ws_url", "ws://127.0.0.1:3001")
    reconnect_interval = onebot_cfg.get("reconnect_interval_sec", 5)
    token = onebot_cfg.get("access_token", "")

    extra_headers = {}
    if token:
        extra_headers["Authorization"] = f"Bearer {token}"

    print("=" * 60)
    print("   🤖 QQ群消息智能体监听服务已就绪")
    print(f"   • 连接网关: {ws_url}")
    print(f"   • 目标群组: {config.get('monitoring', {}).get('target_groups') or '全部群聊'}")
    print(f"   • AI 模型 : {config.get('agent', {}).get('model')} ({'已开启' if config.get('agent', {}).get('api_key') else '未配置API Key，纯规则模式'})")
    print("=" * 60)

    while True:
        try:
            print(f"[*] 正在尝试连接 NapCat OneBot 网关: {ws_url} ...")
            async with websockets.connect(
                ws_url,
                additional_headers=extra_headers if extra_headers else None,
                ping_interval=30,
                ping_timeout=10
            ) as ws:
                print(f"[✔] 成功连接 NapCat OneBot 网关！正在实时监听群消息...")
                async for message in ws:
                    try:
                        event = json.loads(message)
                        asyncio.create_task(handle_event(event, rules, agent, notifier))
                    except Exception as parse_err:
                        print(f"[!] 解析网关推送数据失败: {parse_err}")

        except (websockets.ConnectionClosed, websockets.InvalidURI, OSError) as e:
            print(f"[!] 网关连接中断或 NapCat 尚未启动 ({e})，{reconnect_interval} 秒后自动重试...")
            await asyncio.sleep(reconnect_interval)
        except Exception as e:
            print(f"[!] 运行时异常: {e}，{reconnect_interval} 秒后重试...")
            await asyncio.sleep(reconnect_interval)

if __name__ == "__main__":
    try:
        asyncio.run(run_listener())
    except KeyboardInterrupt:
        print("\n[*] 智能体监听服务已停止。")
