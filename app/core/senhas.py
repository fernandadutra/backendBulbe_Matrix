import hashlib
import hmac
import secrets

ITERACOES = 600_000


def _derivar(senha: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)


def gerar_hash(senha: str) -> str:
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}${_derivar(senha, salt).hex()}"


def conferir(senha: str, senha_hash: str) -> bool:
    try:
        salt_hex, hash_hex = senha_hash.split("$")
        esperado = bytes.fromhex(hash_hex)
        return hmac.compare_digest(_derivar(senha, bytes.fromhex(salt_hex)), esperado)
    except ValueError:
        return False
