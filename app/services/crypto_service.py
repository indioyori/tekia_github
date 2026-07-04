"""
Servicio de cifrado para TEKIA.
Usa Fernet (AES-128) para cifrar/descifrar notas.
"""
from pathlib import Path
from cryptography.fernet import Fernet
from .config import KEYS_DIR, ENCRYPTION_ENABLED
import os


class CryptoService:
    """Servicio de cifrado/descifrado usando Fernet."""
    
    def __init__(self):
        self.key_path = KEYS_DIR / "secret.key"
        self._key = self._load_or_generate_key()
        self.cipher = Fernet(self._key)
    
    def _load_or_generate_key(self):
        """Carga la clave o genera una nueva si no existe."""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            # Proteger el archivo de claves
            os.chmod(self.key_path, 0o600)
            return key
    
    def encrypt(self, text: str) -> str:
        """Cifra un texto."""
        if not ENCRYPTION_ENABLED:
            return text
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Descifra un texto."""
        if not ENCRYPTION_ENABLED:
            return encrypted_text
        return self.cipher.decrypt(encrypted_text.encode()).decode()
    
    def is_encrypted(self, text: str) -> bool:
        """Verifica si un texto está cifrado."""
        if not ENCRYPTION_ENABLED:
            return False
        try:
            self.cipher.decrypt(text.encode())
            return True
        except:
            return False


# Instancia global
crypto_service = CryptoService()
