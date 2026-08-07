from arango import ArangoClient

client = ArangoClient(hosts="https://ac9167c14bca.arangodb.cloud:8529")

db = client.db(
    "_system",
    username="root",
    password="mAS13Mp3P4VANDLICCQ7"
)

print("Connected Successfully")