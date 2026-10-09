"""Contratos de entrada e saída da API (validados pelo Pydantic)."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .dados import PRODUTOS_POR_ID


class PremissasProjecao(BaseModel):
    """Taxas anuais estimadas para o modo projeção (% ao ano)."""

    cdi: float | None = Field(default=None, ge=0, le=50)
    poupanca: float | None = Field(default=None, ge=0, le=50)
    ipca: float | None = Field(default=None, ge=0, le=50)
    ibovespa: float | None = Field(default=None, ge=-50, le=50)
    ifix: float | None = Field(default=None, ge=-50, le=50)

    def preenchidas(self) -> dict[str, float]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class SimulacaoRequest(BaseModel):
    aporte_inicial: float = Field(default=1000, ge=0, le=100_000_000)
    aporte_mensal: float = Field(default=500, ge=0, le=10_000_000)
    anos: int = Field(default=10, ge=1, le=10)
    #: Prazo em meses. Tem prioridade sobre `anos`, que fica como atalho para
    #: quem só quer períodos redondos.
    meses: int | None = Field(default=None, ge=1, le=120)
    modo: Literal["historico", "projecao"] = "historico"
    produtos: list[str] = Field(default_factory=lambda: list(PRODUTOS_POR_ID))
    premissas: PremissasProjecao = Field(default_factory=PremissasProjecao)

    @property
    def total_meses(self) -> int:
        return self.meses if self.meses is not None else self.anos * 12

    @field_validator("produtos")
    @classmethod
    def validar_produtos(cls, valor: list[str]) -> list[str]:
        desconhecidos = [p for p in valor if p not in PRODUTOS_POR_ID]
        if desconhecidos:
            raise ValueError(f"produto(s) desconhecido(s): {', '.join(desconhecidos)}")
        if not valor:
            raise ValueError("selecione ao menos um produto")
        return valor

    def validar_aportes(self) -> None:
        if self.aporte_inicial == 0 and self.aporte_mensal == 0:
            raise ValueError("informe um aporte inicial ou um aporte mensal")


class PontoSerieOut(BaseModel):
    mes: int
    rotulo: str
    investido: float
    bruto: float
    liquido: float


class ResumoOut(BaseModel):
    total_investido: float
    valor_bruto: float
    imposto: float
    valor_liquido: float
    ganho_liquido: float
    rentabilidade_pct: float
    investido_corrigido: float
    ganho_real: float
    rentabilidade_real_pct: float


class ProdutoOut(BaseModel):
    id: str
    nome: str
    descricao: str
    categoria: str
    indexador: str
    percentual_indexador: float
    juros_adicional: float
    aliquota_ir: float | None
    isento_ir: bool
    risco: int
    liquidez: str
    cor: str
    cor_escura: str


class ResultadoOut(BaseModel):
    produto: ProdutoOut
    serie: list[PontoSerieOut]
    resumo: ResumoOut


class PeriodoOut(BaseModel):
    modo: str
    inicio: str
    fim: str
    meses: int
    inflacao_acumulada_pct: float


class SimulacaoResponse(BaseModel):
    periodo: PeriodoOut
    total_investido: float
    investido_corrigido: float
    resultados: list[ResultadoOut]
    observacoes: list[str]


class TermoOut(BaseModel):
    termo: str
    definicao: str
