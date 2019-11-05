import asyncio
import json
import logging
import os

from retranslator.safeconnect import SafeConnect

logger = logging.getLogger()

# technically demo_consumer is not belongs to this project,
# in that case he have his own config

default_cfg = {
    "LOGFILE": None,
    "LOGLEVEL": logging.INFO,
    "LOG_FORMAT": "%(asctime)s %(levelname).1s %(message)s",
    "LOG_DATEFMT": "%Y.%m.%d,%H:%M:%S",
    "RECEIVER": {"HOST": "retranslator", "PORT": 8888},
    "MAX_MESSAGE_SIZE": 1024,
    "CONSUMERID": os.getenv("CONSUMERID")
}


async def consumer(cfg):
    logging.basicConfig(filename=cfg["LOGFILE"], level=cfg["LOGLEVEL"],
                        format=cfg["LOG_FORMAT"], datefmt=cfg["LOG_DATEFMT"])

    m_size = cfg["MAX_MESSAGE_SIZE"]

    id = cfg["CONSUMERID"]

    async with SafeConnect(tuple(cfg["RECEIVER"].values())) as stream:
        reader, writer = stream
        # register in receiver
        message = json.dumps({"REGISTER_CONSUMER": {"CONSUMER_ID": id}})
        writer.write(message.encode())
        await writer.drain()
        answer = await reader.read(m_size)

        if not json.loads(answer).get("RESULT", False):
            return

        while True:
            message = await reader.read(m_size)
            if not message:
                break
            logger.info(f"Consumer got:\n{message.decode()}")


if __name__ == '__main__':
    asyncio.run(consumer(default_cfg))
