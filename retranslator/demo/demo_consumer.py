import asyncio
import json
import logging
import os

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
    "RECONNECT_ATTEMPTS": 3,
    "RECONNECT_WAIT": 5,
    "CONSUMER_DEFAULT_PORT": 6666,
    "CONSUMER_IP": "0.0.0.0",
    "CONSUMERID": os.getenv("CONSUMERID")
}


def create_handler(cfg):
    m_size = cfg["MAX_MESSAGE_SIZE"]

    async def handle_message(reader, writer):
        message = await reader.read(m_size)
        logger.info(f'Consumer {cfg["CONSUMERID"]} received a message "{message.decode()}"')
    return handle_message


async def consumer(cfg):
    logging.basicConfig(filename=cfg["LOGFILE"], level=cfg["LOGLEVEL"],
                        format=cfg["LOG_FORMAT"], datefmt=cfg["LOG_DATEFMT"])

    receiver_host = cfg["RECEIVER"]["HOST"]
    receiver_port = cfg["RECEIVER"]["PORT"]
    m_size = cfg["MAX_MESSAGE_SIZE"]

    id = cfg["CONSUMERID"]
    consumer_port = cfg["CONSUMER_DEFAULT_PORT"]
    consumer_ip = cfg["CONSUMER_IP"]

    # register in receiver
    for i in range(cfg["RECONNECT_ATTEMPTS"]):
        try:
            reader, writer = await asyncio.open_connection(receiver_host, receiver_port)
            break
        except ConnectionRefusedError as error:
            logger.error(error)
            if i < cfg["RECONNECT_ATTEMPTS"]:
                await asyncio.sleep(cfg["RECONNECT_WAIT"])

        raise Exception("Can't connect to receiver")

    message = json.dumps({"REGISTER_CONSUMER": {"CONSUMER_ID": id}})
    writer.write(message.encode())
    answer = await reader.read(m_size)
    # import pdb; pdb.set_trace()

    writer.close()
    if not json.loads(answer).get("RESULT", False):
        return

    # start server after successful registration
    handler = create_handler(cfg)
    server = await asyncio.start_server(handler, consumer_ip, consumer_port)
    addr = server.sockets[0].getsockname()
    logger.info(f"Consumer serving on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(consumer(default_cfg))
