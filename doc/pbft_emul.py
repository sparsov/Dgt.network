import random
import time

class PBFTNode:
    def __init__(self, node_id, all_nodes):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.state = {}  # Состояние узла, например, хранимые данные
        self.leader = None  # Идентификатор текущего лидера
        self.round = 0  # Текущий раунд
        self.votes = {}  # Голоса за смену лидера

    def send_message(self, receiver_node, message):
        # Эмулируем отправку сообщения от одного узла к другому
        receiver_node.receive_message(self, message)

    def receive_message(self, sender_node, message):
        # Эмулируем прием сообщения от другого узла
        # Здесь вы можете реализовать логику обработки сообщения

        # Для примера, случайно решаем, принять ли сообщение
        if random.random() < 0.5:
            print(f"Узел {self.node_id} принимает сообщение от узла {sender_node.node_id}: {message}")
            self.process_message(sender_node.node_id, message)

    def process_message(self, sender_id, message):
        # Обрабатываем полученное сообщение
        # Здесь вы можете реализовать логику выполнения операций и обновления состояния узла
        if "change_leader" in message:
            self.process_change_leader(sender_id, message["change_leader"])
        elif "operation" in message:
            self.process_operation(sender_id, message["operation"])
        elif "vote" in message:
            self.process_vote(sender_id, message["vote"])

    def process_operation(self, sender_id, operation):
        # Проверяем, выполнились ли достаточно операций для запроса на смену лидера
        if len(self.state) % 2 == 0:
            self.request_leader_change()

        # Выполнение операции
        # Здесь вы можете добавить логику выполнения определенной операции и обновления состояния узла
        print(f"Узел {self.node_id} выполняет операцию: {operation}")

        # Пример обновления состояния
        self.state[sender_id] = operation

    def request_leader_change(self):
        # Запрос на смену лидера
        if self.leader == self.node_id:
            new_leader_id = random.choice([node.node_id for node in self.all_nodes if node.node_id != self.node_id])
            print(f"Узел {self.node_id} запрашивает смену лидера. Новый лидер: {new_leader_id}")
            message = {"change_leader": new_leader_id}
            self.send_message(self.all_nodes[0], message)

    def process_change_leader(self, sender_id, new_leader_id):
        # Обработка запроса на смену лидера
        if self.leader == sender_id and new_leader_id != self.leader:
            self.round += 1
            self.votes = {node.node_id: None for node in self.all_nodes}
            self.votes[sender_id] = new_leader_id
            self.send_vote_messages()

    def send_vote_messages(self):
        # Отправка сообщений с голосами за нового лидера
        vote_message = {
            "sender": self.node_id,
            "vote": self.votes[self.node_id]
        }
        for node in self.all_nodes:
            if node != self and self.votes[node.node_id] is None:
                self.send_message(node, vote_message)

        # Проверяем, достигнут ли кворум голосов за нового лидера
        if len([vote for vote in self.votes.values() if vote == self.votes[self.node_id]]) >= (2 / 3) * len(
                self.all_nodes):
            self.change_leader(self.votes[self.node_id])

    def change_leader(self, new_leader_id):
        # Изменение текущего лидера
        old_leader = self.leader
        self.leader = new_leader_id
        print(f"Узел {self.node_id} сменил лидера. Новый лидер: {self.leader}")

        # Сообщение о смене лидера
        print(f"Узел {self.node_id} объявляет смену лидера. Текущий лидер: {old_leader}, Новый лидер: {self.leader}")

    def process_vote(self, sender_id, vote):
        # Обработка полученного голоса
        if sender_id in self.votes and self.votes[sender_id] is None:
            self.votes[sender_id] = vote
            self.send_vote_messages()

    def start(self):
        # Эмулируем запуск узла и начало операций
        while True:
            operation = f"Operation from {self.node_id}"
            self.send_message(self, {"operation": operation})
            time.sleep(2)


# Создаем узлы
node1 = PBFTNode(1, [])
node2 = PBFTNode(2, [node1])
node3 = PBFTNode(3, [node1, node2])

# Обновляем ссылки на все узлы у каждого узла
node1.all_nodes = [node1, node2, node3]
node2.all_nodes = [node1, node2, node3]
node3.all_nodes = [node1, node2, node3]

# Запускаем узлы
node1.start()
node2.start()
node3.start()

