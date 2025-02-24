from typing import List, Dict, Any 
from collections import defaultdict
from abc import ABC, abstractmethod
from production_graph.planner import ProcesoProductivo
import numpy as np
from dataclasses import dataclass , make_dataclass




#------------------------ Economy Exchange of assets classes -----------------------------
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



#----------------------------- Data Strucuture For Orders -------------------------


@dataclass
class Order:
    time: int
    agents: List[Agent]
    order_type: str
    good_type: str
    complementary_info: Dict[str, Any] # Allows to dynamically add information

class OrderInterpretationStrategy(ABC):
    @abstractmethod
    def interpret_order(self, order) -> "Order":
        """
        Interpreta una orden y la devuelve como una instancia de la clase Order.
        
        Args:
            order (tuple): Tupla que contiene la orden a interpretar.
                Debe contener (en orden) el tiempo, agentes involucrados, tipo de orden y tipo de bien.
        Returns:
            Order: Instancia de la clase Order con la orden interpretada.
        """
        pass

class TupleOrderInterpreter(OrderInterpretationStrategy):
    def interpret_order(self, order: tuple) -> "Order":
        # Unpack the tuple and create an Order instance
        time, agents, order_type, good_type = order
        return Order(time, agents, order_type, good_type)

class OrderInterpreter:
    def __init__(self, strategy: OrderInterpretationStrategy = TupleOrderInterpreter()):
        # Default to the tuple strategy if none is provided

        self._strategy = strategy

    def interpret_order(self, order) -> "Order":
        # Delegate to the strategy
        return self._strategy.interpret_order(order)



###---------------------------- Order Complementary Information Creation -----------------

# Price Lookup 

class PriceLookupStrategy(ABC):
    @abstractmethod
    def get_price(self, good_type: str) -> float:
        pass


class PriceMatrixLookup(PriceLookupStrategy):
    def __init__(self, price_matrix: np.ndarray, agent_indexes: Dict):
        self.price_matrix = price_matrix
        self.agent_indexes = agent_indexes

    def get_price(self, order: Order) -> float:
        buyer = order.agents[0]
        seller = order.agents[1]

        if buyer and seller in self.agent_indexes:
           price = self.price_matrix[self.agent_indexes[buyer], self.agent_indexes[seller]]
           return price
        else:
            raise ValueError ("Buyer or seller not found in agent indexes")



# ---------------------------------- Production process Lookup 

class ProductionLookupStrategy(ABC):
    @abstractmethod
    def get_production_info(self, good_type: str) -> float:
        pass


class PGraphProductionLookup(ProductionLookupStrategy):
    def __init__(self, production_graph: ProcesoProductivo):
        self.production_graph = production_graph

    def get_inputs(self, good_type: str) -> List[str]:
        return self.production_graph.get_insumos(good_type)

    def get_outputs(self, good_type: str) -> List[str]:
        return self.production_graph.get_productos(good_type)
    
    def get_production_info(self, good_type: str) -> Dict[str:list]:
        inputs = self.get_inputs(good_type)
        outputs = self.get_outputs(good_type)
        return {"inputs": inputs, "outputs": outputs}




# -------------------------- Mediator Interface to add the additional information 

class OrderAdditionalInfoGeneratorStrategy(ABC):
    @abstractmethod
    def generate_additional_information(self,order:Order):        
        pass


class BuyerOrderAdditionalInfoGenerator(OrderAdditionalInfoGeneratorStrategy):
    def __init__(self, price_strategy:PriceLookupStrategy=PriceMatrixLookup(), production_strategy:ProductionLookupStrategy=PGraphProductionLookup()):
        self.price_strategy = price_strategy
        self.production_strategy = production_strategy
        pass

    def generate_additional_information(self,order:Order):
        price = self.price_strategy.get_price(order)
        production_info = self.production_strategy.get_production_info(order.good_type)

        order.complementary_info["price"] = price
        order.complementary_info["production_info"] = production_info


class ProductionOrderAdditionalInfoGenerator(OrderAdditionalInfoGeneratorStrategy):
    def __init__(self, production_strategy:ProductionLookupStrategy=PGraphProductionLookup()):
        self.production_strategy = production_strategy
        pass

    def generate_additional_information(self,order:Order):
        production_info = self.production_strategy.get_production_info(order.good_type)
        order.complementary_info["production_info"] = production_info

        


class OrderAdditionalInfoGenerator:
    """Mediator that selects the appropriate additional info strategy for an order."""

    def __init__(self, price_strategy: PriceLookupStrategy, production_strategy: ProductionLookupStrategy):
        self.price_strategy = price_strategy
        self.production_strategy = production_strategy

    def generate_info(self, order: Order):
        """Selects and applies the correct strategy based on order_type."""

        if order.order_type == "buyer":
            strategy = BuyerOrderAdditionalInfoGenerator(self.price_strategy, self.production_strategy)
        elif order.order_type == "production":
            strategy = ProductionOrderAdditionalInfoGenerator(self.production_strategy)
        else:
            raise ValueError(f"Unknown order_type: {order.order_type}")

        # Apply the strategy
        strategy.generate_additional_information(order)
