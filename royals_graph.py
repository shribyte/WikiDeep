"""
This module contains our blood relationship graph implementation.
"""
from __future__ import annotations

import os
import time
import datetime
import pickle
from typing import Any, Tuple, Optional

import networkx as nx
from plotly.graph_objs import Scatter, Figure
from wiki_extract import WikiExtract


class RoyalsGraph:
    """A graph of blood relationships between European royals in history."""
    # Private Instance Attributes:
    #     - _royals:
    #         A collection of the royals contained in this graph.
    #         Maps wiki ids to _Royal objects.
    _royals: dict[str, _Royal]

    def __init__(self) -> None:
        """Initialize an empty royals graph (no royals or edges)."""
        self._royals = {}

    ################################################################################################
    # Utility methods
    ################################################################################################
    def add_royal(self, wiki_id: str, name: str) -> None:
        """Add a royal with the given id and name to this graph and
        query wikidata for birth_year.

        The new royal is not adjacent to any other royals.
        """
        if wiki_id not in self._royals:
            birth_years = WikiExtract.get_birthdate(wiki_id)

            # These are a bunch of sanity checks since wikidata is weird
            if isinstance(birth_years, list) and len(birth_years) > 0:
                birth_year_str = birth_years[0]

                if isinstance(birth_year_str, str) and len(birth_year_str) >= 4 \
                        and birth_year_str[:4].isdigit():
                    birth_year = int(birth_year_str[:4])
                else:
                    birth_year = -1
            else:
                # Set to -1 if no valid birth date given
                birth_year = -1

            self._royals[wiki_id] = _Royal(wiki_id, name, birth_year)

    def add_royal_with_birth_year(self, wiki_id: str, name: str, birth_year: int) -> None:
        """Add a royal with the given id and name to this graph with specified birth_year.

        The new royal is not adjacent to any other royals.
        """
        if wiki_id not in self._royals:
            self._royals[wiki_id] = _Royal(wiki_id, name, birth_year)

    def add_edge(self, parent_id: Any, child_id: Any) -> None:
        """Add an edge between the a parent royal and child royal with the given ids in this graph.

        Raise a ValueError if parent_id or child_id do not appear as royals in this graph.

        Preconditions:
            - parent_id != child_id
        """
        if parent_id in self._royals and child_id in self._royals:
            parent = self._royals[parent_id]
            child = self._royals[child_id]

            # Add the new edge
            parent.children.add(child)
            child.parents.add(parent)
        else:
            # We didn't find an existing royal for both items.
            raise ValueError

    def get_royal(self, wiki_id: str) -> Optional[_Royal]:
        """Get the _Royal with wiki_id from self._royals.

        Raise ValueError if wiki_id not in the graph.
        """
        if wiki_id in self._royals:
            return self._royals[wiki_id]
        else:
            raise ValueError

    def get_all_ids(self) -> list[str]:
        """Return a list of all wiki ids in the graph."""
        return list(self._royals.keys())

    def get_all_royals(self) -> list[_Royal]:
        """Return a list of all _Royal objects (vertices) in graph."""
        return list(self._royals.values())

    def get_ids_for_name(self, name: str) -> list[str]:
        """Return a list of wiki ids in this graph whose associated _Royal have the same name."""
        wiki_ids_for_name = []
        for wiki_id in self._royals:
            v = self._royals[wiki_id]

            if v.name == name:
                wiki_ids_for_name.append(wiki_id)

        return wiki_ids_for_name

    def save(self) -> None:
        """Save this graph in a pickle file."""
        if not os.path.exists('graph_files/'):
            os.makedirs('graph_files/')

        num_royals = len(self._royals)
        date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file = open(f'graph_files/{date_time}_RoyalsGraph_{num_royals}royals', 'wb')
        pickle.dump(self, file)

    @staticmethod
    def load() -> RoyalsGraph:
        """Load and return a graph from a pickle file."""
        if not os.path.exists('graph'):
            raise ValueError(f'File \'graph\' DNE')

        file = open('graph', 'rb')
        graph_loaded = pickle.load(file)
        return graph_loaded

    ################################################################################################
    # Graph creation
    ################################################################################################
    def fill_graph(self, root_names: set,
                   max_depth: int) -> None:
        """Fill this graph with royals based on a set of staring royals' names.

        Args:
            root_names: Names of royals to initialize in the graph.
            max_depth: Max depth (number of edges) away from root royals
                that will be stored in graph.
        """
        # royals_queue is a queue of tuples. Each tuple contains information about a royal
        # who has been added as a node to the graph but whose children and parents have yet to
        # all be added. Each royal is removed from royals_queue and added to royals_added
        # once all the royal's children and parents are added and the edges between them are formed.
        royals_queue = []
        royals_added = set()

        # Counter for knowing when to save the graph
        counter = 0

        # Initialize graph with the royals in root_names
        for name in root_names:
            wiki_id = WikiExtract.get_wikidata_id(name.strip())

            if wiki_id is not None:
                self.add_royal(wiki_id, name)

                royals_queue.append((0, wiki_id, name))

        while len(royals_queue) > 0:
            # Save graph about every 100 added royals
            if len(self._royals) - counter > 100:
                self.save()
                counter = len(self._royals)

            # curr_depth: number of edges away from the associated root royal
            # curr_id, curr_name: id and name of current royal
            curr_depth, curr_id, curr_name = royals_queue.pop(0)
            # print(f'Current: {curr_name}')

            # After this point, curr_depth is the distance of the parents/children
            # of the current royal to the associated root royal.
            curr_depth += 1

            if curr_depth <= max_depth:
                self.add_children_parents(curr_id, curr_depth, royals_queue, royals_added, None)

        self.save()

    def add_children_parents(self, curr_id: str, curr_depth: int,
                             royals_queue: list, royals_added: set,
                             base_graph: Optional[RoyalsGraph]) -> None:
        """Add the curr_id royal's children and parents to this graph.

        Mutates royals_queue & royals_added according to comments here
        and comments in self.fill_graph.

        If base_graph is not None, children and parent IDs, names, and birth years
        will be extracted from this base graph, not from wikipedia.

        Preconditions:
            - base_graph is None or curr_id in base_graph._royals
        """
        # Get ids and names of children and parents
        if base_graph is None:
            children_info = WikiExtract.get_children(curr_id)
            parents_info = WikiExtract.get_parents(curr_id)
        else:
            # tuples in lists contains additional birth date information
            children_info = [(c.wiki_id, c.name, c.birth_year)
                             for c in base_graph.get_royal(curr_id).children]
            parents_info = [(p.wiki_id, p.name, p.birth_year)
                            for p in base_graph.get_royal(curr_id).parents]

        if parents_info is not None:
            # Add parents and create edge to current royal
            for royal_info in parents_info:
                # print(f'Parent: {royal_info[1]}')

                if base_graph is None:
                    self.add_royal(royal_info[0], royal_info[1])
                else:
                    self.add_royal_with_birth_year(royal_info[0], royal_info[1], royal_info[2])

                self.add_edge(royal_info[0], curr_id)

                # Enqueue this parent since we need to add this parent's
                # children and parents
                royals_queue.append((curr_depth, royal_info[0], royal_info[1]))

        if children_info is not None:
            # Add children and create edge to current royal
            for royal_info in children_info:
                # print(f'Children: {royal_info[1]}')

                if base_graph is None:
                    self.add_royal(royal_info[0], royal_info[1])
                else:
                    self.add_royal_with_birth_year(royal_info[0], royal_info[1], royal_info[2])

                self.add_edge(curr_id, royal_info[0])

                # Enqueue this child since we need to add this child's children and parents
                royals_queue.append((curr_depth, royal_info[0], royal_info[1]))

        # Add curr_id to royals_added since we have added children
        # and parents and created edges
        royals_added.add(curr_id)

    ################################################################################################
    # Visualization
    ################################################################################################
    def visualize(self, highlight_path: Optional[list[str]] = None,
                  highlight_nodes: Optional[list[str]] = None) -> None:
        """Visualize this graph using networkx.

        Royals are colored according to birth_year (older = darker).

        Blue royals have no birth_year.

        Args:
            highlight_path: Optional path to highlight in the visualization.
            highlight_nodes: Optional nodes to highlight in the visualization.
        """
        # Define networkx requirements and create networkx graph
        layout = "spring_layout"
        graph_nx = self.to_networkx()

        # Create positions and labels for nodes
        pos = getattr(nx, layout)(graph_nx)

        # We will use birth_years for coloring of nodes.
        birth_year_real = [self._royals[id_].birth_year for id_ in graph_nx.nodes if
                           self._royals[id_].birth_year != -1]
        if len(birth_year_real) == 0:
            min_max_years = (1, 1)  # All will be same color
        else:
            min_max_years = (min(birth_year_real), max(birth_year_real))

        # Create plotly traces
        data1 = self.create_traces(graph_nx, pos, (highlight_path, highlight_nodes), min_max_years)

        # If highlight path is not None, overlay red edges on the edges which need to be highlighted
        if highlight_path is not None:
            x_edges_highlight = []
            y_edges_highlight = []

            for i in range(len(highlight_path) - 1):
                x_edges_highlight += [pos[highlight_path[i]][0],
                                      pos[highlight_path[i + 1]][0], None]
                y_edges_highlight += [pos[highlight_path[i]][1],
                                      pos[highlight_path[i + 1]][1], None]

            line = dict(color='rgb(255,0,0)', width=2)
            trace5 = Scatter(x=x_edges_highlight, y=y_edges_highlight, mode='lines', name='edges',
                             line=line, hoverinfo='none')
            data1.append(trace5)

        fig = Figure(data=data1)
        fig.update_layout({'showlegend': False})
        fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
        fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
        fig.show()

    def create_traces(self, graph_nx: nx.Graph, pos: dict,
                      highlight_path_and_nodes: Tuple[Optional[list[str]], Optional[list[str]]],
                      min_max_years: Tuple[int, int]) -> list:
        """Create plotly traces from networkx graph and other information."""
        colors = []
        for wiki_id in graph_nx.nodes:
            # Color red if need to be highlighted, else color according to birth_year
            if ((highlight_path_and_nodes[0] is not None
                 and wiki_id in highlight_path_and_nodes[0])) or \
                    (highlight_path_and_nodes[1] is not None
                     and wiki_id in highlight_path_and_nodes[1]):
                colors.append('rgb(255,0,0)')
            else:
                birth_year = self._royals[wiki_id].birth_year
                if birth_year == -1:
                    # Color blue if no birth year
                    colors.append('rgb(0,0,255)')
                elif min_max_years[0] == min_max_years[1]:
                    color = 255 // 2  # To avoid division by zero error
                    colors.append(f'rgb({color},{color},{color})')
                else:
                    # Darker = older
                    max_min_diff = min_max_years[1] - min_max_years[0]
                    color = 255 * ((birth_year - min_max_years[0]) / max_min_diff)
                    colors.append(f'rgb({color},{color},{color})')

        # Define necessary variables for plotly visualization
        x_edges = []
        y_edges = []
        for edge in graph_nx.edges:
            x_edges += [pos[edge[0]][0], pos[edge[1]][0], None]
            y_edges += [pos[edge[0]][1], pos[edge[1]][1], None]

        trace3 = Scatter(x=x_edges, y=y_edges, mode='lines', name='edges',
                         line=dict(color='rgb(105, 89, 205)', width=1), hoverinfo='none')

        trace4 = Scatter(x=[pos[k][0] for k in graph_nx.nodes],
                         y=[pos[k][1] for k in graph_nx.nodes], mode='markers', name='nodes',
                         marker=dict(symbol='circle-dot', size=10, color=colors,
                                     line=dict(color='rgb(105, 89, 205)', width=0.5)),
                         text=list([self._royals[id_].name for id_ in graph_nx.nodes]),
                         hovertemplate='%{text}',
                         hoverlabel={'namelength': 0})

        return [trace3, trace4]

    def visualize_family(self, wiki_id: str, max_depth: int) -> None:
        """Generates a graph of a Royal's family by expanding around the given id and visualizes.

        Args:
            wiki_id: The id of the 'root royal' whose family we want to draw and on which
                we will expand.
            max_depth: Max depth (number of edges) away from root royals
                that will be included in family graph.
        """
        graph = RoyalsGraph()

        # royals_queue is a queue of tuples. Each tuple contains information about a royal
        # who has been added as a node to the graph but whose children and parents have yet to
        # all be added. Each royal is removed from royals_queue and added to royals_added
        # once all the royal's children and parents are added and the edges between them are formed.
        royals_queue = []
        royals_added = set()

        # Add root royal to graph and royals_queue
        graph.add_royal_with_birth_year(wiki_id, self._royals[wiki_id].name,
                                        self._royals[wiki_id].birth_year)
        royals_queue.append((0, wiki_id, self._royals[wiki_id].name))

        while len(royals_queue) > 0:
            # curr_depth: number of edges away from the associated root royal
            # curr_id, curr_name: id and name of current royal
            curr_depth, curr_id, curr_name = royals_queue.pop(0)
            # print(f'Current: {curr_name}')

            # After this point, curr_depth is the distance of the parents/children of the
            # current royal to the associated root royal.
            curr_depth += 1

            if curr_depth <= max_depth:
                graph.add_children_parents(curr_id, curr_depth, royals_queue, royals_added, self)

        graph.visualize([wiki_id, wiki_id])

    def to_networkx(self, max_vertices: int = 5000) -> nx.Graph:
        """Convert this graph into a networkx Graph.

        max_vertices specifies the maximum number of vertices that can appear in the graph.
        (This is necessary to limit the visualization output for large graphs.)
        """
        graph_nx = nx.Graph()

        for wiki_id in self._royals:
            v = self._royals[wiki_id]
            graph_nx.add_node(wiki_id)

            for u in set.union(v.parents, v.children):
                if graph_nx.number_of_nodes() < max_vertices:
                    graph_nx.add_node(u.wiki_id)

                if u.wiki_id in graph_nx.nodes:
                    graph_nx.add_edge(v.wiki_id, u.wiki_id)

            if graph_nx.number_of_nodes() >= max_vertices:
                break

        return graph_nx

    ################################################################################################
    # Pathfinding Algorithms
    ################################################################################################
    def connected_breadth(self, id1: Any, id2: Any) -> Tuple[bool, list[str], float]:
        """Return whether id1 and id2 are connected in the RoyalsGraph using the
        Breadth-First search algorithm.

        Also return the path connecting the nodes (if any) and the time taken.

        The algorithm uses a queue to check vertices in a first-in-first-out fashion.
        That is, the algorithm checks the neighbours of the root. Then, the neighbours of each
        neighbour of the root. Etc...

        Preconditions:
            - id1 in self._royals
            - id2 in self._royals
            - id1 != id2
        """
        tik = time.time()

        # Each element of queue is a list containing a _Royal object and
        # list containing the current path from the initial id1 royal and the current royal
        queue = [[self._royals[id1], [id1]]]
        visited = set()

        while len(queue) > 0:
            v, path_so_far = queue.pop(0)

            for u in set.union(v.parents, v.children):
                if u.wiki_id == id2:
                    tok = time.time()
                    return True, path_so_far + [u.wiki_id], tok - tik
                elif u not in visited:
                    visited.add(u)
                    queue.append([u, path_so_far + [u.wiki_id]])

        tok = time.time()
        return False, [], tok - tik

    def connected_depth(self, id1: Any, id2: Any) -> Tuple[bool, list[str], float]:
        """Return whether id1 and id2 are connected in the RoyalsGraph using the
        Depth-First search algorithm.

        Also return the path connecting the nodes (if any) and the time taken.

        The algorithm uses a stack to check vertices in a last-in-first-out fashion.
        That is, the algorithm checks the first neighbour of the root. Then, the first neighbour
        of that the first neighbour of the root. Etc... Eventually, after it has checked all paths
        stemming from the first neighbour of the root, it comes back to the second neighbour of the
        root and does the same depth-first search from there... etc.

        Preconditions:
            - id1 in self._royals
            - id2 in self._royals
            - id1 != id2
        """
        tik = time.time()

        # Each element of stack is a list containing a _Royal object and
        # list containing the current path from the initial id1 royal and the current royal
        stack = [[self._royals[id1], [id1]]]
        visited = set()

        while len(stack) > 0:
            v, path_so_far = stack.pop()

            for u in set.union(v.parents, v.children):
                if u.wiki_id == id2:
                    tok = time.time()
                    return True, path_so_far + [u.wiki_id], tok - tik
                elif u not in visited:
                    visited.add(u)
                    stack.append([u, path_so_far + [u.wiki_id]])

        tok = time.time()
        return False, [], tok - tik


class _Royal:
    """A royal in RoyalsGraph.

    Instance Attributes:
        - wiki_id: The wiki id of this royal.
        - name: The name of this royal.
        - birth_year: The birth year of this royal.
        - parents: This parents of this royal.
        - children: This children of this royal.

    Representation Invariants:
        - self not in self.parents
        - self not in self.children
        - all(self in u.children for u in self.parents)
        - all(self in u.parents for u in self.children)
        - self.wiki_id[0] == 'Q' and self.wiki_id[1:].isdigit()
    """
    wiki_id: str
    name: str
    birth_year: int
    parents: set[_Royal]
    children: set[_Royal]

    def __init__(self, wiki_id: str, name: str, birth_year: int) -> None:
        """Initialize a new royal with the given name, parents, and children."""
        self.wiki_id = wiki_id
        self.name = name
        self.birth_year = birth_year
        self.parents = set()
        self.children = set()


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'pygame_menu', 'pygame', 'os', 'networkx',
                          'plotly.graph_objs', 'datetime', 'pickle',
                          'random', 'royals_graph', 'wiki_extract',
                          'pygame_menu.themes', 'time'],
        'allowed-io': ['save', 'load'],
        'max-line-length': 100,
        # Disables E1101, which incorrectly views some pygame functions as not members of pygame.
        'disable': ['R1705', 'C0200', 'E1101']
    })

    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = True
    python_ta.contracts.check_all_contracts()
