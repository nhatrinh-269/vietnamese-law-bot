from neo4j import GraphDatabase


class LawGraphQuery:
    def __init__(self, uri):
        self.driver = GraphDatabase.driver(uri)

    def query(self, query):
        with self.driver.session() as session:
            result = session.run(query)
            return [record for record in result]

    def close(self):
        self.driver.close()

    def test_connection(self):
        """
        Test the connection to the Neo4j database.
        """
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("Database connection successful!")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
