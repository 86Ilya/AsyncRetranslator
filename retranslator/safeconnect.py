import asyncio


class SafeConnect:
    def __init__(self, addr, reconnect_attempts=3, reconnect_wait=5):
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_wait = reconnect_wait
        self.addr = addr

    async def __aenter__(self):
        for i in range(self.reconnect_attempts):
            try:
                self.reader, self.writer = await asyncio.open_connection(*self.addr)
                break
            except ConnectionRefusedError:
                if i < self.reconnect_attempts:
                    await asyncio.sleep(self.reconnect_wait)

            raise Exception(f"Can't connect to server {self.addr}")
        return (self.reader, self.writer)

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            raise Exception(exc)
        else:
            self.writer.close()
            await self.writer.wait_closed()
            return True
