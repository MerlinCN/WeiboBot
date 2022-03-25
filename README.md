<div align="center">

# WeiboBot

_基于微博H5 API开发的机器人框架_



</div>



WeiboBot 是一个基于微博H5 API开发的机器人框架，提供了一个简单的接口，可以让你的机器人更加简单的接入微博，并且提供了一些简单的指令，比如：转评赞，回复消息等

## 安装

`pip install weibobot`

## 开始使用

```python
from WeiboBot import Bot
from WeiboBot.message import Chat
from WeiboBot.weibo import Weibo

cookies = "your cookies"
myBot = Bot(cookies=cookies)


@myBot.onNewMsg
async def onMsg(oChat: Chat):
    for msg in oChat.msg_list:  # 消息列表
        print(f"{msg.sender_screen_name}:{msg.text}")


@myBot.onNewWeibo
async def onWeibo(oWeibo: Weibo):
    if oWeibo.original_weibo is None:  # 原创微博
        print(f"{oWeibo.text}")


if __name__ == '__main__':
    myBot.run()

```


