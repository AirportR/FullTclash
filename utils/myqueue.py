import asyncio

from loguru import logger
from pyrogram import Client
from pyrogram.types import Message
from utils.collector import reload_config as r1
from utils.cleaner import reload_config as r2

import botmodule

q = asyncio.Queue(maxsize=1)
task_num = 0


async def bot_task_queue(client: Client, message, task_type: str, qu: asyncio.Queue, **kwargs):
    """
    一个简单的任务队列

    include_text: 包含过滤器
    exclude_text: 排除过滤器
    url: 订阅链接
    :param client: 客户端
    :param message: 消息对象
    :param task_type: 测试类型
    :param qu: 队列
    :return: no return
    """
    slaveid = kwargs.get('slaveid', 'local')
    if slaveid != 'local':
        await qu.get()
        qu.task_done()
        await botmodule.process(client, message, put_type=task_type, **kwargs)
    else:
        await botmodule.process(client, message, put_type=task_type, **kwargs)
        await qu.get()
        qu.task_done()


async def bot_task_queue_master(client: Client, message, task_type: str, qu: asyncio.Queue, **kwargs):
    pass


async def bot_put(client: Client, message: Message, put_type: str, test_items: list = None, **kwargs):
    """
    推送任务，bot推送反馈
    :param test_items:
    :param client:
    :param message:
    :param put_type:
    :return:
    """
    global task_num
    task_num += 1
    try:
        if test_items is None:
            test_items = []
        logger.info("任务测试项为: " + str(test_items))
        mes = await message.reply("排队中,前方队列任务数量为: " + str(task_num - 1))
        await q.put(message)
        r1(test_items)
        r2(test_items)
        await mes.delete()
        await bot_task_queue(client, message, put_type, q, test_items=test_items, **kwargs)
        task_num -= 1

    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))


async def bot_put_master(client: Client, message: Message, putinfo: dict, **kwargs):
    global task_num
    task_num += 1
    try:
        test_items = putinfo.get('test-items', None)
        edit_chat_id = putinfo.get('edit-chat-id', None)
        edit_message_id = putinfo.get('edit-message-id', None)
        master_id = kwargs.get('master_id', None)
        if master_id is None and edit_chat_id is None and edit_message_id is None:
            task_num -= 1
            return
        if test_items is None:
            test_items = []
        logger.info("任务测试项为: " + str(test_items))
        botmsg = await message.reply(f"/relay {master_id} edit {edit_chat_id} {edit_message_id} 排队中,前方队列任务数量为:"
                                     + str(task_num - 1))
        await q.put(message)
        r1(test_items)
        r2(test_items)
        await message.reply(f"/relay {master_id} edit {edit_chat_id} {edit_message_id} 测试开始啦~")
        await asyncio.sleep(10)
        await botmsg.edit_text(f"/relay {master_id} edit {edit_chat_id} {edit_message_id} 测试结束啦。")
        # await bot_task_queue_master(client, message, put_type, q, **kwargs)
        task_num -= 1
        await q.get()
        q.task_done()

    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))
