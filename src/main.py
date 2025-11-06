# API imports
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse

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


app = FastAPI()


@app.get("/v1/vault", response_model=status_schema)
async def read_root():
    return JSONResponse(content={"status": "ok", "version": "v0.1.0"}, status_code=200)


@app.get("/v1/vault/decrypt_vault", response_model=vault_structure_schema)
async def decrypt_vault(x_vault_key: str | None = Header(default=None)):
    if x_vault_key:
        project_key, salt, timestamp = x_vault_key.split('.')
        data = pg.get_vault_data(project_key)
        if data != {}:
            decrypted_data = {}
            for item in data[project_key]:
                decrypted_data[item] = crypt.decrypt(data[project_key][item], crypt.derive_key(project_key, salt))
                
            return JSONResponse(content={"data": decrypted_data}, status_code=200)
        
    return JSONResponse(content={"message": "Invalid request."}, status_code=400)


@app.get("/v1/vault/vault_structure", response_model=vault_structure_schema)
async def get_vault_structure():
    return JSONResponse(content={"data": pg.get_vault_data('*')}, status_code=200)


@app.post("/v1/vault/create_vault", response_model=create_vault_schema)
async def create_vault(request: Request):
    vault_key = crypt.create_vault_key()
    project_key = vault_key['project_key']
    if request.body():
        post_data = {}
        body = await request.json()
        for item in body.get("data", {}):
            post_data[item] = crypt.encrypt(body["data"][item], crypt.derive_key(project_key, vault_key['salt']))
            
        pg.post_data_to_vault(project_key, post_data)
        return JSONResponse(content={"message": "Vault created successfully.", "x-vault-key": vault_key['full_key']}, status_code=201)
    
    pg.post_data_to_vault(project_key, {})
    return JSONResponse(content={"message": "Empty vault created successfully.", "x-vault-key": vault_key['full_key']}, status_code=201)


@app.post("/v1/vault/update_vault", response_model=update_vault_schema)
async def update_vault(request: Request, x_vault_key: str | None = Header(default=None)):
    if x_vault_key:
        project_key, salt, timestamp = x_vault_key.split('.')
        data = pg.get_vault_data(project_key)
        if data != {}:
            body = await request.json()
            if body is None or "data" not in body:
                return JSONResponse(content={"message": "No data provided."}, status_code=400)
            
            for item in body.get("data", {}):
                if body["data"][item] is not None and body["data"][item] != "":
                    data[project_key][item] = crypt.encrypt(body["data"][item], crypt.derive_key(project_key, salt))
                else:
                    if item in data[project_key]:
                        del data[project_key][item]
                
            pg.post_data_to_vault(project_key, data[project_key])
                
            return JSONResponse(content={"message": "Vault updated successfully."}, status_code=200)

    return JSONResponse(content={"message": "Invalid request."}, status_code=400)
