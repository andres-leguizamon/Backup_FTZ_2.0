from typing import List, Dict, Any , Optional 
from collections import defaultdict
from abc import ABC, abstractmethod
from production_graph.planner import ProcesoProductivo
import numpy as np
from dataclasses import dataclass , make_dataclass




#------------------------ Economy Exchange of assets classes -----------------------------

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
    def __init__(self, good_type: str, price: float = 0, last_cost: float = 0):
        self.price = price
        self.last_cost = last_cost
        self.good_type = good_type  # Atributo público, sin property por ahora

    def update_price(self, new_price: float):
        self.price = new_price

    def update_cost(self, new_cost: float):
        self.last_cost = new_cost

    def __repr__(self):
        return f"Good(Type: {self.good_type}, Price: {self.price}, Cost: {self.last_cost})"

# --- Estrategia de Gestión de Inventarios ---
class InventoryStrategy(ABC):
    """Interfaz para definir la estrategia de remoción de bienes en el inventario."""
    @abstractmethod
    def select_good(self, goods: List[Good]) -> Optional[Good]:
        """Dado una lista de bienes, devuelve el bien a remover(bien escogido) según la estrategia."""
        pass

class FIFOInventoryStrategy(InventoryStrategy):
    """Implementa la estrategia FIFO: First-In, First-Out."""
    def select_good(self, goods: List[Good]) -> Optional[Good]:
        if goods:
            return goods[0]  # El primero que llegó
        return None

class LIFOInventoryStrategy(InventoryStrategy):
    """Implementa la estrategia LIFO: Last-In, First-Out."""
    def select_good(self, goods: List[Good]) -> Optional[Good]:
        if goods:
            return goods[-1]  # El último que llegó
        return None

# --- Clase de Inventario ---
class PhysicalInventory:
    def __init__(self):
        # Diccionario: clave = tipo de bien (str), valor = lista de Good
        self.inventory = defaultdict(list)

    def add_good(self, unit: Good):
        """Agrega una unidad al inventario."""
        self.inventory[unit.good_type].append(unit)

    def remove_good(self, unit: Good):
        """Remueve una unidad específica del inventario."""
        if unit in self.inventory[unit.good_type]:
            self.inventory[unit.good_type].remove(unit)

    def select_good_by_strategy(self, good_type: str, strategy: InventoryStrategy) -> Optional[Good]:
        """
        Remueve y retorna una unidad del inventario según la estrategia indicada.
        
        Args:
            good_type (str): Tipo de bien a gestionar.
            strategy (InventoryStrategy): Estrategia de remoción (por ejemplo, FIFO o LIFO).
        
        Returns:
            Optional[Good]: La unidad removida o None si no hay unidades disponibles.
        """
        goods = self.inventory[good_type]
        selected_good = strategy.select_good(goods)
        if selected_good is not None:
            return selected_good

    def get_stock_quantity(self, good_type: str) -> List[Good]:
        """Devuelve la lista de unidades de un tipo de bien en el inventario."""
        return len(self.inventory[good_type])
    
    def get_stock(self, good_type: str) -> List[Good]:
        return self.inventory[good_type]
    
    def __repr__(self):
        return f"Inventory({dict(self.inventory)})"

    



class Agent(ABC):
        """Clase abstracta para representar un agente."""
        @property
        def name(self)->str:
            pass 

        @abstractmethod
        def process_order(self, order):
            pass

        
        @abstractmethod
        def get_stock_quantity(self, good_type: str) -> int:
            pass

        @abstractmethod
        def get_stock(self, good_type: str) -> List[Good]:
            pass


# --- Clase base para agentes económicos ---
class EconomyAgent(Agent):
    """Clase para representar un agente económico con inventario."""
    def __init__(self, name: str):
        self._name = name
        self.inventory = PhysicalInventory()

    @property
    def name(self) -> str:
        return self._name


    def get_stock(self, good_type: str) -> List[Good]:
        return self.inventory.get_stock(good_type)
    
    def get_stock_quantity(self, good_type: str) -> List[Good]:
        return self.inventory.get_stock_quantity(good_type)




# --- Agente de mercado ---
class MarketAgent(EconomyAgent):
    """Clase para representar un agente de mercado."""
    def __init__(self, name: str):
        super().__init__(name)
        self._id = 0  # Atributo privado

    @property
    def id(self) -> int:
        return self._id


# --- Firma económica ---
class Firm(EconomyAgent):
    """Clase para representar una firma."""
    contador = 1

    def __init__(self, name: str, inventory_strategy=None):
        super().__init__(name)
        self._id = Firm.contador
        self.inventory_strategy = inventory_strategy or FIFOInventoryStrategy()
        Firm.contador += 1

    @property
    def id(self) -> int:
        return self._id


# --- Subclases de Firm ---
class NctFirm(Firm):
    """Clase para representar una firma de NCT."""
    def __init__(self, name: str):
        super().__init__(name)



class ZfFirm(Firm):
    """Clase para representar una firma de ZF."""
    def __init__(self, name: str):
        super().__init__(name)



#----------------------------- Data Strucuture For Orders -------------------------

class PriceMatrix:
    def __init__(self, matrix: np.ndarray):
        self.matrix = np.ndarray

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



###!------------------------------------------------------------------------------------ Order Complementary Information Creation --------------------------------------

# Price Lookup 

class PriceLookupStrategy(ABC):
    @abstractmethod
    def get_price(self, good_type: str) -> float:
        pass


class PriceMatrixLookup(PriceLookupStrategy):
    def __init__(self, price_matrix: PriceMatrix, agent_indexes: Dict):
        self.price_matrix = price_matrix.matrix
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
    def __init__(self, price_strategy:PriceLookupStrategy, production_strategy:ProductionLookupStrategy):
        self.price_strategy = price_strategy
        self.production_strategy = production_strategy
        pass

    def generate_additional_information(self,order:Order):
        price = self.price_strategy.get_price(order)
        production_info = self.production_strategy.get_production_info(order.good_type)

        order.complementary_info["price"] = price
        order.complementary_info["production_info"] = production_info


class ProductionOrderAdditionalInfoGenerator(OrderAdditionalInfoGeneratorStrategy):
    def __init__(self, production_strategy:ProductionLookupStrategy):
        self.production_strategy = production_strategy
        pass

    def generate_additional_information(self,order:Order):
        production_info = self.production_strategy.get_production_info(order.good_type)
        order.complementary_info["production_info"] = production_info

        


class OrderAdditionalInfoGenerator:
    def __init__(self, price_strategy: PriceLookupStrategy, production_strategy: ProductionLookupStrategy):
        self.price_strategy = price_strategy
        self.production_strategy = production_strategy

    def get_strategy_for_order_type(self, order_type: str) -> OrderAdditionalInfoGeneratorStrategy:
        if order_type == "comprar":
            return BuyerOrderAdditionalInfoGenerator(self.price_strategy, self.production_strategy)
        elif order_type == "produccion":
            return ProductionOrderAdditionalInfoGenerator(self.production_strategy)
        else:
            raise ValueError(f"Unknown order_type: {order_type}")

    def generate_info(self, order: Order):
        strategy = self.get_strategy_for_order_type(order.order_type)
        strategy.generate_additional_information(order)

#!------------------------------------------------- Order Execution ------------------------------------------------




# ---------------------Buscador de agentes para realizar los intercambios -------------------------------

class AgentLookupStrategy(ABC):
    @abstractmethod
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        pass

class EconomyAgentListLookup(AgentLookupStrategy):
    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        raise ValueError ("Agent not found in Agents List")  
    

#! ----------------------------------------- Interface Mediator to execute the orders and generate the transactions -----------------------------------------




# Dataclass Para generar una configuración general de la economía. 

@dataclass
class EconomyConfig:
    production_graph: ProcesoProductivo
    price_matrix: PriceMatrix
    agent_indexes: Dict
    price_strategy: PriceLookupStrategy
    production_strategy: ProductionLookupStrategy
    agent_lookup_strategy: AgentLookupStrategy


#--------------------- Specific Order Execution Strategies --------------------------------




class OrderValiadationStrategy(ABC):
    @abstractmethod
    def validate_order(self, order:Order):
        pass


class BuyOrderValidation(OrderValiadationStrategy):
    def __init__(self, config:EconomyConfig):
        super().__init__()
        self.config = config
        self.info_generator = OrderAdditionalInfoGenerator(self.config.price_strategy, self.config.production_strategy)
        pass

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        return self.config.agent_lookup_strategy.get_agent(agent_name)
    
    def validate_order(self, order:Order):
        buyer_name = order.agents[0]
        seller_name = order.agents[1]
        buyer = self.get_agent(buyer_name)
        seller = self.get_agent(seller_name)


        if seller.get_stock_quantity(order.good_type)
            raise ValueError ("No hay stock suficiente para la que el vendedor pueda vender")

        pass



class OrderExecutionStrategy(ABC):
    @abstractmethod
    def execute_order(order:Order):
     """
        Executes an order and generates the transaction.
    
        Args:
            order (Order): The order to execute.
    
        Returns:
            None
        """
    pass


class ProductionOrderExecution(OrderExecutionStrategy):
    def __init__(self, config:EconomyConfig):
        super().__init__()
        self.config = config

    def execute_order(order:Order):
        pass


class BuyerOrderExecution(OrderExecutionStrategy):
    def __init__(self, config:EconomyConfig):
        super().__init__()
        self.config = config
    def execute_order(order:Order):
        pass


class OrderExecutor:
    def __init__(self, config:EconomyConfig):
        self.config = config
        self.info_generator = OrderAdditionalInfoGenerator(self.config.price_strategy, self.config.production_strategy)
    
    def generate_info(self, order: Order):
        self.info_generator.generate_info(order)


