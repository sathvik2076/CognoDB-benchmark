from neo4j import GraphDatabase

URI = "bolt+ssc://18.162.190.69:7687"
USER = "sathvikbodugala25@gmail.com"
PASSWORD = "Sathvik@254798"

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

try:
    driver.verify_connectivity()
    print("✅ Connected to Memgraph!")

    with driver.session(database="memgraph") as session:
        result = session.run("RETURN 'Hello Memgraph!' AS message")
        print(result.single()["message"])

finally:
    driver.close()