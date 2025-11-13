from pydantic import BaseModel, Field

class exception_schema(BaseModel):
    message: str 

class status_schema(BaseModel):
    status: str
    version: str

class decrypt_schema(BaseModel):
    vault_metadata: dict
    data: dict
    
class create_vault_schema(BaseModel):
    message: str
    x_vault_key: str
    
class update_vault_schema(BaseModel):
    message: str