from redis import Redis

client = Redis(
    host="r-6jissuruar.instance-4jq0j2pm8.hc-7up0crkyn.ap-south-1.aws.f2e0a955bb84.cloud",
    port=54132,
    username="falkordb",
    password="Sathvik@254798",
    decode_responses=True
)

print(client.ping())
print("✅ Connected to FalkorDB!")