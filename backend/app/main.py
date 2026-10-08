"""API do Investe Simples.

Rode em desenvolvimento com:
    uvicorn app.main:app --reload
Documentação interativa: http://127.0.0.1:8000/docs
"""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import simulador
from .dados import ANO_FINAL, GLOSSARIO, PRODUTOS, PRODUTOS_POR_ID, produto_como_dict
from .schemas import SimulacaoRequest, SimulacaoResponse, ProdutoOut, TermoOut

app = FastAPI(
    title="Investe Simples",
    description=(
        "API educativa que simula e compara investimentos brasileiros. "
        "Os dados são aproximados e não constituem recomendação de investimento."
    ),
    version="1.0.0",
)

# O frontend roda em outra porta durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/saude", tags=["meta"])
def saude() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/produtos", response_model=list[ProdutoOut], tags=["catálogo"])
def listar_produtos() -> list[dict]:
    """Catálogo de produtos disponíveis para simulação."""
    return [produto_como_dict(p) for p in PRODUTOS]


@app.get("/api/glossario", response_model=list[TermoOut], tags=["catálogo"])
def listar_glossario() -> list[dict[str, str]]:
    """Termos de investimento explicados em linguagem simples."""
    return GLOSSARIO


@app.post("/api/simular", response_model=SimulacaoResponse, tags=["simulação"])
def simular(req: SimulacaoRequest) -> dict:
    """Simula a evolução de um plano de aportes em vários produtos ao mesmo tempo."""
    try:
        req.validar_aportes()
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    meses = req.anos * 12
    historico = req.modo == "historico"

    premissas = req.premissas.preenchidas()

    if historico:
        anos = simulador.anos_do_periodo(req.anos)
        rotulos = simulador.rotulos_historicos(anos)
        inflacao_mensal = simulador.taxas_inflacao_mensais(anos)
    else:
        anos = []
        rotulos = simulador.rotulos_projecao(meses)
        ipca_estimado = premissas.get("ipca", simulador.PROJECAO_PADRAO["ipca"])
        inflacao_mensal = [simulador.taxa_mensal(ipca_estimado)] * meses

    inicio, fim = rotulos[0], rotulos[-1]
    fator_inflacao = simulador.inflacao_acumulada(inflacao_mensal)
    investido_corrigido = simulador.investido_a_valor_de_hoje(
        inflacao_mensal, req.aporte_inicial, req.aporte_mensal
    )

    resultados = []
    for produto_id in req.produtos:
        produto = PRODUTOS_POR_ID[produto_id]
        if historico:
            taxas = simulador.taxas_mensais_historicas(produto, anos)
        else:
            taxas = simulador.taxas_mensais_projetadas(produto, meses, premissas)

        resultado = simulador.simular_produto(
            produto=produto,
            taxas=taxas,
            aporte_inicial=req.aporte_inicial,
            aporte_mensal=req.aporte_mensal,
            rotulos=rotulos,
        )
        simulador.aplicar_inflacao(resultado, investido_corrigido)
        resultados.append(
            {
                "produto": produto_como_dict(produto),
                "serie": [asdict(p) for p in resultado.serie],
                "resumo": asdict(resultado.resumo),
            }
        )

    # Do melhor para o pior líquido — o frontend confia nessa ordem na legenda.
    resultados.sort(key=lambda r: r["resumo"]["valor_liquido"], reverse=True)

    return {
        "periodo": {
            "modo": req.modo,
            "inicio": inicio,
            "fim": fim,
            "meses": meses,
            "inflacao_acumulada_pct": round((fator_inflacao - 1) * 100, 2),
        },
        "total_investido": resultados[0]["resumo"]["total_investido"],
        "investido_corrigido": round(investido_corrigido, 2),
        "resultados": resultados,
        "observacoes": _observacoes(historico),
    }


def _observacoes(historico: bool) -> list[str]:
    """Ressalvas exibidas abaixo da tabela.

    Mantidas curtas de propósito: cada linha existe para evitar que o usuário
    tire uma conclusão errada. Detalhe de metodologia fica no README.
    """
    notas = [
        "Os valores líquidos já descontam o Imposto de Renda do resgate.",
        "Fora da conta: taxa de administração, corretagem, IOF e come-cotas.",
    ]
    if historico:
        notas.append(
            f"A série termina em dezembro de {ANO_FINAL}. O ano em curso fica de fora "
            "porque cada índice é publicado num ritmo diferente — o IPCA sai com "
            "atraso — e comparar períodos desiguais distorceria o ganho real."
        )
        notas.append("Rentabilidade passada não garante rentabilidade futura.")
    else:
        notas.append("A projeção repete a mesma taxa todo mês — a realidade oscila.")
    return notas
