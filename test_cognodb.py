from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("COGNODB_URI"),
    auth=(os.getenv("COGNODB_USER"), os.getenv("COGNODB_PASSWORD"))
)

with driver.session() as session:
    session.run("""
        CREATE (p:Person {
            name:'Sathvik',
            age:22,
            city:'Hyderabad'
        })
    """)

print("✅ Person node created successfully!")

driver.close()