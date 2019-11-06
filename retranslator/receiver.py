import asyncio
import json
import logging
import socket

from exceptions import UnknownMessage

logger = logging.getLogger()


class MessageDispatcher:
    consumers = dict()

    async def register_consumer(self, parsed_message, consumer_writer, white_list):
        consumer_id = parsed_message["REGISTER_CONSUMER"].get("CONSUMER_ID", None)
        if not consumer_id:
            logger.error("Consumer id doesn't exist")
            return
        if int(consumer_id) not in white_list:
            logger.error(f"Consumer id {consumer_id} is not listed in white list")
            message = json.dumps({"RESULT": False}).encode()
            consumer_writer.write(message)
            await consumer_writer.drain()
            return
        try:
            message = json.dumps({"RESULT": True}).encode()
            consumer_writer.write(message)
            await consumer_writer.drain()

            self.consumers.update({consumer_id: consumer_writer})

            logger.info(f"Registered consumer with id {consumer_id}")
        except Exception as error:
            logger.error(f"Error occured when adding consumer id to storage {error}")

    async def dispatch_message_to_consumers(self, parsed_message):

        for consumer_writer in self.consumers.values():
            message = parsed_message["RETRANSLATE_MESSAGE"]
            if isinstance(message, list):
                message = "\n".join(message)
            consumer_writer.write(message.encode())
            await consumer_writer.drain()

    async def close_connections(self):
        for consumer_writer in self.consumers.values():
            consumer_writer.close()
            await consumer_writer.wait_closed()


def create_handler(cfg, router):
    m_size = cfg["MAX_MESSAGE_SIZE"]
    white_list = cfg["CONSUMERS_WHITE_LIST"]

    async def handle_message(reader, writer):
        message = await reader.read(m_size)
        try:
            parsed_message = json.loads(message)
        except Exception:
            logging.error(f"Error parse message {message}")
            return

        # process registration request message
        try:
            if parsed_message.get("REGISTER_CONSUMER", None):

                # writer is needed to send answer to consumer
                await router["REGISTER_CONSUMER"](parsed_message, writer, white_list)
                return
        except Exception as error:
            logging.error(f"Error occurred when registering a new customer: {error}")
            return

        # retranslate message to consumers
        try:
            if parsed_message.get("RETRANSLATE_MESSAGE", None):
                await router["RETRANSLATE_MESSAGE"](parsed_message)
                return
        except Exception as error:
            logging.error(f"Error occurred when retranslating message to consumers: {error}")
            return

        raise UnknownMessage(parsed_message)

    return handle_message


async def receiver(cfg):
    receiver_ip = cfg["RECEIVER"]["IP"]
    receiver_port = cfg["RECEIVER"]["PORT"]

    dispatcher = MessageDispatcher()

    router = {"REGISTER_CONSUMER": dispatcher.register_consumer,
              "RETRANSLATE_MESSAGE": dispatcher.dispatch_message_to_consumers}
    handler = create_handler(cfg, router)

    server = await asyncio.start_server(handler, receiver_ip, receiver_port)

    # set tcp options for keep alive connection
    sock = server.sockets[0]
    addr = sock.getsockname()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, cfg["TCP_IDLE_SEC"])
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, cfg["TCP_INTERVAL_SEC"])
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, cfg["TCP_MAX_RECONNECT_FAILS"])
    logging.info(f"Receiver serving on {addr}")

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
        await dispatcher.close_connections()
        await server.wait_closed()
        logger.info("Receiver closed connections")
