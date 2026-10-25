from uuid import uuid4


def gerar_id(prefixo: str) -> str:
    return f"{prefixo}_{uuid4().hex[:8]}"
