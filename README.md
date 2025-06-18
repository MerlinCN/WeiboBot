<div align="center">

# WeiboBot

_基于微博H5 API开发的爬虫框架_

<a href="https://pypi.org/project/WeiboBot/"><img alt="PyPI" src="https://img.shields.io/pypi/v/WeiboBot" /></a></td>
<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Version" src="https://img.shields.io/pypi/pyversions/WeiboBot" /></a>
<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Implementation" src="https://img.shields.io/pypi/implementation/WeiboBot" /></a>

<a href="https://github.com/MerlinCN/WeiboBot/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/MerlinCN/WeiboBot"></a>

</div>



WeiboBot 是一个基于微博H5 API开发的爬虫框架，提供了简单的接口，包括了一些指令，比如：转评赞，回复消息等
可以选择直接获取数据，也可以持续运行

## 安装

### 普通安装

```bash
pip install WeiboBot
```

### 带截图功能

```bash
pip install WeiboBot[screenshot]
```

### 源码安装（推荐使用uv）

```bash
uv sync --all-extras
```





## 开始使用(生命周期)

```python
from loguru import logger

from WeiboBot import Bot, ChatDetail, Comment, Weibo

bot = Bot()


@bot.onNewMsg()  # 被私信的时候触发
async def on_msg(chat: ChatDetail):
    for msg in chat.msgs:  # 消息列表
        logger.info(f"{msg.sender_screen_name}:{msg.text}")


@bot.onNewWeibo()  # 首页刷到新微博时触发
async def on_weibo(weibo: Weibo):
    weibo = await bot.weibo_info(weibo.mid)  # 获取微博详细信息(长微博才需要)
    logger.info(f"{weibo.text}")


@bot.onMentionCmt()  # 提及我的评论时触发
async def on_mention_cmt(cmt: Comment):
    logger.info(f"收到{cmt.mid}的评论")


@bot.onTick()  # 每次循环触发
async def on_tick():
    logger.info("tick")


if __name__ == "__main__":
    bot.run()

```

## 开始使用(仅调用)

```python
import asyncio

from loguru import logger

import WeiboBot.const as const
from WeiboBot import NetTool


async def main():
    async with NetTool() as nettool:
        user = await nettool.user_info(nettool.mid)
        logger.info(user)
        weibo_example1 = await nettool.weibo_info(123456)  # 获取微博
        weibo_example2 = await nettool.post_weibo(
            "发一条微博", visible=const.VISIBLE.ONLY_ME
        )
    # ...... 其他操作


if __name__ == "__main__":
    asyncio.run(main())
```

## 更新路线图

目前项目仍在重构中

- [x]  对旧API的整合
- [ ]  扩展更加多的API
- [x]  提升登录的健壮性
- [ ]  增加更多测试用例和自动化
- [ ]  去掉 logger

## 示例

[好康Bot](https://github.com/MerlinCN/WeiboWatchdog)

正在重构中

> 一个转发小姐姐的Bot

