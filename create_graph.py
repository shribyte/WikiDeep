"""
Module containing a function which creates a RoyalsGraph and saves it.
"""
from royals_graph import RoyalsGraph


class CreateGraph:
    """Creating and saving graphs."""

    @staticmethod
    def create_and_save_graph() -> None:
        """Create and save a graph."""
        root_names = {'Victor Emmanuel III', 'Charles IV', 'Ludwig III',
                      'Tomislav II', 'George V', 'Napoleon III', 'Wilhelm II', 'Christian X',
                      'George VI', 'Umberto II', 'Ivan III', 'Manuel II', 'Peter II',
                      'Ferdinand II of Aragon', 'Prince Alfred of Great Britain', 'Prince Adolphus',
                      'Duke of Cambridge', 'Prince Octavius of Great Britain', 'Queen Victoria',
                      'Queen Elizabeth II', 'Augustus II the Strong', 'Frederick I of Prussia',
                      'George I', 'Henry VII of England', 'Henry VII',
                      'Queen Victoria', 'Edward VII', 'Louis XV', 'Louis XIV',
                      'Ferdinand I', 'Maximilian II', 'Leopold I', 'Philip IV',
                      'Charles II', 'Francis II', 'William III',
                      'Napoleon I', 'Francis Joseph I', 'Frederick III'}

        graph = RoyalsGraph()

        graph.fill_graph(root_names, 6)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'pygame_menu', 'pygame',
                          'random', 'royals_graph', 'wiki_extract',
                          'pygame_menu.themes', 'time'],
        'allowed-io': [],
        'max-line-length': 100,
        # Disables E1101, which incorrectly views some pygame functions as not members of pygame.
        'disable': ['R1705', 'C0200', 'E1101']
    })

    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = True
    python_ta.contracts.check_all_contracts()
