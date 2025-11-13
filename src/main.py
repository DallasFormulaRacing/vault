# API imports
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse

# data imports
import json
import os
from datetime import datetime

# util imports
import utils.crypt as crypt
import utils.postgres as pg
from utils.schema import *

# Remove 422 docs from /docs

_openapi = FastAPI.openapi
def openapi(self: FastAPI):
    _openapi(self)

    for _, method_item in self.openapi_schema.get('paths').items():
        for _, param in method_item.items():
            responses = param.get('responses')
            # remove 422 response, also can remove other status code
            if '422' in responses:
                del responses['422']

    return self.openapi_schema

FastAPI.openapi = openapi

# End of 422 removal


# Start of function definitions

def update_vault_metadata(metadata: dict): # self explanatory
    metadata["created"] = metadata.get("created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    metadata["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata["version"] = 1 + metadata.get("version", 0)
    return metadata

# End of function definitions


app = FastAPI(root_path=os.getenv("API_ROOT_PATH", ""))


@app.get("/", response_model=status_schema)
async def read_root():
    return JSONResponse(content={"status": "ok", "version": "v0.1.2"}, status_code=200) # static return, update version # on release


@app.get("/decrypt_vault", response_model=decrypt_schema)
async def decrypt_vault(x_vault_key: str | None = Header(default=None), x_product_name: str | None = Header(default=None)):
    if x_vault_key:
        try:
            project_key, salt, timestamp = x_vault_key.split('.') # split combined key
            data = pg.get_vault_data(project_key)
        except:
            return JSONResponse(content={"message": f"Invalid x-vault-key"}, status_code=500)

        if data != {}: # check if vault data exists
            decrypted_data = {}
            
            if x_product_name not in data[project_key]: # check if product exists in vault data
                return JSONResponse(content={"message": "Invalid x-product-name"}, status_code=400)
            
            for item in data[project_key][x_product_name]: # decrypt each item in the product
                decrypted_data[item] = crypt.decrypt(data[project_key][x_product_name][item], crypt.derive_key(project_key, salt))

            metadata = data[project_key].get("vault_metadata", {}) # get vault metadata

            return JSONResponse(content={"vault_metadata": metadata, "data": decrypted_data}, status_code=200)

    return JSONResponse(content={"message": "Invalid request."}, status_code=400)


@app.get("/decrypt_secret", response_model=decrypt_schema)
async def decrypt_secret(x_vault_key: str | None = Header(default=None), x_product_name: str | None = Header(default=None), x_secret_name: str | None = Header(default=None)):
    if x_vault_key:
        try:
            project_key, salt, timestamp = x_vault_key.split('.')
            data = pg.get_vault_data(project_key)
        except:
            return JSONResponse(content={"message": f"Invalid x-vault-key"}, status_code=500)

        if data != {}:
            if x_product_name not in data[project_key]:
                return JSONResponse(content={"message": "Invalid product name."}, status_code=400)
            if x_secret_name not in data[project_key][x_product_name]:
                return JSONResponse(content={"message": "Invalid secret name."}, status_code=400)

            decrypted_secret = crypt.decrypt(data[project_key][x_product_name][x_secret_name], crypt.derive_key(project_key, salt))
            
            metadata = data[project_key].get("vault_metadata", {}) # get vault metadata

            return JSONResponse(content={"vault_metadata": metadata, "data": decrypted_secret}, status_code=200)

    return JSONResponse(content={"message": "Invalid request."}, status_code=400)


@app.post("/create_vault", response_model=create_vault_schema)
async def create_vault(request: Request, x_api_key: str | None = Header(default=None)):
    if x_api_key != os.getenv("VAULT_API_KEY"): # suuuuuuuuuuuuuuuuuuuper basic api key check, mostly to stop people from flooding the database (shouldn't be needed anyways)
        return JSONResponse(content={"message": "Invalid API key."}, status_code=403)
    
    vault_key = crypt.create_vault_key() # generate new vault key using crypt util
    project_key = vault_key['project_key']
    if await request.body(): # check if request body is not empty
        post_data = {"vault_metadata": {}}
        try: # check if request body is valid json
            body = json.loads((await request.body()).decode('utf-8')) 
        except:
            return JSONResponse(content={"message": "Invalid JSON."}, status_code=400)
        
        if body is None or len(body) == 0: # check if request body is empty
            return JSONResponse(content={"message": "Incorrect request format."}, status_code=400)

        for x_product_name, product_value in body.items(): # iterate through each product in the request body
            post_data[x_product_name] = {}
            for secret_name, secret_value in product_value.items(): # iterate through each secret in the product (from body)
                if secret_value is not None and secret_value != "":
                    if x_product_name == "vault_metadata": # if product is vault metadata, do not encrypt, else encrypt
                        post_data[x_product_name][secret_name] = secret_value
                        
                    else:
                        post_data[x_product_name][secret_name] = crypt.encrypt(secret_value, crypt.derive_key(project_key, vault_key['salt']))

        post_data["vault_metadata"] = update_vault_metadata(post_data["vault_metadata"])
        
        try: # try posting to postgres, if fail rollback (stops the api from hanging on db error)
            pg.create_vault(project_key, post_data)
            return JSONResponse(content={"message": "Vault created successfully.", "x-vault-key": vault_key['full_key']}, status_code=201)
        except Exception as e:
            return JSONResponse(content={"message": f"Error creating vault: {e}"}, status_code=500)
        
    pg.create_vault(project_key, {"vault_metadata": update_vault_metadata({})})
    return JSONResponse(content={"message": "Empty vault created successfully.", "x-vault-key": vault_key['full_key']}, status_code=201)


@app.post("/update_vault", response_model=update_vault_schema)
async def update_vault(request: Request, x_vault_key: str | None = Header(default=None)):
    if x_vault_key: # check if vault key is provided
        try:
            project_key, salt, timestamp = x_vault_key.split('.')
            update_data = pg.get_vault_data(project_key)[project_key]
        except:
            return JSONResponse(content={"message": f"Invalid x-vault-key"}, status_code=500)
        
        try:
            body = json.loads((await request.body()).decode('utf-8'))
        except:
            return JSONResponse(content={"message": "Invalid JSON."}, status_code=400)
        
        if body is None or len(body) == 0:
            return JSONResponse(content={"message": "Incorrect request format."}, status_code=400)

        for x_product_name, product_value in body.items():
            for secret_name, secret_value in product_value.items():
                if secret_value is not None and secret_value != "": # if secret value is not empty or null then update/add the value
                    if x_product_name not in update_data: # if product does not exist in existing data then create it
                        update_data[x_product_name] = {}
                        
                    if x_product_name == "vault_metadata": # if product is vault metadata, do not encrypt, else encrypt
                        if secret_name != "version" and secret_name != "created": # prevent overwriting version and created fields
                            update_data[x_product_name][secret_name] = secret_value
                            
                    else:
                        update_data[x_product_name][secret_name] = crypt.encrypt(secret_value, crypt.derive_key(project_key, salt))
                
                else:
                    if secret_name in update_data[x_product_name]: # if secret exists in existing data then delete it
                        if not (x_product_name == "vault_metadata" and (secret_name == "version" or secret_name == "created")): # if product is vault metadata, do not delete version and created fields
                            del update_data[x_product_name][secret_name]

        update_data["vault_metadata"] = update_vault_metadata(update_data.get("vault_metadata", {})) # update vault metadata
        
        try: # try updating vault data in postgres and rollback on fail
            pg.update_vault_data(project_key, update_data)
        except Exception as e:
            return JSONResponse(content={"message": f"Error updating vault: {e}"}, status_code=500)

        return JSONResponse(content={"message": "Vault updated successfully."}, status_code=200)

    return JSONResponse(content={"message": "Invalid request."}, status_code=400)
