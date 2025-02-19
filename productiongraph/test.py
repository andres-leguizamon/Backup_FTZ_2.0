import networkx as nx
import importlib
from collections import deque
import matplotlib.pyplot as plt
import production_graph as pg
import planner as pln


# Ejemplo de uso:
G = nx.DiGraph()
G.add_edges_from(
    [
        ("A", "C"),
        ("B", "C"),
        ("C", "D"),
        ("C", "E"),
        ("D", "F"),
        ("D", "G"),
        ("F", "K"),
        ("G", "K"),
        ("E", "K"),
    ]
)


proceso = pln.Proceso_productivo(G)


plan = [0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0]

planeador = pln.Planner(proceso)

planeador.ejecutar_plan(plan)
