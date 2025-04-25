from database import LawGraphQuery
from config import URI, NEO4J_USER, PASSWORD

def extract_data_from_graph(dan_su_query, hinh_su_query):
    """
    Extracts data from the graph database using a given query.
    
    Args:
        dan_su_query (str): The query for civil law to be executed on the graph database.
        hinh_su_query (str): The query for criminal law to be executed on the graph database.
        
    Returns:
        list: A list of results obtained from the graph database.
    """
    # Create an instance of LawGraphQuery
    graph_query = LawGraphQuery(URI, NEO4J_USER, PASSWORD)
    
    # Execute the query and get the results
    results_ds = graph_query.query(dan_su_query)
    results_hs = graph_query.query(hinh_su_query)
    
    return results_ds, results_hs