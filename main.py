"""
Module containing main driver for program.
"""
from user_interface import UserInterface


def main() -> None:
    """Main driver for program."""
    ui = UserInterface()
    ui.start_main_menu()


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['user_interface'],
        'allowed-io': [],
        'max-line-length': 100,
        # Disables E1101, which incorrectly views some pygame functions as not members of pygame.
        'disable': ['R1705', 'C0200', 'E1101']
    })

    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = True
    python_ta.contracts.check_all_contracts()

    main()
