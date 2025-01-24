import networkx as nx
import numpy as np
from typing import List, Dict, Tuple
import production_graph as pg


class Agente:
    id = 0

    def __init__(self, nombre, inventario: Dict[str, List[str]]):
        self._nombre = nombre
        self._id = Agente.id
        Agente.id += 1
        self._inventario = inventario

    def __getattribute__(self, name):
        # Si el atributo existe en la clase, devuélvelo normalmente
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            # Si no existe, devolver el mensaje personalizado
            return f"El agente {self._id} no tiene el atributo {name}"

    def agregar_inventario(self, bien, activo):
        if bien in self._inventario:
            self._inventario[bien].append(activo)
        else:
            self._inventario[bien] = [activo]

    def eliminar_inventario(self, bien, activo):
        if bien in self._inventario:
            self._inventario[bien].remove(activo)
            if len(self._inventario[bien]) == 0:
                del self._inventario[bien]
        else:
            print(f"El agente {self._id} no tiene el bien {bien}")


class Proceso_productivo:
    def __init__(self, pgraph: nx.DiGraph):
        """
        Inicializa un objeto Proceso_productivo con un grafo de producción.

        Args:
            pgraph (nx.DiGraph): Grafo de producción.

        Attributes:
            _insumos_directos (Dict[str, List[str]]): Diccionario que mapea cada nodo a una lista de nodos
                a los que está directamente conectado en un grafo dirigido.
            _productos_directos (Dict[str, List[str]]): Diccionario que mapea cada nodo a una lista de nodos
                a los que está directamente conectado en un grafo dirigido.
            _clasificacion_bienes (Dict[str, str]): Diccionario que mapea cada nodo a una lista de nodos
                clasificados en "bien_primario", "bien_intermedio" o "bien_final".
        """
        self._pgraph = pgraph

        self._insumos_directos = pg.generar_insumos_directos(self._pgraph)

        self._productos_directos = pg.generar_productos_directos(self._pgraph)

        self._clasificacion_bienes = pg.clasificar_bienes(self._pgraph)  # diccionario

        self.cantidades_requeridas = pg.generar_cantidad_requerida_bienes(self._pgraph)

    def get_insumos(self, bien):
        return self._insumos_directos[bien]

    def get_grafo(self):
        """
        Devuelve el grafo de producción que se utiliza en el Proceso_productivo.

        Returns
        -------
        nx.DiGraph
            Grafo de producción
        """
        return self._pgraph

    def crear_plan_produccion(self, plan: List[int]):
        action_map = {
            "bien_primario": "comprar",
            "bien_intermedio": "producir",  # Mapeo de acciones dependiendo el tipo de bien
            "bien_final": "producir",
        }
        agent_map = {1: "NCT", 0: "ZF"}  # mapeo de Agente

        #### Cálculo del número de pasos requeridos
        requerimientos = sum(self.cantidades_requeridas.values())

        # Validación de la longitud del plan
        if len(plan) < requerimientos:
            raise ValueError(
                "El plan debe tener al menos un elemento por cada paso necesario"
            )
        plan_produccion = []  # Aqui se almacenara la lista de transacciones

        position = 0

        # Asignación de compras de bienes primarios
        for bien, cantidad in self.cantidades_requeridas.items():
            if self._clasificacion_bienes[bien] == "bien_primario":
                for _ in range(cantidad):
                    plan_produccion.append(
                        (
                            bien,
                            action_map[self._clasificacion_bienes[bien]],
                            agent_map[plan[position]],
                        )
                    )
                    position += 1

        # Asignación de producciones para bienes intermedios / finales

        for bien, cantidad in self.cantidades_requeridas.items():
            if self._clasificacion_bienes[bien] in ["bien_intermedio", "bien_final"]:
                for _ in range(cantidad):
                    plan_produccion.append(
                        (
                            bien,
                            "producir",
                            agent_map[plan[position]],
                        )
                    )
                    position += 1

        return plan_produccion


def cortar_lista(
    lista: List[Tuple[str, str, str]], orden: str, primera_parte: bool
) -> List[Tuple[str, str, str]]:
    """
    Corta la lista en la última aparición de la acción indicada.

    Args:
        lista (List[Tuple[str, str, str]]): Lista de órdenes.
        orden (str): Acción en la cual se debe cortar la lista.
        primera_parte (bool): Si es True, retorna la primera parte hasta la última aparición de 'orden'.
                              Si es False, retorna la segunda parte después de la última aparición de 'orden'.

    Returns:
        List[Tuple[str, str, str]]: Lista cortada según la opción seleccionada.
    """
    for i in range(len(lista) - 1, -1, -1):
        if lista[i][1] == orden:
            return lista[: i + 1] if primera_parte else lista[i + 1 :]

    print("No se encontró la orden en la lista.")
    return lista  # Si no se encuentra "orden", devolver la lista original


class Planner:
    def __init__(self, proceso_productivo):
        self._proceso_productivo = proceso_productivo
        self.cantidades_requeridas = self._proceso_productivo.cantidades_requeridas
        self.clasificacion_bienes = self._proceso_productivo._clasificacion_bienes
        # Inicializar al mercado con los bienes primarios
        self._mercado = Agente("MKT", {})

        for bien, cantidad in self.cantidades_requeridas.items():
            if self.clasificacion_bienes[bien] == "bien_primario":
                for i in range(1, cantidad + 1):
                    self._mercado.agregar_inventario(bien, f"unidad_{i}")

        # Inicializar los agentes
        self._agentes = {
            "NCT": Agente("NCT", {}),
            "ZF": Agente("ZF", {}),
            "MKT": self._mercado,
        }

        # Inicializar la secuencia de transacciones
        self.transacciones = []

    def reset(self):
        """
        Reinicia el estado del Planner, eliminando todos los bienes comprados /
        producidos y volviendo a inicializar los agentes y el mercado con los
        bienes primarios iniciales.
        """
        self.__init__(self._proceso_productivo)

    def procesar_compra(self, orden: Tuple[str, str, str]):
        """
        Procesa una orden de compra en la forma (Bien, "comprar", Agente).
        Busca un vendedor que tenga el bien en su inventario y transfiere
        la primera unidad disponible al agente comprador.

        Args:
            orden (Tuple[str, str, str]): Tupla en la forma (bien, accion, agente).

        Raises:
            ValueError: Si la acción no es "comprar" o si ningún agente tiene
                        el bien disponible para vender.
        """
        bien, accion, agente = orden

        if accion != "comprar":
            raise ValueError("La orden debe ser de tipo 'comprar'.")

        # Buscar en todos los agentes quién tiene el bien disponible
        vendedor_encontrado = None
        # Filtrar los agentes excluyendo la clave específica
        posibles_vendedores = {k: v for k, v in self._agentes.items() if k != agente}
        for nombre_agente, objeto_agente in posibles_vendedores.items():
            if bien in objeto_agente._inventario and objeto_agente._inventario[bien]:
                vendedor_encontrado = nombre_agente
                break

        if vendedor_encontrado:
            # Transferir la primera unidad disponible del vendedor al comprador
            unidad = self._agentes[vendedor_encontrado]._inventario[bien][0]
            self._agentes[vendedor_encontrado].eliminar_inventario(bien, unidad)
            self._agentes[agente].agregar_inventario(bien, unidad)

            # Registrar la transacción en formato ((comprador,vendedor), "compra", bien)
            self.transacciones.append(
                (
                    (
                        agente,
                        vendedor_encontrado,
                    ),
                    "compra",
                    bien,
                )
            )
        else:
            raise ValueError(f"Ningún agente tiene '{bien}' disponible para vender.")

    def procesar_produccion(self, orden: Tuple[str, str, str]):
        """
        Procesa una orden de producción en la forma (Bien, "producir", Agente).
        Antes de producir, valida que el agente tenga todos los insumos requeridos.
        Si no los tiene, intenta comprarlos de manera recursiva llamando a
        'procesar_orden' para cada insumo faltante.

        Args:
            orden (Tuple[str, str, str]): Tupla en la forma (bien, accion, agente).

        Raises:
            ValueError: Si la acción no es "producir".
        """
        bien, accion, agente = orden

        if accion != "producir":
            raise ValueError("La orden debe ser de tipo 'producir'.")

        # Obtener los insumos necesarios para producir este bien
        insumos_necesarios = self._proceso_productivo._insumos_directos[bien]

        # Verificar y/o comprar insumos antes de producir
        for insumo in insumos_necesarios:
            # Si el agente no tiene el insumo en su inventario (o no tiene unidades),
            # procedemos a hacer la compra de manera recursiva.
            if (
                insumo not in self._agentes[agente]._inventario
                or not self._agentes[agente]._inventario[insumo]
            ):
                self.procesar_orden((insumo, "comprar", agente))

        # Una vez que tiene los insumos, se agrega el bien producido al inventario
        self._agentes[agente].agregar_inventario(bien, f"unidad_{bien}")

        # Consumir (eliminar) una unidad de cada insumo
        for insumo in insumos_necesarios:
            unidad_insumo = self._agentes[agente]._inventario[insumo][0]
            self._agentes[agente].eliminar_inventario(insumo, unidad_insumo)

        # Registrar la transacción de producción
        # Estructura de ejemplo: ((agente, ), "producción", bien)
        # o algún formato que te resulte conveniente.
        self.transacciones.append(((agente,), "producción", bien))

    def procesar_orden(self, orden: Tuple[str, str, str]):
        """
        Dado un orden en la forma (bien, accion, agente), delega el procesamiento
        a 'procesar_compra' o 'procesar_produccion' según corresponda.

        Args:
            orden (Tuple[str, str, str]): Tupla en la forma (bien, accion, agente).

        Raises:
            ValueError: Si la acción no es reconocida.
        """
        bien, accion, agente = orden

        if accion == "comprar":
            self.procesar_compra(orden)
        elif accion == "producir":
            self.procesar_produccion(orden)
        else:
            raise ValueError(f"Acción no reconocida: {accion}")

    def ejecutar_plan(self, plan: List[Tuple[str, str, str]]):
        """
        Ejecuta un plan de producción procesando cada orden.

        Args:
            plan_produccion (List[Tuple[str, str, str]]): Lista de órdenes.
        """
        Planner.reset(self)
        plan_produccion = self._proceso_productivo.crear_plan_produccion(plan)
        parte_1_secuencia = cortar_lista(plan_produccion, "comprar", 1)
        parte_2_secuencia = cortar_lista(plan_produccion, "comprar", 0)

        for orden in parte_1_secuencia:
            self.procesar_orden(orden)

        for orden in parte_2_secuencia:
            self.procesar_orden(orden)

        return self.transacciones