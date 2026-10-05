# -*- coding: utf-8 -*-
import os
import json
import httpx
import logging

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "group_cache.json")
_MEM_CACHE = {}

def _load_cache():
    global _MEM_CACHE
    if not _MEM_CACHE and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _MEM_CACHE = json.load(f)
        except Exception:
            _MEM_CACHE = {}
    return _MEM_CACHE

def _save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_MEM_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save group cache: {e}")

def get_group_name(group_id: int, http_url: str = "http://127.0.0.1:3000", token: str = "") -> str:
    gid_str = str(group_id)
    cache = _load_cache()
    if gid_str in cache and cache[gid_str]:
        return cache[gid_str]

    # 尝试向 NapCat HTTP API 发送请求获取群名称
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        with httpx.Client(timeout=1.5) as client:
            resp = client.post(f"{http_url}/get_group_info", json={"group_id": group_id}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    g_name = data.get("data", {}).get("group_name", "")
                    if g_name:
                        cache[gid_str] = g_name
                        _save_cache()
                        return g_name
    except Exception:
        pass

    return f"群_{gid_str}"

def set_group_name(group_id: int, name: str):
    gid_str = str(group_id)
    cache = _load_cache()
    cache[gid_str] = name
    _save_cache()

def sync_all_groups(http_url: str = "http://127.0.0.1:3000", token: str = "") -> dict:
    """批量同步 NapCat 中小号加入的所有群聊信息"""
    cache = _load_cache()
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(f"{http_url}/get_group_list", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    for g in data.get("data", []):
                        gid = str(g.get("group_id"))
                        gname = g.get("group_name")
                        if gid and gname:
                            cache[gid] = gname
                    _save_cache()
    except Exception as e:
        logging.warning(f"sync_all_groups failed: {e}")
    return cache
