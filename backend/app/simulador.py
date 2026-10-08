"""Motor de cálculo do simulador.

A ideia central é tratar cada aporte como um *lote* independente. Isso importa
porque o Imposto de Renda da renda fixa é regressivo: o dinheiro que entrou no
primeiro mês já está há anos aplicado e paga 15%, enquanto o aporte do mês
passado ainda paga 22,5%. Simuladores simplórios usam uma alíquota única para o
saldo inteiro e erram o valor líquido para cima.
"""

from dataclasses import dataclass

from .dados import (
    ANO_FINAL,
    ANO_INICIAL,
    PROJECAO_PADRAO,
    RENTABILIDADE_ANUAL,
    Produto,
)

#: Convenção da Receita Federal para contar o prazo de cada aplicação.
DIAS_POR_MES = 30


def aliquota_regressiva(dias: int) -> float:
    """Alíquota de IR da renda fixa conforme o prazo da aplicação."""
    if dias <= 180:
        return 0.225
    if dias <= 360:
        return 0.20
    if dias <= 720:
        return 0.175
    return 0.15


def taxa_mensal(taxa_anual_pct: float) -> float:
    """Converte % ao ano em taxa mensal equivalente (juros compostos).

    Usamos a raiz décima-segunda, não a divisão por 12: 12% ao ano não são 1% ao
    mês, são 0,949% ao mês.
    """
    return (1 + taxa_anual_pct / 100) ** (1 / 12) - 1


def _rentabilidade_anual_do_produto(produto: Produto, ano: int) -> float:
    """Rentabilidade nominal (% a.a.) do produto em um ano histórico."""
    base = RENTABILIDADE_ANUAL[produto.indexador][ano]
    return _combinar(base, produto)


def _combinar(base_pct: float, produto: Produto) -> float:
    """Aplica percentual do indexador e juros adicionais sobre a taxa base."""
    indexado = base_pct * produto.percentual_indexador
    if produto.juros_adicional:
        # IPCA+ é composição, não soma: (1+IPCA) * (1+juros) - 1.
        return ((1 + indexado / 100) * (1 + produto.juros_adicional) - 1) * 100
    return indexado


def anos_do_periodo(anos: int) -> list[int]:
    """Os `anos` mais recentes disponíveis na série histórica."""
    anos = max(1, min(anos, ANO_FINAL - ANO_INICIAL + 1))
    return list(range(ANO_FINAL - anos + 1, ANO_FINAL + 1))


def taxas_mensais_historicas(produto: Produto, anos: list[int]) -> list[float]:
    """Uma taxa mensal por mês do período, derivada do retorno real de cada ano."""
    return [taxa_mensal(_rentabilidade_anual_do_produto(produto, ano)) for ano in anos for _ in range(12)]


def taxas_mensais_projetadas(produto: Produto, meses: int, premissas: dict[str, float]) -> list[float]:
    """Taxa mensal constante, derivada das premissas de cenário futuro."""
    base = premissas.get(produto.indexador, PROJECAO_PADRAO[produto.indexador])
    return [taxa_mensal(_combinar(base, produto))] * meses


@dataclass
class _Lote:
    """Um aporte individual e sua evolução."""

    mes_entrada: int
    custo: float
    bruto: float


@dataclass
class PontoSerie:
    mes: int
    rotulo: str
    investido: float
    bruto: float
    liquido: float


@dataclass
class Resumo:
    total_investido: float
    valor_bruto: float
    imposto: float
    valor_liquido: float
    ganho_liquido: float
    rentabilidade_pct: float
    investido_corrigido: float   # aportes trazidos a valor de hoje pelo IPCA
    ganho_real: float            # quanto sobrou ACIMA da inflação
    rentabilidade_real_pct: float


@dataclass
class ResultadoProduto:
    produto_id: str
    serie: list[PontoSerie]
    resumo: Resumo


def _imposto_do_lote(lote: _Lote, mes_atual: int, produto: Produto) -> float:
    """IR devido se o lote fosse resgatado agora."""
    ganho = lote.bruto - lote.custo
    if produto.isento_ir or ganho <= 0:
        return 0.0
    if produto.aliquota_ir is not None:
        return ganho * produto.aliquota_ir
    dias = (mes_atual - lote.mes_entrada + 1) * DIAS_POR_MES
    return ganho * aliquota_regressiva(dias)


def simular_produto(
    produto: Produto,
    taxas: list[float],
    aporte_inicial: float,
    aporte_mensal: float,
    rotulos: list[str],
) -> ResultadoProduto:
    """Evolui mês a mês o saldo do produto e devolve série + resumo.

    Em cada mês o aporte entra ANTES do rendimento, e a série já registra quanto
    sobraria no bolso caso o resgate acontecesse naquele mês (coluna `liquido`).
    """
    lotes: list[_Lote] = []
    serie: list[PontoSerie] = []
    investido = 0.0

    for mes, taxa in enumerate(taxas):
        # No primeiro mês entram o valor inicial e o primeiro aporte mensal.
        aporte = aporte_mensal + (aporte_inicial if mes == 0 else 0.0)
        if aporte > 0:
            lotes.append(_Lote(mes_entrada=mes, custo=aporte, bruto=aporte))
            investido += aporte

        for lote in lotes:
            lote.bruto *= 1 + taxa

        bruto = sum(lote.bruto for lote in lotes)
        imposto = sum(_imposto_do_lote(lote, mes, produto) for lote in lotes)
        serie.append(
            PontoSerie(
                mes=mes + 1,
                rotulo=rotulos[mes],
                investido=round(investido, 2),
                bruto=round(bruto, 2),
                liquido=round(bruto - imposto, 2),
            )
        )

    final = serie[-1]
    ganho_liquido = final.liquido - final.investido
    rentabilidade = (final.liquido / final.investido - 1) * 100 if final.investido else 0.0

    return ResultadoProduto(
        produto_id=produto.id,
        serie=serie,
        resumo=Resumo(
            total_investido=final.investido,
            valor_bruto=final.bruto,
            imposto=round(final.bruto - final.liquido, 2),
            valor_liquido=final.liquido,
            ganho_liquido=round(ganho_liquido, 2),
            rentabilidade_pct=round(rentabilidade, 2),
            investido_corrigido=0.0,  # preenchidos por `aplicar_inflacao`
            ganho_real=0.0,
            rentabilidade_real_pct=0.0,
        ),
    )


def taxas_inflacao_mensais(anos: list[int]) -> list[float]:
    """IPCA mensal equivalente para cada mês do período histórico."""
    return [taxa_mensal(RENTABILIDADE_ANUAL["ipca"][ano]) for ano in anos for _ in range(12)]


def inflacao_acumulada(taxas_inflacao: list[float]) -> float:
    """Fator de inflação do período (1.35 = preços subiram 35%)."""
    fator = 1.0
    for taxa in taxas_inflacao:
        fator *= 1 + taxa
    return fator


def investido_a_valor_de_hoje(
    taxas_inflacao: list[float], aporte_inicial: float, aporte_mensal: float
) -> float:
    """Soma dos aportes corrigidos pelo IPCA até o fim do período.

    Comparar o saldo final com a soma nominal dos aportes é injusto: os R$ 500
    depositados há dez anos valiam muito mais do que os R$ 500 do mês passado.
    Corrigindo cada aporte pela inflação do seu próprio período, a diferença para
    o saldo final passa a ser ganho de poder de compra de verdade.
    """
    # fatores[m] = inflação acumulada do mês m até o fim.
    fatores: list[float] = [1.0] * len(taxas_inflacao)
    acumulado = 1.0
    for mes in reversed(range(len(taxas_inflacao))):
        acumulado *= 1 + taxas_inflacao[mes]
        fatores[mes] = acumulado

    total = 0.0
    for mes, fator in enumerate(fatores):
        aporte = aporte_mensal + (aporte_inicial if mes == 0 else 0.0)
        total += aporte * fator
    return total


def aplicar_inflacao(resultado: ResultadoProduto, investido_corrigido: float) -> None:
    """Preenche os indicadores de ganho real do resumo."""
    resumo = resultado.resumo
    resumo.investido_corrigido = round(investido_corrigido, 2)
    resumo.ganho_real = round(resumo.valor_liquido - investido_corrigido, 2)
    if investido_corrigido:
        resumo.rentabilidade_real_pct = round(
            (resumo.valor_liquido / investido_corrigido - 1) * 100, 2
        )


def rotulos_historicos(anos: list[int]) -> list[str]:
    return [f"{ano}-{mes:02d}" for ano in anos for mes in range(1, 13)]


def rotulos_projecao(meses: int) -> list[str]:
    return [f"Mês {m}" for m in range(1, meses + 1)]
