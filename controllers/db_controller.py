from supabase import create_client, Client
from supabase.storage import StorageFileAPI

# from dotenv import load_dotenv

# load_dotenv()

SUPABASE_URL = "https://zmihpyxsmvcstuyukgly.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InptaWhweXhzbXZjc3R1eXVrZ2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjg2MjY0NzIsImV4cCI6MjA0NDIwMjQ3Mn0.FVBM2zKO-UjQW_Pz2mtNguRr4AeGj3c7r0NXLe0ZxWU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


storage: StorageFileAPI = supabase.storage()
files = storage.from_("test_bucket").list()
print(files)