"""Fallback Humano — encaminha o pedido para um digitador da rede (nunca falha)."""


def generate(arte_path: str, params: dict) -> str:
    """Cria um ticket para um digitador humano e retorna o job em fila manual.

    E o localFallback do MaterialView-Pro: nao gera a matriz, mas garante
    que o pedido nunca fica sem resposta.
    """
    raise NotImplementedError("Integracao com sistema de tickets pendente.")
