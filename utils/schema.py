from pydantic import BaseModel, Field
from enum import Enum
from typing import Union, List, Literal

class exception_schema(BaseModel):
    message: str 

class status_schema(BaseModel):
    status: str = "ok"
    version: str = "v0.1.0"

class vault_structure_schema(BaseModel):
    data: dict
    
class create_vault_schema(BaseModel):
    message: str
    x_vault_key: str = Field(alias="x-vault-key")
    
class update_vault_schema(BaseModel):
    message: str