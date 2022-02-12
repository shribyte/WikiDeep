"""
Module containing the program UI.
"""
from __future__ import annotations
import random
from typing import Optional, List, Callable, Tuple

from pygame_menu.themes import Theme
from pygame_menu import Menu
import pygame_menu
import pygame

from royals_graph import RoyalsGraph

ALIGN_LEFT = pygame_menu.locals.ALIGN_LEFT


class UserInterface:
    """Creates a pygame instance with main menu and visualizations.

    Instance Attributes:
        - graph: A RoyalsGraph object with our loaded royals.
        - screen: the pygame Surface to render everything on.
        - main_menu: the pygame menu object that handles selecting modes and leaving.
        - secondary_menu: the menu for the specific details for each mode.
        - theme: the theme for the menu to render with.
        - current_mode_method: the method corresponding to the current mode being run.
    """
    graph: RoyalsGraph
    screen: Optional[pygame.Surface]
    main_menu: Optional[Menu]
    secondary_menu: Optional[Menu]
    query_royal_ids: List[Optional[str]]
    theme: Theme
    current_mode_method: Optional[Callable]

    def __init__(self) -> None:
        """Initialize a new user interface for the given datafile path.
        """
        # Start an instance of pygame
        _, num_failed = pygame.init()
        if num_failed > 0:
            raise Exception('Something failed to import')

        # Initialize the pygame surface to be used for the rest of the project.
        self.screen = pygame.display.set_mode((1200, 780))

        # Initialize values for the class attributes.
        self.main_menu = None
        self.secondary_menu = None

        # Menu theme initialization
        self.theme = pygame_menu.themes.THEME_SOLARIZED.copy()
        self.theme.menubar_close_button = False

        # Set up a temporary loading menu before running
        temp_menu = pygame_menu.Menu("Loading Graph Database, Please Wait...", 1200, 780,
                                     theme=self.theme)
        temp_menu.draw(self.screen)
        pygame.display.update()

        # Load the graph from the saved file.
        self.graph = RoyalsGraph.load()

        # Initialize the pair royals who will be compared in the program
        self.query_royal_ids = [None, None]
        # Initialize the comparison method
        self.current_mode_method = None

    def start_main_menu(self) -> None:
        """Display main menu with button options for each mode. """
        # Always reset royal pair and current_mode_method before an option is chosen
        self.query_royal_ids = [None, None]
        self.current_mode_method = None

        # Start the main menu
        self.main_menu = pygame_menu.Menu("European Royalty and Their Bloodlines", 1200, 780,
                                          theme=self.theme)

        # Add buttons with callbacks to menu items
        self.main_menu.add.button("Royal Connections: Breadth-First Search V.S. Depth-First Search",
                                  self.run_race_pathfinders)
        self.main_menu.add.button("The Royal Family: Visualize a Royal's Family",
                                  self.run_show_family)
        # Add button to exit safely
        self.main_menu.add.button("Quit", pygame_menu.events.EXIT)

        # Start rendering the menu on our surface
        self.main_menu.mainloop(self.screen)
        pygame.quit()

    def run_race_pathfinders(self) -> None:
        """Run Royal Connections: Breadth-First Search V.S. Depth-First Search" mode
        from main menu."""
        # Set current menu option callback to this method
        self.current_mode_method = self.run_race_pathfinders

        # Set text for Royal Selection Screen
        title = 'Royal Connections: Breadth-First Search V.S. Depth-First Search'
        text = 'In this mode, the user enters the name of two royals in the graph and we employ ' \
               '\ntwo pathfinding algorithms (Breadth-First Search and Depth-First Search) to ' \
               '\ndetermine whether the two royals are connected. Further, we report the time ' \
               'taken \nfor each search algorithm and visualize the path found by the winning ' \
               'algorithm. \nNote that rendering the graph might take a minute.' \
               '\n\nPlease choose your two royals:'

        # Keep selecting a royal until both spots are filled
        while None in self.query_royal_ids:
            # Call the selection function to ask for the relevant information.
            self.royal_selection(title, text, 'First Royal: ', 'Second Royal: ')

        # The royals should already have been chosen, so not None:
        assert None not in self.query_royal_ids

        # Both royals are in the graph by royal_selection, so we can get their IDs and names.
        id1, id2 = self.query_royal_ids[0], self.query_royal_ids[1]
        name1, name2 = self.graph.get_royal(id1).name, self.graph.get_royal(id2).name

        # call both pathfinding algorithms.
        found_breadth, path_breadth, time_breadth = self.graph.connected_breadth(id1, id2)
        found_depth, path_depth, time_depth = self.graph.connected_depth(id1, id2)

        # Both algorithms are correct, so there should be no difference in the result.
        assert found_breadth == found_depth

        text, path = self.get_race_results_text((name1, name2), found_breadth,
                                                (time_breadth, time_depth),
                                                path_breadth, path_depth)

        # Display results screen
        self.secondary_menu = pygame_menu.Menu('Royal Connections: Breadth-First Search V.S. '
                                               'Depth-First Search',
                                               1200, 780, theme=self.theme)

        self.secondary_menu.add.label(text, align=ALIGN_LEFT)
        if found_breadth:
            self.graph.visualize(path)
        else:
            self.graph.visualize(None, [id1, id2])

        # Spacing to the return
        self.secondary_menu.add.label("")
        self.secondary_menu.add.button("Return to Main Menu", self.start_main_menu)

        # Start rendering the menu on our surface.
        self.secondary_menu.mainloop(self.screen)

    @staticmethod
    def get_race_results_text(names: Tuple[str, str], found: bool,
                              times_breadth_depth: Tuple[float, float], path_breadth: list[str],
                              path_depth: list[str]) -> Tuple[str, Optional[list[str]]]:
        """Create and return race results display text and path based on race results."""
        name1 = names[0]
        name2 = names[1]
        time_breadth = times_breadth_depth[0]
        time_depth = times_breadth_depth[1]

        # Determine winner based on runtime:
        if time_breadth == time_depth:
            # If the times are the same, then there is a tie.
            algo_index = random.choice([0, 1])
            algo_name = ['Breadth-First', 'Depth-First'][algo_index]
            path = [path_breadth, path_depth][algo_index]

            if found:
                text = (f'Breadth-First search and Depth-First search found a path between '
                        f'the royals:'
                        f'\n    \u2022{name1}'
                        f'\n    \u2022{name2}'
                        f'\nAlso, Breadth-First and Depth-First search both took about '
                        f'\n{time_breadth} seconds. So, there is a tie!'
                        f'\n\nSince there was a tie, we will randomly choose one of the algorithms '
                        f'and show the '
                        f'\npath that it discovered...'
                        f'\n\nThe path found by {algo_name} contains {len(path) - 1} edges. '
                        f'\nPlease see your browser for a visualization of this path!')
            else:
                text = (f'Breadth-First search and Depth-First search did not find a path between '
                        f'the royals:'
                        f'\n    \u2022{name1}'
                        f'\n    \u2022{name2}'
                        f'\nAlso, Breadth-First and Depth-First search both took about '
                        f'\n{time_breadth} seconds. So, there is a tie!'
                        f'\n\nPlease see your browser for a visualization of the graph and the '
                        f'two royals (in red)!')
        else:
            # There is no tie, we can find a winner
            if time_breadth < time_depth:
                path = path_breadth
                winner = 'Breadth-First'
            else:  # time_breadth > time_depth
                path = path_depth
                winner = 'Depth-First'

            if found:
                text = (f'Breadth-First and Depth-First search found a path between the royals:'
                        f'\n    \u2022{name1}'
                        f'\n    \u2022{name2}'
                        f'\nBreadth-First search took about {time_breadth} seconds while '
                        f'\nDepth-First search took about {time_depth} seconds. '
                        f'\nSo, {winner} search wins!'
                        f'\n\nThe path found by {winner} contains {len(path) - 1} edges. '
                        f'\nPlease see your browser for a visualization of this path!')
            else:
                text = (f'Breadth-First search and Depth-First search did not find a path between '
                        f'the royals:'
                        f'\n    \u2022{name1}'
                        f'\n    \u2022{name2}'
                        f'\nBreadth-First search took about {time_breadth} seconds while '
                        f'\nDepth-First search took about {time_depth} seconds. '
                        f'\nSo, {winner} search wins!'
                        f'\n\nPlease see your browser for a visualization of the graph and the two '
                        f'royals (in red)!')

        return text, path

    def run_show_family(self) -> None:
        """Run "The Royal Family: Visualize a Royal's Family" mode from main menu."""
        # Set current menu option callback to this method
        self.current_mode_method = self.run_show_family

        # Set text for Royal Selection Screen
        title = "The Royal Family: Visualize a Royal's Family"
        text = 'In this mode, the user enters the name of a royal in the graph and we visualize' \
               '\na graph of the royal\'s family (up to a maximum depth, or number of edges).' \
               '\n\nWe recommend depth values between 1 and 5 for reasonable loading times.'
        submit_first = 'Royal: '
        submit_second = 'Royal: '

        # Select one royal
        if self.query_royal_ids[0] is None:
            self.royal_selection(title, text, submit_first, submit_second)

        # Run generations visualization
        assert self.query_royal_ids[0] is not None
        id1 = self.query_royal_ids[0]
        name = self.graph.get_royal(id1).name

        # Display selection menu for the degree of separation
        self.secondary_menu = pygame_menu.Menu("The Royal Family: Visualize a Royal's Family",
                                               1200, 780, theme=self.theme)
        self.secondary_menu.add.label(text, align=ALIGN_LEFT)
        self.secondary_menu.add.label(
            '\nEnter the maximum depth for which to visualize the following royal\'s family:',
            align=ALIGN_LEFT)
        self.secondary_menu.add.label(f"    \u2022{name}", align=ALIGN_LEFT)
        self.secondary_menu.add.label("")
        self.secondary_menu.add.text_input("Maximum Depth from Family: ",
                                           textinput_id="max_depth", default="3")
        # Add the button for submitting the form, which will visualize everything.
        self.secondary_menu.add.button("Submit", self.show_family_callback)
        self.secondary_menu.add.button("Return to Main Menu", self.start_main_menu)

        # Start rendering the menu on our surface.
        self.secondary_menu.mainloop(self.screen)

    def show_family_callback(self) -> None:
        """Function that draws the graph of the royal's family."""
        assert self.query_royal_ids[0] is not None
        id1 = self.query_royal_ids[0]
        name = self.graph.get_royal(id1).name
        max_depth = int(self.secondary_menu.get_input_data()['max_depth'])
        self.graph.visualize_family(id1, max_depth)

        # Display results screen
        self.secondary_menu = pygame_menu.Menu('Royal Family Visualization - Results',
                                               1200, 780, theme=self.theme)
        self.secondary_menu.add.label("Please see your browser for a visualization "
                                      "of the following royal's family:",
                                      align=ALIGN_LEFT)
        self.secondary_menu.add.label(f"    \u2022{name}", align=ALIGN_LEFT)
        self.secondary_menu.add.label("")
        self.secondary_menu.add.label("The visualization shows this royal's family up to a "
                                      f"maximum depth of {max_depth} edges.", align=ALIGN_LEFT)
        self.secondary_menu.add.label("Also note that the royal you entered is drawn in red.",
                                      align=ALIGN_LEFT)
        self.secondary_menu.add.label("")
        self.secondary_menu.add.button("Return to Main Menu", self.start_main_menu)

        # Start rendering the menu on our surface
        self.secondary_menu.mainloop(self.screen)

    def royal_selection(self, title: str, text: str, submit_first: str, submit_second: str) -> None:
        """Show royal selection screen corresponding to which royal is being
        selected (first or second).

        We know whether first or second royal is being selected by looking at which elements of
        self.query_royal_ids are None. None elements mean the royal has not yet been selected.

        Args:
            title: Title for menu screen.
            text: Explanation text for menu screen.
            submit_first: Submit button text when first royal is being selected.
            submit_second: Submit button text when second royal is being selected.
        """
        if self.query_royal_ids[0] is None and self.query_royal_ids[1] is None:
            # First royal is being selected
            submit = submit_first
        else:
            assert self.query_royal_ids[1] is None
            # Second royal is being selected
            submit = submit_second

        # Choose a random default royal
        default_royal = random.choice([royal.name for royal in self.graph.get_all_royals()])

        # Setup menu
        self.secondary_menu = pygame_menu.Menu(title, 1200, 780, theme=self.theme)
        self.secondary_menu.add.label(text, align=ALIGN_LEFT)
        self.secondary_menu.add.label('')
        self.secondary_menu.add.text_input(submit, textinput_id="name", default=default_royal)
        self.secondary_menu.add.label('')
        self.secondary_menu.add.button("Submit", self.royal_selection_callback)
        self.secondary_menu.add.button("Randomize Royal", self.current_mode_method)
        self.secondary_menu.add.button("Return to Main Menu", self.start_main_menu)

        # Start rendering the menu on our surface, with custom background
        self.secondary_menu.mainloop(self.screen)

    def royal_selection_callback(self) -> None:
        """Given entered royal name, take corresponding action:

        If there is no royal with this name in the graph, call
        self.no_ids_found_message() to show an error message and return to royal selection.

        If there is 1 royal with this name in the graph, call
        self.set_query_royal_id() to set the first non-None element of
        self.query_royal_ids to the wiki_id of the royal with name.

        If there are more than 1 royal with this name in the graph,
        call self.pick_royal_by_birth() so that the user can pick the right royal.

        Preconditions:
            - None in self.query_royal_ids
        """
        name = self.secondary_menu.get_input_data()["name"]

        # Get ids for royals in the graph with the correct name
        wiki_ids = [r.wiki_id for r in self.graph.get_all_royals() if r.name == name]
        wiki_ids_in_graph = [id_ for id_ in wiki_ids
                             if id_ in self.graph.get_all_ids()]

        # Take corresponding action outlined in docstring
        if len(wiki_ids_in_graph) == 0:
            self.no_ids_found_message()
        elif len(wiki_ids_in_graph) == 1:
            wiki_id = wiki_ids_in_graph[0]
            self.set_query_royal_id(None, wiki_id)
        else:
            self.pick_royal_by_birth(name, wiki_ids_in_graph)

    def pick_royal_by_birth(self, name: str, wiki_ids_for_name: list[str]) -> None:
        """Search window to select royal by birth date when multiple royals have the same name.

        Args:
            name: Name of royal.
            wiki_ids_for_name: Wiki ids in self.graph with their name == name.

        Preconditions:
            - len(wiki_ids_in_graph) > 0
            - all(wiki_id in self.graph.get_all_ids for wiki_id in wiki_ids_for_name)
            - all(self.graph.get_royal(wiki_id).name == name for wiki_id in wiki_ids_for_name)

        """
        self.secondary_menu = pygame_menu.Menu(f"Who did you mean by '{name}'?",
                                               1200, 780, theme=self.theme)

        self.secondary_menu.add.label(
            'There were multiple royals in the graph that matched your search.', align=ALIGN_LEFT)
        self.secondary_menu.add.label(
            'Please select the birth year corresponding to your intended royal...',
            align=ALIGN_LEFT)
        self.secondary_menu.add.label('')

        birth_years = [(f'{self.graph.get_royal(wiki_id).birth_year}', wiki_id)
                       for wiki_id in wiki_ids_for_name]

        self.secondary_menu.add.selector('Select: ', birth_years, onreturn=self.set_query_royal_id)
        self.secondary_menu.mainloop(self.screen)

    def set_query_royal_id(self, input_from_menu: Optional[Tuple], wiki_id: str) -> None:
        """Set the first non-None element of self.query_royal_ids to wiki_id and
        call self.current_mode_method().

        Args:
            input_from_menu: a tuple of pygame inputs for when this method is a callback.
            wiki_id: the wikidata ID referring to the royal.
        """
        assert input_from_menu != 666  # to satisfy py_ta, pygame requires it even though unused
        if self.query_royal_ids[0] is None:
            assert self.query_royal_ids[1] is None
            self.query_royal_ids[0] = wiki_id
        elif self.query_royal_ids[0] != wiki_id:
            assert self.query_royal_ids[1] is None
            self.query_royal_ids[1] = wiki_id
        else:
            self.no_ids_found_message()  # Second royal == first royal

        self.current_mode_method()

    def no_ids_found_message(self) -> None:
        """Show an error message for when invalid values are entered.

        The user can click on a button to return to the royal selection screen.
        """
        self.secondary_menu = pygame_menu.Menu('Invalid Search Input', 1200, 780, theme=self.theme)

        self.secondary_menu.add.label(
            "Sorry, there were no results for your search."
            "\nIf entering two royals, you might have entered the same royal twice."
            "\nOtherwise, please check your spelling and try again...",
            align=ALIGN_LEFT)
        self.secondary_menu.add.label("")
        self.secondary_menu.add.button("Return to Royal Selection Screen", self.current_mode_method)

        # Start rendering the menu on our surface.
        self.secondary_menu.mainloop(self.screen)


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
