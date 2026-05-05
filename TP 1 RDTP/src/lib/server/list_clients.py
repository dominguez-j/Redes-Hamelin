from lib.common.client_handler import ClientHandler


class ListClients:
    def __init__(self):
        self.clients: list[ClientHandler] = []

    def addClient(self, client: ClientHandler):
        self.clients.append(client)

    def clear(self):
        self.clients.clear()

    def reap(self):
        self.clients = [client for client in self.clients if client.isAlive()]
