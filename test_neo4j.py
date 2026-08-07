from neo4j import GraphDatabase

URI = "neo4j+s://6564adf1.databases.neo4j.io"
USER = "6564adf1"
PASSWORD = "ThkjDmAY5BB5mgdM-kKxJxtG86HQzml_5O7MpabdH-4"

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

try:
    driver.verify_connectivity()
    print("✅ Connected to Neo4j AuraDB")

    with driver.session() as session:
        result = session.run("RETURN 'Hello Neo4j' AS msg")
        print(result.single()["msg"])

finally:
    driver.close()