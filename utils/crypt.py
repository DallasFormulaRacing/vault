# Crypt imports
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import base64
import secrets
from datetime import datetime


def encrypt(text, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(text.encode('utf-8'))
    
    return '.'.join([
        base64.b64encode(ciphertext).decode('utf-8'),
        base64.b64encode(cipher.nonce).decode('utf-8'),
        base64.b64encode(tag).decode('utf-8')
    ])


def decrypt(text, key):
    ciphertext_b64, nonce_b64, tag_b64 = text.split('.')
    
    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)
    tag = base64.b64decode(tag_b64)
    
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    
    return plaintext.decode('utf-8')


def create_vault_key():
    key_info = {
        "project_key": base64.b64encode(secrets.token_bytes(64)).decode('utf-8'),
        "salt": base64.b64encode(secrets.token_bytes(128)).decode('utf-8'),
        "timestamp": base64.b64encode(datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode('utf-8')).decode('utf-8')
    }
    
    key_info['full_key'] = '.'.join([key_info['project_key'], key_info['salt'], key_info['timestamp']])
    
    return key_info


def derive_key(project_key, salt, iterations=500000):
    key = PBKDF2(project_key, salt, dkLen=32, count=iterations, hmac_hash_module=SHA256)
    return key