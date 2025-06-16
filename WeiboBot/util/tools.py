import json
from pathlib import Path

import httpx


def save_cookies(cookies_path: Path, client: httpx.AsyncClient):
    """保存cookies到文件"""
    cookies_dict = {}
    for cookie in client.cookies.jar:
        cookies_dict[cookie.name] = cookie.value

    with open(cookies_path, "w", encoding="utf-8") as f:
        json.dump(cookies_dict, f, ensure_ascii=False, indent=4)


def load_cookies(cookies_path: Path, client: httpx.AsyncClient):
    """从文件加载cookies"""
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies_dict = json.load(f)
    for name, value in cookies_dict.items():
        client.cookies.set(name, value)


def get_cookies_value(client: httpx.AsyncClient, name: str) -> str:
    for cookie in client.cookies.jar:
        if cookie.name == name:
            return cookie.value
    return ""
