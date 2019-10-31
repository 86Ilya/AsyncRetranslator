import socket


def test_sender(retranslator_server, base_config):

    inet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # if it's impossible to connect then error will be raised
    inet_socket.connect(("127.0.0.1", base_config["SENDER"]["PORT"]))
    return retranslator_server


def test_receiver(retranslator_server, base_config):
    inet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # if it's impossible to connect then error will be raised
    inet_socket.connect(("127.0.0.1", base_config["RECEIVER"]["PORT"]))
    return retranslator_server
