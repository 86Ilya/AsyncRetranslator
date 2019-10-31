import asyncio

import json

from retranslator.safeconnect import SafeConnect

# technically demo_spamer is not belongs to this project,
# in that case he have his own config

default_cfg = {
    "LOGFILE": None,
    "LOG_FORMAT": "%(asctime)s %(levelname).1s %(message)s",
    "LOG_DATEFMT": "%Y.%m.%d,%H:%M:%S",
    "RECONNECT_ATTEMPTS": 3,
    "RECONNECT_WAIT": 5,
    "SENDER": {"HOST": "retranslator", "PORT": 7777}
}


messages = ["ASDF", "Русские буквы", "Smiles😀😁😂😃😄😅😆😇😈😉😊😋😌😍😎😏😐😑😒😓😔😕😖😗😘😙😚😛😜😝😞😟😠😡😢😣", "12 11 111 22"]


async def spamer(cfg):

    # each time create new connection
    for message in messages:
        # make pause for visibility
        await asyncio.sleep(2)
        async with SafeConnect(tuple(cfg["SENDER"].values())) as stream:
            _, writer = stream
            writer.write(json.dumps({"RETRANSLATE_MESSAGE": message}).encode())


if __name__ == '__main__':
    asyncio.run(spamer(default_cfg))
