from grammatron import *
from unittest import TestCase

import matplotlib.pyplot as plt
import networkx as nx

def draw_graph(graph):
    pos = nx.circular_layout(graph)

    # Не рисуем лейблы узлов, только сами узлы
    nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue')

    # Рисуем рёбра
    nx.draw_networkx_edges(graph, pos, arrows=True)

    # Подписи рёбер (label)
    edge_labels = {(u, v): d.get('label', '') for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10)

    plt.axis('off')
    plt.tight_layout()

    plt.savefig('graph.png', format='png', dpi=300)
    plt.close()

class SmartGraphBuildingTestCase(TestCase):
    def test_smart_building(self):
        options = ['пятый', 'пятая', 'пятое', 'пятого','пятому','пятом']
        template = Template(f'{OptionsDub(options).as_variable("options")}')
        parser = AStarParser(template.dub)
        draw_graph(parser.data.graph)

