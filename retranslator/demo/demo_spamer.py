import asyncio

import json

from retranslator.safeconnect import SafeConnect

# technically demo_spamer is not belongs to this project,
# in that case he have his own config

default_cfg = {
    "LOGFILE": None,
    "LOG_FORMAT": "%(asctime)s %(levelname).1s %(message)s",
    "LOG_DATEFMT": "%Y.%m.%d,%H:%M:%S",
    "SENDER": {"HOST": "retranslator", "PORT": 7777}
}


messages = ["ASDF", "Русские буквы", "Smiles😀😁😂😃😄😅😆😇😈😉😊😋😌😍😎😏😐😑😒😓😔😕😖😗😘😙😚😛😜😝😞😟😠😡😢😣", "12 11 111 22"]


async def spamer(cfg):

    async with SafeConnect(tuple(cfg["SENDER"].values())) as stream:
        _, writer = stream
        writer.write((json.dumps({"RETRANSLATE_MESSAGE": messages})).encode())
        await writer.drain()

    async with SafeConnect(tuple(cfg["SENDER"].values())) as stream:
        _, writer = stream
        writer.write((json.dumps({"RETRANSLATE_MESSAGE": messages[::-1]})).encode())
        await writer.drain()

if __name__ == '__main__':
    asyncio.run(spamer(default_cfg))
