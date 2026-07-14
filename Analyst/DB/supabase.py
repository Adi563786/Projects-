import os 
from dotenv import load_dotenv
load_dotenv()
SUPABASE_DB_URI=os.getenv("SUPABASE_DB_URI")
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(SUPABASE_DB_URI)