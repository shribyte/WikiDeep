"""
Module for extracting royals information from wikipedia (using the wikibase api).
"""
import time
import urllib
from typing import Optional, Set, Tuple

from SPARQLWrapper import SPARQLWrapper, JSON
from wikibase_api import Wikibase


class WikiExtract:
    """Object for extracting data from wikipedia."""

    @staticmethod
    def get_children(wiki_id: str) -> Optional[Set[Tuple[str, str]]]:
        """Gets the children for a given wikidata id.

        Args:
            wiki_id: The wikidata ID for the object, ie 'Q57224'.

        Returns:
            set: A set of tuples (id, name) of the children.
        """
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery(
            f'''
            SELECT ?child ?childLabel
            WHERE
            {{
                wd:{wiki_id} wdt:P40 ?child.
                SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
            }}'''
        )

        sparql.setReturnFormat(JSON)

        # If HTTPError occurs, wait retry_after seconds and try again
        try:
            results = sparql.query().convert()
        except urllib.error.HTTPError as excep:
            retry_after = excep.headers["retry-after"]
            print('X' * 20 + f' WAIT {retry_after} SECONDS ' + 'X' * 20)
            time.sleep(int(retry_after) + 1)
            return WikiExtract.get_children(wiki_id)
        except IndexError:
            return None

        return_value = set()

        for result in results["results"]['bindings']:
            return_value.add((result['child']['value'][31:],
                              result['childLabel']['value']))

        return return_value

    @staticmethod
    def get_parents(wiki_id: str) -> Optional[Set[Tuple[str, str]]]:
        """Gets the parents for a given wikidata id.

        Args:
            wiki_id: The wikidata ID for the object, ie 'Q57224'.

        Returns:
            set: A set of tuples (id, name) of the parents.
        """
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery(
            f'''
            SELECT ?item ?itemLabel
            WHERE
            {{
                ?item wdt:P40 wd:{wiki_id}.
                SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
            }}'''
        )

        sparql.setReturnFormat(JSON)

        # If HTTPError occurs, wait retry_after seconds and try again
        try:
            results = sparql.query().convert()
        except urllib.error.HTTPError as excep:
            retry_after = excep.headers["retry-after"]
            print('X' * 20 + f' WAIT {retry_after} SECONDS ' + 'X' * 20)
            time.sleep(int(retry_after) + 1)
            return WikiExtract.get_parents(wiki_id)
        except IndexError:
            return None

        return_value = set()

        for result in results["results"]['bindings']:
            return_value.add((result['item']['value'][31:],
                              result['itemLabel']['value']))

        return return_value

    @staticmethod
    def get_birthdate(wiki_id: str) -> Optional[list[str]]:
        """Return a list of birthdates for a royal's wikidata id using wikibase api.

        Args:
            wiki_id: The wikidata ID for the object, ie 'Q57224'.

        Returns:
            list: A list of birth dates stored in strings.
        """
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery(
            f'''
            SELECT *
            WHERE
            {{
                wd:{wiki_id} wdt:P569 ?dateOfBirth
            }}'''
        )
        sparql.setReturnFormat(JSON)

        # If HTTPError occurs, wait retry_after seconds and try again
        try:
            results = sparql.query().convert()
        except urllib.error.HTTPError as excep:
            retry_after = excep.headers["retry-after"]
            print('X' * 20 + f' WAIT {retry_after} SECONDS ' + 'X' * 20)
            time.sleep(int(retry_after) + 1)
            return WikiExtract.get_birthdate(wiki_id)
        except IndexError:
            return None

        return_value = []

        for result in results["results"]['bindings']:
            return_value.append(result['dateOfBirth']['value'])

        return return_value

    @staticmethod
    def get_wikidata_ids(query: str) -> list:
        """Return a list of resulting ids for query_name using the wikibase api.

        Args:
            query: String to search for a wikidata id.
        """
        wb = Wikibase()
        result = wb.entity.search(query, 'en', entity_type="item")
        if result['success'] == 1:
            return [x['id'] for x in result['search']]
        return []

    @staticmethod
    def get_wikidata_id(query: str) -> Optional[str]:
        """Query wikibase api and return the wikibase id for the given royal's name.

        Args:
            query: String to search for a wikidata id.
        """
        # If HTTPError occurs, wait retry_after seconds and try again
        try:
            return WikiExtract.get_wikidata_ids(query)[0]
        except urllib.error.HTTPError as excep:
            retry_after = excep.headers["retry-after"]
            print('X' * 20 + f' WAIT {retry_after} SECONDS ' + 'X' * 20)
            time.sleep(int(retry_after) + 1)
            return WikiExtract.get_wikidata_id(query)
        except IndexError:
            return None


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['python_ta.contracts', 'urllib', 'SPARQLWrapper',
                          'wikibase_api', 'time'],
        'allowed-io': ['get_wikidata_id', 'get_birthdate', 'get_children', 'get_parents'],
        'max-line-length': 100,
        # Disables E1101, which incorrectly views some pygame functions as not members of pygame.
        'disable': ['R1705', 'C0200', 'E1101']
    })

    import python_ta.contracts

    python_ta.contracts.DEBUG_CONTRACTS = True
    python_ta.contracts.check_all_contracts()
