import asyncio

import aiohttp


async def main():
    ds_sent = False
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('ws://127.0.0.1:8000/ws') as ws:
            # await for messages and send messages
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(f'SERVER says - {msg.data}')
                    if not ds_sent:
                        await ws.send_str("dataset_id=train_1")
                        ds_sent = True
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break


asyncio.run(main())
