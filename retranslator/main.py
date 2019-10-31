import logging
import asyncio
import json
import argparse

from sender import sender
from receiver import receiver

# default config for main function
default_cfg = {
    "LOGFILE": None,
    "LOGLEVEL": logging.INFO,
    "LOG_FORMAT": "%(asctime)s %(levelname).1s %(message)s",
    "LOG_DATEFMT": "%Y.%m.%d,%H:%M:%S",
    "SENDER": {"IP": "0.0.0.0", "PORT": 7777},
    "RECEIVER": {"IP": "0.0.0.0", "PORT": 8888},
    "MAX_MESSAGE_SIZE": 1024,
    "CONSUMERS_WHITE_LIST": [1, 2, 4],
    "RECONNECT_ATTEMPTS": 3,
    "RECONNECT_WAIT": 5,
    "CONSUMER_DEFAULT_PORT": 6666
}


def update_config_from_file(fname, current_config):
    """
    This function create new config dictionary from
    the data obtained from the configuration file
    """
    tmp_config = current_config.copy()

    loglevel = {
        "INFO": 20,
        "DEBUG": 10,
        "ERROR": 40,
    }

    try:
        with open(fname, 'r') as config_file:
            new_config = json.load(config_file)
            tmp_config.update(new_config)
            tmp_config["LOGLEVEL"] = loglevel[tmp_config["LOGLEVEL"]]

    # we use print here instead of logging, beacause logging not configured yet
    except ValueError as error:
        print('Error parsing config file! {}\n'.format(error))
        return
    except IOError as error:
        print('I/O error during processing {}\n'.format(error))
        return
    return tmp_config


async def main(cfg):
    logging.basicConfig(filename=cfg["LOGFILE"], level=cfg["LOGLEVEL"],
                        format=cfg["LOG_FORMAT"], datefmt=cfg["LOG_DATEFMT"])

    sender_task = asyncio.create_task(sender(cfg))
    asyncio.create_task(receiver(cfg))

    await sender_task


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default=None, nargs='?', help='Path to config file')
    config_file_name = parser.parse_args().config

    # update default cfg with values from config file
    cfg = None
    if config_file_name:
        cfg = update_config_from_file(config_file_name, default_cfg)

    # if we have errors in parsing config file, then we will use default config
    if not cfg:
        cfg = default_cfg

    try:
        asyncio.run(main(cfg))
    except Exception as error:
        logging.exception(error)
    logging.shutdown()
