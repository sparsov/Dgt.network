import random
import time

class PBFTNode:
    def __init__(self, node_id, all_nodes):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.leader = node_id
        self.round = 0
        self.transactions = []
        self.decisions = {}
        self.total_transactions = 0
        self.successful_transactions = 0

    def send_message(self, receiver_id, message):
        receiver_node = next(node for node in self.all_nodes if node.node_id == receiver_id)
        receiver_node.receive_message(self.node_id, message)

    def receive_message(self, sender_id, message):
        if random.random() < 0.5:
            print(f"Узел {self.node_id} принимает сообщение от узла {sender_id}: {message}")
            self.process_message(sender_id, message)

    def process_message(self, sender_id, message):
        if "operation" in message:
            self.process_operation(sender_id, message["operation"])
        elif "leader_change" in message:
            self.process_leader_change(sender_id, message["leader_change"])
        elif "decision" in message:
            self.process_decision(sender_id, message["decision"])

    def process_operation(self, sender_id, operation):
        print(f"Узел {self.node_id} выполняет операцию: {operation}")
        self.transactions.append(operation)
        self.total_transactions += 1

        if len(self.transactions) % 2 == 0:
            self.request_leader_change()

        if len(self.transactions) >= 2 * len(self.all_nodes) / 3:
            decision = self.decide_consensus()
            if self.node_id == self.leader:
                self.send_decision(decision)
            else:
                leader_node = next(node for node in self.all_nodes if node.node_id == self.leader)
                self.send_message(leader_node.node_id, {"decision": decision})

    def request_leader_change(self):
        if self.leader == self.node_id:
            new_leader_id = random.choice([node.node_id for node in self.all_nodes if node.node_id != self.node_id])
            print(f"Узел {self.node_id} запрашивает смену лидера на узел {new_leader_id}")
            self.send_message(new_leader_id, {"leader_change": new_leader_id})

    def process_leader_change(self, sender_id, new_leader_id):
        if self.leader == sender_id and new_leader_id != self.leader:
            self.change_leader(new_leader_id)

    def change_leader(self, new_leader_id):
        old_leader = self.leader
        self.leader = new_leader_id
        print(f"Узел {self.node_id} сменил лидера. Новый лидер: {self.leader}")

    def decide_consensus(self):
        if len(self.transactions) >= 2 * len(self.all_nodes) / 3:
            consensus_decision = "commit"
            print(f"Узел {self.node_id} достиг консенсуса двух третей голосов. Решение: {consensus_decision}")
            return consensus_decision
        else:
            consensus_decision = "abort"
            return consensus_decision

    def send_decision(self, decision):
        leader_node = next(node for node in self.all_nodes if node.node_id == self.leader)
        self.send_message(leader_node.node_id, {"decision": decision})

    def process_decision(self, sender_id, decision):
        if self.node_id == self.leader:
            print(f"Узел {self.node_id} получил решение от узла {sender_id}: {decision}")
            if decision == "commit":
                print(f"Узел {self.node_id} фиксирует транзакцию.")
                self.decisions[self.round] = "commit"
                self.successful_transactions += 1
            elif decision == "abort":
                print(f"Узел {self.node_id} отклоняет транзакцию.")
                self.decisions[self.round] = "abort"
            self.round += 1

            print(f"Узел {self.node_id}: Общее число транзакций: {self.total_transactions}, Успешные транзакции: {self.successful_transactions}")

    def start(self):
        while True:
            operation = f"Operation from {self.node_id}"
            self.process_operation(self.node_id, operation)
            time.sleep(2)


# Создаем узлы
node1 = PBFTNode(1, [])
node2 = PBFTNode(2, [])
node3 = PBFTNode(3, [])

# Устанавливаем связи между узлами
node1.all_nodes = [node1, node2, node3]
node2.all_nodes = [node1, node2, node3]
node3.all_nodes = [node1, node2, node3]

# Запускаем узлы
node1.start()

