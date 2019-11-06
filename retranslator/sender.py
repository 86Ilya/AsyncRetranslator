import logging
import asyncio


logger = logging.getLogger()


class CreateHandler:
    connection = dict()

    def __init__(self, cfg):
        self.receiver_writer = None
        self.receiver_stream = None
        self.receiver_ip = cfg["RECEIVER"]["IP"]
        self.receiver_port = cfg["RECEIVER"]["PORT"]
        self.m_size = cfg["MAX_MESSAGE_SIZE"]

    async def __call__(self, reader, writer):
        if self.receiver_stream not in self.connection.keys():
            self.receiver_stream = await asyncio.open_connection(self.receiver_ip, self.receiver_port)
            self.connection.update({self.receiver_ip: self.receiver_stream})
        _, receiver_writer = self.connection[self.receiver_ip]

        while True:
            # read message. for high load it's better to use memoryview
            message = await reader.read(self.m_size)
            if not message:
                logger.info("Sender received empty message. Waiting for next block.")
                break
            logger.info(f"Sender got a message {bytes(message).decode('utf-8')}")

            receiver_writer.write(message)
            await receiver_writer.drain()

    async def close_connections(self):
        for _, writer in self.connection.values():
            writer.close()


async def sender(cfg):
    ip, port = cfg["SENDER"]["IP"], cfg["SENDER"]["PORT"]
    handler = CreateHandler(cfg)
    server = await asyncio.start_server(handler, ip, port)
    addr = server.sockets[0].getsockname()
    logger.info(f'Sender Serving on {addr}')

    try:
        loop = asyncio.get_event_loop()
        async with server:
            await server.serve_forever()
    except Exception:
        pass
    finally:
        # restart loop on exception
        if not loop.is_running:
            loop.run_forever()
        await handler.close_connections()
        await server.wait_closed()
        logger.info("Sender closed connections")
