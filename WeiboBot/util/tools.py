import json
from pathlib import Path
from typing import List

import httpx


def save_cookies(cookies_path: Path, client: httpx.AsyncClient):
    """保存cookies到文件"""
    cookies_dict = {}
    for cookie in client.cookies.jar:
        cookies_dict[cookie.name] = cookie.value
    cookies_path.parent.mkdir(parents=True, exist_ok=True)
    cookies_path.touch(exist_ok=True)
    # 根据cookies_dict的key排序
    cookies_dict = dict(sorted(cookies_dict.items()))
    with open(cookies_path, "w", encoding="utf-8") as f:
        json.dump(cookies_dict, f, ensure_ascii=False, indent=4)


def load_cookies(cookies_path: Path, client: httpx.AsyncClient) -> bool:
    if not cookies_path.exists():
        return False
    """从文件加载cookies"""
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies_dict = json.load(f)
    for name, value in cookies_dict.items():
        client.cookies.set(name, value)
    return True


def get_cookies_value(client: httpx.AsyncClient, name: str) -> str:
    for cookie in client.cookies.jar:
        if cookie.name == name:
            return cookie.value
    return ""


def httpx_cookies_to_playwright(httpx_cookies) -> List[dict]:
    cookies = []
    for cookie in httpx_cookies:
        # Playwright 需要 domain 不带前导点
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": "weibo.cn",
                "path": cookie.path,
                "expires": cookie.expires or -1,
                "httpOnly": False,
                "secure": cookie.secure,
            }
        )
    return cookies
