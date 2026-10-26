from app.models.conteudo import ConteudoBoasVindas


class ConteudoRepository:
    def __init__(self, boas_vindas: ConteudoBoasVindas):
        boas_vindas.passos = sorted(boas_vindas.passos, key=lambda p: p.ordem)
        self._boas_vindas = boas_vindas

    def obter_boas_vindas(self) -> ConteudoBoasVindas:
        return self._boas_vindas
