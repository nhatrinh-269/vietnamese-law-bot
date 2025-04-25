from database import LawGraphQuery
from config import URI


def extract_data_from_graph(dan_su_query, hinh_su_query):
    """
    Extracts data from the graph database using given queries.

    Args:
        dan_su_query (str): The query for civil law to be executed on the graph database.
        hinh_su_query (str): The query for criminal law to be executed on the graph database.

    Returns:
        tuple: A tuple containing results for civil law and criminal law queries.
    """
    # Create an instance of LawGraphQuery
    graph_query = LawGraphQuery(URI)

    # Initialize results
    results_ds = ""
    results_hs = ""

    # Execute the query for civil law if not empty
    if dan_su_query.strip():
        results_ds = graph_query.query(dan_su_query)

    # Execute the query for criminal law if not empty
    if hinh_su_query.strip():
        results_hs = graph_query.query(hinh_su_query)

    return results_ds, results_hs
