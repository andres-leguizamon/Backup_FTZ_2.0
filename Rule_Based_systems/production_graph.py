import networkx as nx
from typing import List, Dict


# Función auxiliar para obtener nodos de un grafo
def get_nodes(grafo: nx.DiGraph) -> List[str]:
    """Obtiene la lista de nodos en un grafo dirigido.

    Args:
        grafo (nx.DiGraph): Grafo dirigido a obtener nodos.

    Returns:
        List[str]: Lista de nodos en el grafo.
    """
    return list(nx.topological_sort(grafo))


# Función para verificar conexión directa en el grafo
def verificar_conexion_directa(grafo: nx.DiGraph, nodo1: str, nodo2: str) -> bool:
    """Verifica si existe una conexión directa entre dos nodos en un grafo.

    Args:
        grafo (nx.DiGraph): Grafo dirigido a verificar.
        nodo1 (str): Nodo de partida.
        nodo2 (str): Nodo de destino.

    Returns:
        bool: True si existe una conexión directa entre los nodos, False en caso
            contrario.
    """
    return grafo.has_edge(nodo1, nodo2)


# Generar insumos directos para cada nodo
def generar_insumos_directos(grafo: nx.DiGraph) -> Dict[str, List[str]]:
    """
    Genera un diccionario que mapea cada nodo a una lista de nodos
    a los que está directamente conectado en un grafo dirigido.

    Args:
        grafo (nx.DiGraph): Grafo dirigido del cual se obtendrán los insumos.

    Returns:
        Dict[str, List[str]]: Un diccionario donde cada clave es un nodo del grafo
        y su valor es una lista de nodos a los que está directamente conectado.
    """
    nodos = get_nodes(grafo)
    insumos_directos = {}

    for nodo in nodos:
        insumos_directos[nodo] = []
    for nodo1 in nodos:
        for nodo2 in nodos:
            if verificar_conexion_directa(grafo, nodo1, nodo2):
                insumos_directos[nodo2].append(
                    nodo1
                )  # Corregido el nombre de la variable

    return insumos_directos


def generar_productos_directos(grafo: nx.DiGraph) -> Dict[str, List[str]]:
    """
    Genera un diccionario que mapea cada nodo a una lista de nodos
    a los que está directamente conectado en un grafo dirigido.

    Args:
        grafo (nx.DiGraph): Grafo dirigido del cual se obtendrán los insumos.

    Returns:
    """
    nodos = get_nodes(grafo)
    productos_directos = {}

    for nodo in nodos:
        productos_directos[nodo] = []
    for nodo1 in nodos:
        for nodo2 in nodos:
            if verificar_conexion_directa(grafo, nodo1, nodo2):
                productos_directos[nodo1].append(
                    nodo2
                )  # Corregido el nombre de la variable

    return productos_directos


def clasificar_bienes(grafo: nx.DiGraph) -> Dict[str, List[str]]:
    """
    Clasifica los nodos de un grafo de producción en bienes primarios, intermedios o finales.

    Un bien primario es aquel que no tiene insumos; un bien final es aquel que no tiene productos,
    y un bien intermedio es aquel que tiene tanto insumos como productos.

    Args:
        grafo (nx.DiGraph): Grafo dirigido que representa el proceso de producción.

    Returns:
        Dict[str, str]: Un diccionario que mapea cada nodo a su clasificación como "bien_primario",
                        "bien_intermedio" o "bien_final".
    """

    insumos = generar_insumos_directos(grafo)
    productos = generar_productos_directos(grafo)
    clasificacion_bienes = {}

    for nodo in insumos:
        if not insumos[nodo]:
            clasificacion_bienes[nodo] = "bien_primario"
        elif not productos[nodo]:
            clasificacion_bienes[nodo] = "bien_final"
        else:
            clasificacion_bienes[nodo] = "bien_intermedio"

    return clasificacion_bienes


# ------------------------


def get_bienes_primarios(grafo: nx.DiGraph) -> List[str]:
    """
    Devuelve una lista de todos los bienes primarios en el grafo de producción.

    Un bien primario es aquel que no requiere insumos y se produce de la nada.

    Parameters
    ----------
    grafo : nx.DiGraph
        Grafo dirigido de producción.

    Returns
    -------
    List[str]
        Lista de bienes primarios.
    """

    clasificacion_bienes = clasificar_bienes(grafo)
    bienes_primarios = [
        bien
        for bien, clasificacion in clasificacion_bienes.items()
        if clasificacion == "bien_primario"
    ]
    return bienes_primarios


def get_bienes_intermedios(grafo: nx.DiGraph) -> List[str]:
    """
    Devuelve una lista de todos los bienes intermedios en el grafo de producci n.

    Un bien intermedio es un bien que se utiliza para producir al menos otro bien
    y que no es un bien primario (no se produce a partir de la nada).

    Parameters
    ----------
    grafo : nx.DiGraph
        Grafo de producci n.

    Returns
    -------
    List[str]
        Lista de bienes intermedios en el grafo de producci n.
    """
    clasificacion_bienes = clasificar_bienes(grafo)
    bienes_intermedios = [
        bien
        for bien, clasificacion in clasificacion_bienes.items()
        if clasificacion == "bien_intermedio"
    ]
    return bienes_intermedios


def get_bienes_finales(grafo: nx.DiGraph) -> List[str]:
    """
    Devuelve una lista de todos los bienes finales en el grafo de producci n.

    Parameters
    ----------
    grafo : nx.DiGraph
        Grafo dirigido de producci n.

    Returns
    -------
    List[str]
        Lista de bienes finales.
    """
    clasificacion_bienes = clasificar_bienes(grafo)
    bienes_finales = [
        bien
        for bien, clasificacion in clasificacion_bienes.items()
        if clasificacion == "bien_final"
    ]
    return bienes_finales


def cantidad_caminos_x_to_y(grafo: nx.DiGraph, x, y) -> Dict[str, int]:
    """
    Devuelve el n mero de caminos sencillos desde el nodo x hasta el nodo y en el grafo.

    Parameters
    ----------
    grafo : nx.DiGraph
        Grafo dirigido.
    x : str
        Nodo de partida.
    y : str
        Nodo de destino.

    Returns
    -------
    int
        N mero de caminos sencillos desde x hasta y.
    """
    caminos = nx.all_simple_paths(grafo, source=x, target=y)
    return len(list(caminos))


def generar_cantidad_requerida_bienes(grafo: nx.DiGraph) -> Dict[str, int]:
    """
    Devuelve un diccionario con la cantidad inicial de cada bien primario necesario
    para producir un bien final. La cantidad inicial se calcula como el n mero de
    caminos sencillos desde cada bien primario hasta el bien final.

    Parameters
    ----------
    grafo : nx.DiGraph
        Grafo de producci n.

    Returns
    -------
    Dict[str, int]
        Diccionario con la cantidad inicial de cada bien primario.
    """
    cantidad_requerida_bienes = {}
    bienes = get_bienes_primarios(grafo)
    bienes = bienes + get_bienes_intermedios(grafo)
    bien_final = get_bienes_finales(grafo)[0]

    for bien in bienes:
        cantidad_requerida_bienes[bien] = cantidad_caminos_x_to_y(
            grafo, bien, bien_final
        )
    # Agregar el bien final con cantidad 1

    cantidad_requerida_bienes[bien_final] = 1
    return cantidad_requerida_bienes
