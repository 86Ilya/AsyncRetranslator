import logging
import asyncio


logger = logging.getLogger()


def create_handler(cfg):
    receiver_ip = cfg["RECEIVER"]["IP"]
    receiver_port = cfg["RECEIVER"]["PORT"]
    m_size = cfg["MAX_MESSAGE_SIZE"]

    async def handle_message(reader, writer):
        # read message
        message = await reader.read(m_size)
        logger.info(f"Sender got a message {message.strip().decode('utf-8')}")

        # send message to receiver
        _, receiver_writer = await asyncio.open_connection(receiver_ip, receiver_port)
        receiver_writer.write(message)
        await receiver_writer.drain()
        receiver_writer.close()

    return handle_message


async def sender(cfg):
    ip, port = cfg["SENDER"]["IP"], cfg["SENDER"]["PORT"]
    handler = create_handler(cfg)
    # import pdb; pdb.set_trace()
    server = await asyncio.start_server(
        handler, ip, port)

    addr = server.sockets[0].getsockname()
    logger.info(f'Sender Serving on {addr}')

    async with server:
        await server.serve_forever()
