from urllib.parse import quote_plus
from pymongo import MongoClient

# user = "YOUR_USERNAME"        # type them directly, raw and unencoded
# password = "YOUR_PASSWORD"

user = "vmu"
password = "XXXX"

uri = f"mongodb+srv://{quote_plus(user)}:{quote_plus(password)}@cluster0.hte6gm5.mongodb.net/"
print(f"Connecting to MongoDB cluster {uri}")
print(MongoClient(uri, serverSelectionTimeoutMS=5000).admin.command("ping"))