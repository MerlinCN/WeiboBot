import traceback

from WeiboBot.const import ACTION
from WeiboBot.util import *
from WeiboBot.exception import *


class Action:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = ACTION.UNDONE
        self.run_time = 0
        self.logger = get_logger(__name__)

    async def run(self):
        if self.run_time > 5:
            self.status = ACTION.MAX_TRY
            return None, self.status
        self.status = ACTION.RUNNING
        self.run_time += 1
        try:
            result = await self.func(*self.args, **self.kwargs)
        except RequestError:
            self.status = ACTION.FAILED
            self.logger.error(traceback.format_exc())
            return None, self.status
        except Exception as e:
            self.status = ACTION.MAX_TRY
            self.logger.error(e)
            return None, self.status
        self.status = ACTION.DONE
        return result, self.status

    def __str__(self):
        return f'<Action: {self.func.__name__}>'
