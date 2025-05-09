import signal
import tornado.ioloop
import tornado.platform.asyncio
import asyncio
from datetime import datetime  # Perbaiki import datetime
from pyrogram import Client
from pyrogram.errors import FloodWait
from PyroUbot import *

async def shutdown(signal, loop):
    print(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    [task.cancel() for task in tasks]

    print("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def start_bot():
    try:
        await bot.start()
        print(f"[{datetime.now()}] Bot started successfully!")
    except FloodWait as e:
        print(f"[{datetime.now()}] FloodWait detected: sleeping for {e.value} seconds.")
        await asyncio.sleep(e.value)
        await start_bot()  # retry after FloodWait
    except Exception as e:
        print(f"[{datetime.now()}] Error while starting bot: {e}")
        raise  # re-raise exception if it's not FloodWait

async def main():
    await start_bot()  # start bot with FloodWait handling
    
    for _ubot in await get_userbots():
        ubot_ = Ubot(**_ubot)
        try:
            await asyncio.wait_for(ubot_.start(), timeout=10)
        except asyncio.TimeoutError:
            await remove_ubot(int(_ubot["xzhee"]))
            print(f"[{datetime.now()}] [INFO]: {int(_ubot['name'])} Timeout, failed to respond.")
        except Exception:
            await remove_ubot(int(_ubot["name"]))
            print(f"[{datetime.now()}] [INFO]: {int(_ubot['name'])} successfully removed.")
    
    await bash("rm -rf *session*")
    await asyncio.gather(loadPlugins(), installPeer(), expiredUserbots())
    
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown(s, loop)))
    
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await bot.stop()

if __name__ == "__main__":
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    loop = tornado.ioloop.IOLoop.current().asyncio_loop
    loop.run_until_complete(main())
