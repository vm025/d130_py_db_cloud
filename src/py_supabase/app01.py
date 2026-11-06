import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd


load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
print(f"SUPABASE_URL: {url}")


if url is None or key is None:
	raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

supabase: Client = create_client(url, key)  # initialize supabase client.
# print(f"Supabase client created: {supabase}")

try:
    result = supabase.table("tankerInfo").select("*").execute()
    print(f"Result: {result}")
    data = result.data
    df_tankerinfo = pd.DataFrame(data)
    print("df_tankerinfo: ", df_tankerinfo + "\n")
except Exception as e:
    print(f"Error occurred while fetching data from Supabase: {e}")
    result = None




response = supabase.table('tankerInfo').select("*").eq("block_name", "A-block").execute()
print(f"Response_2: {response.data}")
