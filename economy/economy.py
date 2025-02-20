from typing import List, Dict
from collections import defaultdict
from abc import ABC, abstractmethod
from production_graph.planner import ProcesoProductivo
import numpy as np
from dataclasses import dataclass

class PriceMatrix:
    def __init__(self, matrix: np.ndarray):
        self.matrix = np.ndarray

class Asset(ABC):
    """Clase abstracta para representar un activo."""
    @abstractmethod
    def update_price(self, new_price: float):
        pass

    @abstractmethod
    def update_cost(self, new_cost: float):
        pass

class Good(Asset):
    """Clase que representa una unidad de bien con precio y costo histórico."""
    def __init__(self, price: float, last_cost: float, good_type: str):
        self.price = price
        self.last_cost = last_cost
        self.good_type = good_type  # Atributo público, sin property por ahora

    def update_price(self, new_price: float):
        self.price = new_price

    def update_cost(self, new_cost: float):
        self.last_cost = new_cost

    def __repr__(self):
        return f"Good(Tipo: {self.good_type}, Precio: {self.price}, Costo: {self.last_cost})"

class Inventory:
    def __init__(self):
        # Diccionario: clave = tipo de bien (str), valor = lista de Good
        self.inventory = defaultdict(list)

    def add_good(self, unit: Good):
        """Agrega una unidad al inventario.
        
        Args:
            unit (Good): Unidad de bien a agregar.
        """
        self.inventory[unit.good_type].append(unit)

    def remove_good(self, unit: Good):
        # Solo lo removemos si existe en la lista correspondiente
        """Remueve una unidad del inventario.
        
        Solo lo removemos si existe en la lista correspondiente.
        
        Args:
            unit (Good): Unidad de bien a remover.
        """
        if unit in self.inventory[unit.good_type]:
            self.inventory[unit.good_type].remove(unit)

    def get_stock(self, good_type: str) -> List[Good]:
        """Devuelve la lista de unidades de un tipo de bien en el inventario.
        
        Args:
            good_type (str): Tipo de bien a buscar en el inventario.
        
        Returns:
            List[Good]: Lista de unidades de ese tipo de bien.
        """
        return self.inventory[good_type]
    
    def __repr__(self):
        return f"Inventory({dict(self.inventory)})"
    


class Agent(ABC):
        """Clase abstracta para representar un agente."""
        @abstractmethod
        def process_order(self, order):
            pass



class MarketAgent(Agent):
        """Clase para representar un agente de mercado."""        
        def __init__(self, name: str):
            self.name = name
            self.inventory = Inventory()
            self.index = 0
            self.id = 0  # Atributo privado


class Firm(Agent):
        """Clase para representar una firma."""
        contador = 1
        def __init__(self, name: str):
            self.name = name
            self.inventory = Inventory()
            self.id = Firm.contador
            Firm.contador += 1

class NctFirm(Firm):
        """Clase para representar una firma de NCT."""
        def __init__(self, name: str):
            super().__init__(name)
            self.index = 1

class ZfFirm(Firm):
        """Clase para representar una firma de ZF."""
        def __init__(self, name: str):
            super().__init__(name)
            self.index = 2






@dataclass
class Transaction:
    buyer: "MarketAgent"
    seller: "MarketAgent"
    good_type: str
    price: float
    quantity: int
    # Otros campos si los necesitas
            