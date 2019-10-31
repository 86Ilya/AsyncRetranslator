import asyncio
import json
import logging

from exceptions import UnknownMessage
from safeconnect import SafeConnect

logger = logging.getLogger()


async def register_consumer(parsed_message, consumer_stream, consumer_default_port, white_list, consumers):
    consumer_id = parsed_message["REGISTER_CONSUMER"].get("CONSUMER_ID", None)
    consumer_reader, consumer_writer = consumer_stream
    if not consumer_id:
        logger.error("Consumer id doesn't exist")
        return
    if int(consumer_id) not in white_list:
        logger.error(f"Consumer id {consumer_id} is not listed in white list")
        message = json.dumps({"RESULT": False})
        consumer_writer.write(message.encode())
        consumer_writer.close()
        return
    try:
        ip_addr = consumer_reader._transport.get_extra_info('peername')[0]
        message = json.dumps({"RESULT": True})
        consumer_writer.write(message.encode())
        consumer_writer.close()
        consumers.update({consumer_id: (ip_addr, consumer_default_port)})

        logger.info(f"Registered consumer with id {consumer_id}")
    except Exception as error:
        logger.error(f"Error occured when adding consumer id to storage {error}")


async def dispatch_message_to_one_consumer(message, consumer_addr):
    # _, writer = await asyncio.open_connection(*consumer_addr)
    async with SafeConnect(consumer_addr) as stream:
        _, writer = stream
        writer.write(message)


async def dispatch_message_to_consumers(parsed_message, consumers):
    for consumer, addr in consumers.items():
        asyncio.create_task(dispatch_message_to_one_consumer(parsed_message["RETRANSLATE_MESSAGE"].encode(), addr))

router = {
    "REGISTER_CONSUMER": register_consumer,
    "RETRANSLATE_MESSAGE": dispatch_message_to_consumers,
}


def create_handler(cfg, consumers):
    m_size = cfg["MAX_MESSAGE_SIZE"]
    white_list = cfg["CONSUMERS_WHITE_LIST"]
    consumer_default_port = cfg["CONSUMER_DEFAULT_PORT"]

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
                asyncio.create_task(router["REGISTER_CONSUMER"](parsed_message, (reader, writer), consumer_default_port,
                                                                white_list, consumers))
                return
        except Exception as error:
            logging.error(f"Error occurred when registering a new customer: {error}")
            return

        # retranslate message to consumers
        try:
            if parsed_message.get("RETRANSLATE_MESSAGE", None):
                asyncio.create_task(router["RETRANSLATE_MESSAGE"](parsed_message, consumers))
                return
        except Exception as error:
            logging.error(f"Error occurred when retranslating message to consumers: {error}")
            return

        raise UnknownMessage(parsed_message)

        # message = data.decode()
        # addr = writer.get_extra_info('peername')

        # print(f"Received {message!r} from {addr!r}")

        # print(f"Send: {message!r}")
        # writer.write(data)
        # await writer.drain()

        # print("Close the connection")
        # writer.close()
    return handle_message


async def receiver(cfg):
    receiver_ip = cfg["RECEIVER"]["IP"]
    receiver_port = cfg["RECEIVER"]["PORT"]

    consumers = dict()
    handler = create_handler(cfg, consumers)

    server = await asyncio.start_server(handler, receiver_ip, receiver_port)

    addr = server.sockets[0].getsockname()
    logging.info(f"Receiver serving on {addr}")

    async with server:
        await server.serve_forever()
