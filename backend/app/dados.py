"""Séries históricas e catálogo de produtos de investimento.

ATENÇÃO (leia antes de reutilizar estes números)
------------------------------------------------
As rentabilidades anuais abaixo são valores de domínio público reunidos para fins
educativos e estão ARREDONDADOS. Elas servem para ilustrar ordens de grandeza e o
comportamento relativo entre as classes de ativo -- não para tomar decisão real.

Para obter dados oficiais e sempre atualizados, rode `scripts/atualizar_dados.py`,
que consome a API SGS do Banco Central (séries 4391 = CDI acumulado no mês,
196 = poupança, 433 = IPCA). Ibovespa e IFIX vêm da B3.
"""

from dataclasses import dataclass, asdict

#: Último ano com série completa disponível neste arquivo.
ANO_FINAL = 2025
ANO_INICIAL = 2015

#: Rentabilidade nominal anual, em % ao ano.
#:
#: CDI, poupança e IPCA vêm da API SGS do Banco Central (séries 4391, 196 e 433),
#: compostas mês a mês por `scripts/atualizar_dados.py` — rode-o para atualizar.
#: Ibovespa e IFIX não existem no SGS e seguem como valores aproximados da B3.
RENTABILIDADE_ANUAL: dict[str, dict[int, float]] = {
    # BCB:INICIO — bloco gerado por `scripts/atualizar_dados.py --escrever`.
    # Não edite à mão: a GitHub Action reescreve tudo entre os marcadores.
    "cdi": {
        2015: 13.26, 2016: 13.99, 2017: 9.93, 2018: 6.41, 2019: 5.95,
        2020: 2.75, 2021: 4.44, 2022: 12.38, 2023: 13.03, 2024: 10.89,
        2025: 14.33,
    },
    "poupanca": {
        2015: 8.07, 2016: 8.3, 2017: 6.61, 2018: 4.62, 2019: 4.26,
        2020: 2.11, 2021: 2.99, 2022: 7.9, 2023: 8.04, 2024: 7.03,
        2025: 8.26,
    },
    "ipca": {
        2015: 10.67, 2016: 6.29, 2017: 2.95, 2018: 3.75, 2019: 4.31,
        2020: 4.52, 2021: 10.06, 2022: 5.78, 2023: 4.62, 2024: 4.83,
        2025: 4.26,
    },
    # BCB:FIM
    # Fonte: B3. 2025 conferido no fechamento oficial; anos anteriores são
    # aproximações de domínio público.
    "ibovespa": {
        2015: -13.31, 2016: 38.94, 2017: 26.86, 2018: 15.03, 2019: 31.58,
        2020: 2.92, 2021: -11.93, 2022: 4.69, 2023: 22.28, 2024: -10.36,
        2025: 33.95,
    },
    "ifix": {
        2015: 4.06, 2016: 32.29, 2017: 19.45, 2018: 5.63, 2019: 35.95,
        2020: -10.24, 2021: -2.28, 2022: 2.22, 2023: 15.50, 2024: -5.89,
        2025: 21.15,
    },
}

#: Taxas usadas no modo "projeção" quando o usuário não informa uma estimativa.
#: Refletem um cenário de médio prazo, não a taxa do dia.
PROJECAO_PADRAO = {
    "cdi": 10.5,
    "poupanca": 6.5,
    "ipca": 4.0,
    "ibovespa": 11.0,
    "ifix": 9.0,
}


@dataclass(frozen=True)
class Produto:
    """Um produto de investimento simulável.

    O rendimento é sempre derivado de um indexador (CDI, IPCA, Ibovespa...)
    aplicando `percentual_indexador` e somando `juros_adicional`. Assim um único
    motor de cálculo atende renda fixa pós-fixada, híbrida e renda variável.
    """

    id: str
    nome: str
    descricao: str
    categoria: str              # "renda_fixa" | "renda_variavel"
    indexador: str              # chave de RENTABILIDADE_ANUAL
    percentual_indexador: float  # 1.0 = 100% do indexador
    juros_adicional: float      # ex.: IPCA + 6% a.a. -> 0.06
    aliquota_ir: float | None   # None = IR regressivo da renda fixa
    isento_ir: bool
    risco: int                  # 1 (muito baixo) a 5 (muito alto)
    liquidez: str
    # Slots da paleta categórica validada (ver README > Design). A cor pertence ao
    # PRODUTO, não à sua posição no ranking: reordenar o gráfico não repinta nada.
    cor: str                    # modo claro
    cor_escura: str             # modo escuro


PRODUTOS: list[Produto] = [
    Produto(
        id="poupanca",
        nome="Poupança",
        descricao=(
            "A aplicação mais conhecida do Brasil e quase sempre a que menos rende. "
            "É isenta de Imposto de Renda, mas costuma perder do CDI e, em vários "
            "anos, até da inflação."
        ),
        categoria="renda_fixa",
        indexador="poupanca",
        percentual_indexador=1.0,
        juros_adicional=0.0,
        aliquota_ir=None,
        isento_ir=True,
        risco=1,
        liquidez="Diária, mas só rende no aniversário mensal",
        cor="#2a78d6",
        cor_escura="#3987e5",
    ),
    Produto(
        id="tesouro_selic",
        nome="Tesouro Selic",
        descricao=(
            "Título público pós-fixado que acompanha a Selic/CDI. É o investimento "
            "de menor risco do país e tem liquidez diária — o lugar natural da "
            "reserva de emergência."
        ),
        categoria="renda_fixa",
        indexador="cdi",
        percentual_indexador=1.0,
        juros_adicional=0.0,
        aliquota_ir=None,
        isento_ir=False,
        risco=1,
        liquidez="Diária (D+1)",
        cor="#1baf7a",
        cor_escura="#199e70",
    ),
    Produto(
        id="cdb_100",
        nome="CDB 100% do CDI",
        descricao=(
            "Empréstimo que você faz a um banco. Protegido pelo FGC até R$ 250 mil "
            "por instituição. Rende exatamente o CDI, com IR regressivo na retirada."
        ),
        categoria="renda_fixa",
        indexador="cdi",
        percentual_indexador=1.0,
        juros_adicional=0.0,
        aliquota_ir=None,
        isento_ir=False,
        risco=2,
        liquidez="Varia: de diária a só no vencimento",
        cor="#eda100",
        cor_escura="#c98500",
    ),
    Produto(
        id="cdb_120",
        nome="CDB 120% do CDI",
        descricao=(
            "Bancos médios pagam mais que os grandes porque precisam atrair "
            "captação. O risco de crédito é maior, mas o FGC cobre até R$ 250 mil."
        ),
        categoria="renda_fixa",
        indexador="cdi",
        percentual_indexador=1.20,
        juros_adicional=0.0,
        aliquota_ir=None,
        isento_ir=False,
        risco=3,
        liquidez="Em geral só no vencimento",
        cor="#008300",
        cor_escura="#008300",
    ),
    Produto(
        id="lci_90",
        nome="LCI/LCA 90% do CDI",
        descricao=(
            "Isenta de Imposto de Renda para pessoa física. Repare no gráfico: "
            "mesmo pagando 90% do CDI, ela costuma superar um CDB de 100% no "
            "líquido. É o melhor exemplo de por que taxa bruta não é tudo."
        ),
        categoria="renda_fixa",
        indexador="cdi",
        percentual_indexador=0.90,
        juros_adicional=0.0,
        aliquota_ir=None,
        isento_ir=True,
        risco=2,
        liquidez="Carência mínima de 9 meses",
        cor="#4a3aa7",
        cor_escura="#9085e9",
    ),
    Produto(
        id="tesouro_ipca",
        nome="Tesouro IPCA+ 6%",
        descricao=(
            "Paga a inflação do período MAIS 6% ao ano. Garante ganho real "
            "independente da inflação — por isso é o queridinho da aposentadoria."
        ),
        categoria="renda_fixa",
        indexador="ipca",
        percentual_indexador=1.0,
        juros_adicional=0.06,
        aliquota_ir=None,
        isento_ir=False,
        risco=2,
        liquidez="Diária, mas com marcação a mercado",
        cor="#e34948",
        cor_escura="#e66767",
    ),
    Produto(
        id="ibovespa",
        nome="Ações (ETF do Ibovespa)",
        descricao=(
            "Uma cota do BOVA11 compra, de uma vez, as maiores empresas da Bolsa. "
            "No longo prazo tende a render mais, mas o caminho tem quedas fortes — "
            "olhe 2015, 2021 e 2024 no gráfico."
        ),
        categoria="renda_variavel",
        indexador="ibovespa",
        percentual_indexador=1.0,
        juros_adicional=0.0,
        aliquota_ir=0.15,
        isento_ir=False,
        risco=5,
        liquidez="Diária (D+2)",
        cor="#e87ba4",
        cor_escura="#d55181",
    ),
    Produto(
        id="fiis",
        nome="Fundos Imobiliários (IFIX)",
        descricao=(
            "Você vira sócio de shoppings, galpões e lajes corporativas e recebe "
            "aluguel mensal. Simplificação do simulador: aplicamos 20% sobre todo o "
            "ganho; na vida real os dividendos são isentos, então o imposto é menor."
        ),
        categoria="renda_variavel",
        indexador="ifix",
        percentual_indexador=1.0,
        juros_adicional=0.0,
        aliquota_ir=0.20,
        isento_ir=False,
        risco=4,
        liquidez="Diária (D+2)",
        cor="#eb6834",
        cor_escura="#d95926",
    ),
]

PRODUTOS_POR_ID: dict[str, Produto] = {p.id: p for p in PRODUTOS}


def produto_como_dict(produto: Produto) -> dict:
    return asdict(produto)


#: Termos explicados nos tooltips do frontend.
GLOSSARIO: list[dict[str, str]] = [
    {
        "termo": "CDI",
        "definicao": (
            "Taxa de juros que os bancos cobram uns dos outros para emprestar "
            "dinheiro de um dia para o outro. Anda colada na Selic e virou a régua "
            "de toda a renda fixa: 'esse CDB paga 110% do CDI' significa 10% a mais "
            "que essa taxa."
        ),
    },
    {
        "termo": "Selic",
        "definicao": (
            "A taxa básica de juros da economia, definida a cada 45 dias pelo Copom "
            "(Banco Central). Quando a Selic sobe, a renda fixa fica mais atraente e "
            "a Bolsa costuma sofrer."
        ),
    },
    {
        "termo": "IPCA",
        "definicao": (
            "O índice oficial de inflação do Brasil. Se seu investimento rendeu 8% e "
            "o IPCA foi 5%, seu ganho real foi de apenas ~2,9% — o resto só repôs a "
            "perda de poder de compra."
        ),
    },
    {
        "termo": "Juros compostos",
        "definicao": (
            "Os juros de um mês passam a render juros no mês seguinte. É por isso que "
            "a curva do gráfico não é uma reta: ela acelera com o tempo. O ingrediente "
            "mais importante aqui não é a taxa, é o prazo."
        ),
    },
    {
        "termo": "IR regressivo",
        "definicao": (
            "Na renda fixa, quanto mais tempo você deixa o dinheiro aplicado, menos "
            "imposto paga sobre o lucro: 22,5% até 180 dias, 20% até 360, 17,5% até "
            "720 e 15% acima de 720 dias."
        ),
    },
    {
        "termo": "FGC",
        "definicao": (
            "Fundo Garantidor de Créditos. Se o banco onde você tem um CDB, LCI ou "
            "poupança quebrar, o FGC devolve até R$ 250 mil por CPF por instituição "
            "(teto global de R$ 1 milhão a cada 4 anos)."
        ),
    },
    {
        "termo": "Liquidez",
        "definicao": (
            "A rapidez com que você transforma o investimento em dinheiro na conta "
            "sem perder valor. Reserva de emergência exige liquidez diária; para "
            "objetivos distantes, abrir mão dela costuma render mais."
        ),
    },
    {
        "termo": "Rentabilidade real",
        "definicao": (
            "O que sobrou depois de descontar a inflação. É o único número que diz se "
            "você ficou mais rico de verdade — ganhar 10% com inflação de 10% é ficar "
            "no mesmo lugar."
        ),
    },
    {
        "termo": "Marcação a mercado",
        "definicao": (
            "O preço de um título prefixado ou IPCA+ oscila todo dia conforme os "
            "juros futuros. Se você levar até o vencimento recebe o combinado; se "
            "vender antes, pode receber mais ou menos que isso."
        ),
    },
    {
        "termo": "Diversificação",
        "definicao": (
            "Dividir o dinheiro entre ativos que não sobem e descem juntos. Não "
            "aumenta o retorno esperado, mas reduz o tamanho dos tombos — é o único "
            "'almoço grátis' reconhecido em finanças."
        ),
    },
]
