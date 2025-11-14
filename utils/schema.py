from pydantic import BaseModel

class exception_schema(BaseModel):
    message: str 

class status_schema(BaseModel):
    status: str
    version: str

class metadata_schema(BaseModel):
    created: str
    updated: str
    version: int
    
    model_config = {"extra": "allow"}
    
class list_products_schema(BaseModel):
    vault_metadata: metadata_schema
    products: list[str]
    
class decrypt_schema(BaseModel):
    vault_metadata: metadata_schema
    data: dict[str, str]
    
class create_vault_schema(BaseModel):
    message: str
    x_vault_key: str
    
class update_vault_schema(BaseModel):
    message: str