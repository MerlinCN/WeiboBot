from typing import Dict

from .log import Log
import time

__all__ = ["main_header", "IntField", "StrField", "BoolField", "DictField", "ListField", "get_logger",
           "parse_cookies"]


def main_header(cookies: bytes) -> Dict[str, str]:
    headers_raw = b'''
            accept: application/json, text/plain, */*
    accept-encoding: gzip, deflate, br
    accept-language: zh-CN,zh;q=0.9
    cookie: %b
    mweibo-pwa: 1
    referer: https://m.weibo.cn/
    sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"
    sec-ch-ua-mobile: ?0
    sec-ch-ua-platform: "Windows"
    sec-fetch-dest: empty
    sec-fetch-mode: cors
    sec-fetch-site: same-origin
    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36
    x-requested-with: XMLHttpRequest
    x-xsrf-token: 1d1b9c
            '''

    return formatHeader(headers_raw, cookies)


def formatHeader(headers_raw: bytes, cookies: bytes) -> Dict[str, str]:
    """
    复制浏览器中的header
    """
    headers_raw = headers_raw % cookies
    headers = headers_raw.splitlines()
    headers_tuples = [header.split(b":", 1) for header in headers]

    result_dict = {}
    for header_item in headers_tuples:
        if not len(header_item) == 2:
            continue

        item_key: str = header_item[0].strip().decode("utf8")
        item_value: str = header_item[1].strip().decode("utf8")
        result_dict[item_key] = item_value

    return result_dict


def IntField() -> int:
    return 0


def StrField() -> str:
    return ""


def BoolField() -> bool:
    return False


def DictField() -> dict:
    return {}


def ListField() -> list:
    return []


def get_logger(name: str, is_debug=True) -> Log:
    return Log(name, is_debug=is_debug)


def parse_cookies(cookies: str) -> list:
    result = []
    for kv in cookies.split(";"):
        k = kv.split("=")[0].replace(" ", "")
        v = kv.split("=")[1].replace(" ", "")
        domain = ".weibo.cn"
        if k == "XSRF-TOKEN":
            domain = ".m.weibo.cn"

        result.append({
            "domain": domain,
            "expiry": int(time.time()) + 60 * 60 * 24 * 365,
            "name": k,
            "path": "/",
            "secure": False,
            "httpOnly": False,
            "value": v,
        })

    return result
