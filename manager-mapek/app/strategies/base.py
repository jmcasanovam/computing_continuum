from abc import ABC, abstractmethod

class NodeSelectionStrategy(ABC):
    @abstractmethod
    def select_node(self, nodes_info):
        pass