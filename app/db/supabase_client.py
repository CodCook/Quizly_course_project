import os
import json
import urllib.request
import urllib.error
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

class SupabaseResponse:
    def __init__(self, data, error=None):
        self.data = data
        self.error = error

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
    
    def insert(self, data):
        """Insert data"""
        self.method = "POST"
        self.body = data
        return self
    
    def order(self, column, desc=False):
        """Order by column"""
        order_dir = "desc" if desc else "asc"
        self.query_params["order"] = f"{column}.{order_dir}"
        return self
    
    def eq(self, column, value):
        """Filter by equality"""
        self.query_params[column] = f"eq.{value}"
        return self
    
    def single(self):
        """Return single record"""
        self.query_params["single"] = "true"
        return self
    
    def execute(self):
        """Execute the query"""
        endpoint = f"{self.client.url}/rest/v1/{self.table}"
        headers = {
            "apikey": self.client.key,
            "Authorization": f"Bearer {self.client.key}",
            "Content-Type": "application/json"
        }
        
        # Build query string for GET requests
        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in self.query_params.items()])
        if query_string and self.method == "GET":
            endpoint += "?" + query_string
        
        print(f"🔍 Making {self.method} request to: {endpoint}")
        
        try:
            if self.method == "POST":
                body = json.dumps(self.body).encode() if self.body else None
                print(f"📤 Request body: {self.body}")
                req = urllib.request.Request(endpoint, data=body, headers=headers, method=self.method)
            else:
                req = urllib.request.Request(endpoint, headers=headers, method=self.method)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                print(f"📥 Response: {data}")
                return SupabaseResponse(data, None)
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error: {e.code} - {e.reason}")
            try:
                error_data = json.loads(e.read().decode())
                print(f"❌ Error details: {error_data}")
            except:
                print(f"❌ Error response: {e.read().decode()}")
            return SupabaseResponse(None, str(e))

supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)