import os
import requests
from dotenv import load_dotenv

load_dotenv()


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
        
        try:
            if self.method == "POST":
                response = requests.post(
                    endpoint,
                    json=self.body,
                    headers=headers,
                    timeout=10
                )
            else:
                response = requests.get(
                    endpoint,
                    params=self.query_params,
                    headers=headers,
                    timeout=10
                )
            
            response.raise_for_status()
            data = response.json()
            return SupabaseResponse(data, None)
        except requests.RequestException as e:
            # Try to include response text for easier debugging when available
            resp_text = None
            try:
                resp = getattr(e, "response", None)
                if resp is None:
                    resp = locals().get("response", None)
                if resp is not None:
                    resp_text = resp.text
            except Exception:
                resp_text = None

            err_msg = str(e)
            if resp_text:
                # Avoid exposing secrets; include only response body to aid debugging
                err_msg = f"{err_msg}; response_text={resp_text}"

            return SupabaseResponse(None, err_msg)


class _LazySupabase:
    """Lazy-load Supabase credentials on first use."""
    _instance = None
    
    def __getattr__(self, name):
        if self._instance is None:
            # Prefer server-side credentials, fall back to public vars if missing
            url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            key = (
                os.getenv("SUPABASE_SECRET_KEY")
                or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                or os.getenv("SUPABASE_KEY")
                or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")
            )

            if not url:
                raise ValueError("SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL environment variable is required")
            if not key:
                raise ValueError(
                    "One of SUPABASE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_KEY, or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY is required"
                )

            self._instance = SupabaseClient(url, key)
        
        return getattr(self._instance, name)


supabase = _LazySupabase()