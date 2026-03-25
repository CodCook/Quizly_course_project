import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

class SupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
    
    def table(self, table_name):
        """Returns a table interface"""
        return TableClient(self, table_name)

class TableClient:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.query_params = {}
        self.method = "GET"
        self.body = None
    
    def select(self, columns="*"):
        """Select columns"""
        self.query_params["select"] = columns
        return self
    
    def limit(self, count):
        """Limit results"""
        self.query_params["limit"] = count
        return self
    
    def execute(self):
        """Execute the query"""
        endpoint = f"{self.client.url}/rest/v1/{self.table}"
        headers = {
            "apikey": self.client.key,
            "Authorization": f"Bearer {self.client.key}",
            "Content-Type": "application/json"
        }
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in self.query_params.items()])
        if query_string:
            endpoint += "?" + query_string
        
        try:
            req = urllib.request.Request(endpoint, headers=headers, method=self.method)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return {"data": data, "error": None}
        except urllib.error.HTTPError as e:
            return {"data": None, "error": str(e)}

supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)