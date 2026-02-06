import asyncio
if not hasattr(asyncio, 'coroutine'):
    asyncio.coroutine = lambda x: x

from algoliasearch.search_client import SearchClient
import streamlit as st
import sys
import toml

# Load secrets
try:
    with open(".streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
        APP_ID = secrets["ALGOLIA_APP_ID"]
        API_KEY = secrets["ALGOLIA_API_KEY"]
        print(f"✅ Found Secrets: App ID starts with {APP_ID[:4]}...")
except Exception as e:
    print(f"❌ Could not load secrets.toml: {e}")
    sys.exit(1)

def run_test():
    print("\n--- STARTING ALGOLIA CONNECTION TEST ---")
    
    try:
        client = SearchClient.create(APP_ID, API_KEY)
        index = client.init_index("sitemate_projects")
        print("✅ Client Initialized")

        record = {
            "objectID": "test_record_002",
            "name": "TEST PROJECT 2 - SUCCESS",
            "location": "Lekki Test Site",
            "est_value": 2000000
        }

        print("⏳ Attempting to write record to Algolia...")
        res = index.save_object(record)
        
        # --- ROBUST FIX FOR LIST vs DICT RESPONSE ---
        if isinstance(res, list):
            res = res[0] # Take the first receipt if it's a list
        # --------------------------------------------
        
        print(f"✅ Write Successful! Task ID: {res.get('taskID')}")
        
        print("⏳ Waiting for indexing...")
        index.wait_task(res['taskID'])
        
        print("\n🎉 SUCCESS! Algolia is fully connected.")
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    run_test()