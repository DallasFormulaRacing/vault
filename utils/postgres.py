import json
import os
import psycopg2

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

db = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    database=os.getenv("PG_NAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    port=os.getenv("PG_PORT")
)

cursor = db.cursor()

def get_vault_data(project_key: str):
    data = {}
    
    try: # prevents hanging on db error
        if project_key != '*':
            cursor.execute(f"SELECT * FROM vault WHERE project_key = '{project_key}';")
        else:
            cursor.execute("SELECT * FROM vault;")
    except Exception as e:
        print(f"Error fetching vault data: {e}")
        cursor.rollback()
        return data
        
    result = cursor.fetchall()
    for item in result:
        data[item[0]] = item[1]
        
    return data


def create_vault(project_key: str, project_data: dict):
    try: # prevents hanging on db error
        cursor.execute(f"INSERT INTO vault (project_key, project_data) VALUES ('{project_key}', '{json.dumps(project_data)}');")
        db.commit()
    except Exception as e:
        print(f"Error creating vault: {e}")
        db.rollback()


def update_vault_data(project_key: str, project_data: dict):
    try: # prevents hanging on db error
        cursor.execute(f"UPDATE vault SET project_data = '{json.dumps(project_data)}' WHERE project_key = '{project_key}';")
        db.commit()
    except Exception as e:
        print(f"Error updating vault: {e}")
        db.rollback()