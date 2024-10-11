from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
