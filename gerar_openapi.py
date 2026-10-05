import yaml
from pathlib import Path
from app.main import app  # Importa a instância do FastAPI de app/main.py

def gerar_contrato_openapi():
    # Caminho da pasta docs/api a partir da raiz
    caminho_api = Path("docs/api")
    caminho_api.mkdir(parents=True, exist_ok=True)
    
    # Extrai o esquema OpenAPI do FastAPI
    schema_openapi = app.openapi()
    
    # Caminho do arquivo final
    arquivo_destino = caminho_api / "openapi.yaml"
    
    # Salva em formato YAML
    with open(arquivo_destino, "w", encoding="utf-8") as f:
        yaml.dump(schema_openapi, f, sort_keys=False, allow_unicode=True)
        
    print(f"🚀 Sucesso! Arquivo gerado em: {arquivo_destino.resolve()}")

if __name__ == "__main__":
    gerar_contrato_openapi()