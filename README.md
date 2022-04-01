<div align="center">

# WeiboBot

_基于微博H5 API开发的机器人框架_

<a href="https://pypi.org/project/WeiboBot/"><img alt="PyPI" src="https://img.shields.io/pypi/v/WeiboBot" /></a></td>
<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Version" src="https://img.shields.io/pypi/pyversions/WeiboBot" /></a>
<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Implementation" src="https://img.shields.io/pypi/implementation/WeiboBot" /></a>

<a href="https://github.com/MerlinCN/WeiboBot/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/MerlinCN/WeiboBot"></a>

</div>



WeiboBot 是一个基于微博H5 API开发的机器人框架，提供了一个简单的接口，可以让你的机器人更加简单的接入微博，并且提供了一些简单的指令，比如：转评赞，回复消息等

## 安装

`pip install WeiboBot`

## 开始使用

```python
from WeiboBot import Bot
from WeiboBot.message import Chat
from WeiboBot.weibo import Weibo
from WeiboBot.comment import Comment
cookies = "your cookies"
myBot = Bot(cookies=cookies)


@myBot.onNewMsg
async def on_msg(oChat: Chat):
    for msg in oChat.msg_list:  # 消息列表
        print(f"{msg.sender_screen_name}:{msg.text}")


@myBot.onNewWeibo
async def on_weibo(oWeibo: Weibo):
    if oWeibo.original_weibo is None:  # 原创微博
        print(f"{oWeibo.text}")

@myBot.onMentionCmt
async def on_mention_cmt(cmt: Comment):
    print(f"{cmt.text}") # 被评论@了

if __name__ == '__main__':
    myBot.run()

```

## 示例

[好康Bot](https://github.com/MerlinCN/WeiboWatchdog)

> 一个转发小姐姐的Bot
