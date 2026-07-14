import ast
from sentence_transformers import SentenceTransformer
import json
from sqlalchemy import inspect
from DB.supabase import db

def get_relevant_table(query,db,top_k=6):
    model=SentenceTransformer("all-MiniLM-L6-v2",local_files_only=True)
    vector=model.encode(query)
    vector_list=vector.tolist() if hasattr(vector,'tolist') else vector
    db_query=f"""
                            SELECT 
                                id, 
                                metadata,
                                (vector::vector) <=> '{vector_list}'::vector AS cosine_distance
                            FROM 
                                tablevector
                            ORDER BY 
                                cosine_distance ASC
                            LIMIT '{top_k}';
                            """
    result=db.run(db_query)
    parsed_result=ast.literal_eval(result)
    related=[]
    for i in parsed_result:
        related.append(i[0])
    return related

def get_schema():
    inspector = inspect(db._engine)
    connections=[]
    for table in inspector.get_table_names():
        fks=inspector.get_foreign_keys(table)
        for fk in fks:
            x=f'table:{table},referred_table:{fk["referred_table"]},constrained_columns:{fk["constrained_columns"]},referred_columns:{fk["referred_columns"]}'
            connections.append(x)
    schema= {}
    for table in inspector.get_table_names():
        columns=inspector.get_columns(table)
        schema[table]=[]
        for column in columns:
            schema[table].append((str(column['name']), str(column['type'])))
    result={        "schema":schema,        "connections":connections}
    # return json.dumps(result,indent=2)
    return result