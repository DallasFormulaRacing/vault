import dotenv
import json
import os
import psycopg2

dotenv.load_dotenv()

db = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    database=os.getenv("PG_NAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    port=os.getenv("PG_PORT")
)

cursor = db.cursor()

#test_data = json.dumps({"example_key": "example_value"})

#cursor.execute(f"INSERT INTO vault (project_key, project_data) VALUES ('test_key', '{test_data}');")
#db.commit()


def get_vault_data(project_key: str):
    data = {}
    
    if project_key != '*':
        cursor.execute(f"SELECT * FROM vault WHERE project_key = '{project_key}';")
    else:
        cursor.execute("SELECT * FROM vault;")
        
    result = cursor.fetchall()
    for item in result:
        data[item[0]] = item[1]
        
    return data


def post_data_to_vault(project_key: str, project_data: dict):
    cursor.execute(f"UPDATE vault SET project_data = '{json.dumps(project_data)}' WHERE project_key = '{project_key}';")
    db.commit()