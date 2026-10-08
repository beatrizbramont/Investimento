"""Testes do motor de cálculo.

O foco é garantir que as regras financeiras estejam certas — é o que distingue
um simulador confiável de uma planilha chutada.
"""

import pytest

from app import simulador
from app.dados import PRODUTOS_POR_ID


def test_taxa_mensal_e_equivalente_composta():
    """12% ao ano não são 1% ao mês."""
    mensal = simulador.taxa_mensal(12.0)
    assert mensal == pytest.approx(0.009489, abs=1e-6)
    # Doze meses compostos devem reconstruir a taxa anual original.
    assert (1 + mensal) ** 12 == pytest.approx(1.12, abs=1e-9)


@pytest.mark.parametrize(
    "dias, esperado",
    [(1, 0.225), (180, 0.225), (181, 0.20), (360, 0.20), (361, 0.175), (720, 0.175), (721, 0.15)],
)
def test_aliquota_regressiva_nos_limites(dias, esperado):
    assert simulador.aliquota_regressiva(dias) == esperado


def test_aporte_unico_cresce_com_juros_compostos():
    """R$ 1.000 a 12% a.a. por 1 ano devem virar R$ 1.120 brutos."""
    produto = PRODUTOS_POR_ID["cdb_100"]
    taxas = [simulador.taxa_mensal(12.0)] * 12
    resultado = simulador.simular_produto(
        produto, taxas, aporte_inicial=1000, aporte_mensal=0,
        rotulos=simulador.rotulos_projecao(12),
    )
    assert resultado.resumo.total_investido == 1000
    assert resultado.resumo.valor_bruto == pytest.approx(1120.0, abs=0.01)


def test_ir_incide_apenas_sobre_o_ganho():
    """Em 12 meses (360 dias) a alíquota é 20% e só sobre os R$ 120 de lucro."""
    produto = PRODUTOS_POR_ID["cdb_100"]
    taxas = [simulador.taxa_mensal(12.0)] * 12
    resultado = simulador.simular_produto(
        produto, taxas, aporte_inicial=1000, aporte_mensal=0,
        rotulos=simulador.rotulos_projecao(12),
    )
    assert resultado.resumo.imposto == pytest.approx(120 * 0.20, abs=0.01)
    assert resultado.resumo.valor_liquido == pytest.approx(1096.0, abs=0.01)


def test_produto_isento_nao_paga_imposto():
    produto = PRODUTOS_POR_ID["lci_90"]
    taxas = [simulador.taxa_mensal(12.0)] * 24
    resultado = simulador.simular_produto(
        produto, taxas, aporte_inicial=1000, aporte_mensal=0,
        rotulos=simulador.rotulos_projecao(24),
    )
    assert resultado.resumo.imposto == 0
    assert resultado.resumo.valor_liquido == resultado.resumo.valor_bruto


def test_ir_e_calculado_por_aporte_e_nao_pelo_saldo_total():
    """O aporte antigo paga 15% enquanto o recente ainda paga 22,5%.

    Se o cálculo usasse uma alíquota única para o saldo inteiro, o imposto cairia
    fora da faixa entre os dois extremos.
    """
    produto = PRODUTOS_POR_ID["cdb_100"]
    meses = 36
    taxas = [simulador.taxa_mensal(12.0)] * meses
    resultado = simulador.simular_produto(
        produto, taxas, aporte_inicial=0, aporte_mensal=1000,
        rotulos=simulador.rotulos_projecao(meses),
    )
    ganho_bruto = resultado.resumo.valor_bruto - resultado.resumo.total_investido
    aliquota_efetiva = resultado.resumo.imposto / ganho_bruto
    # Estritamente entre 15% e 22,5%: há lotes nas duas pontas da tabela.
    assert 0.15 < aliquota_efetiva < 0.225


def test_lci_isenta_supera_cdb_com_taxa_maior():
    """A lição central do simulador: taxa bruta não é o que importa."""
    meses = 60
    rotulos = simulador.rotulos_projecao(meses)
    cdb = PRODUTOS_POR_ID["cdb_100"]
    lci = PRODUTOS_POR_ID["lci_90"]

    r_cdb = simulador.simular_produto(
        cdb, simulador.taxas_mensais_projetadas(cdb, meses, {"cdi": 12.0}),
        1000, 500, rotulos,
    )
    r_lci = simulador.simular_produto(
        lci, simulador.taxas_mensais_projetadas(lci, meses, {"cdi": 12.0}),
        1000, 500, rotulos,
    )

    assert r_lci.resumo.valor_bruto < r_cdb.resumo.valor_bruto      # rende menos...
    assert r_lci.resumo.valor_liquido > r_cdb.resumo.valor_liquido  # ...mas sobra mais


def test_tesouro_ipca_compoe_inflacao_com_juro_real():
    """IPCA+ 6% com inflação de 4% deve render ~10,24%, não 10%."""
    produto = PRODUTOS_POR_ID["tesouro_ipca"]
    taxas = simulador.taxas_mensais_projetadas(produto, 12, {"ipca": 4.0})
    anual = (1 + taxas[0]) ** 12 - 1
    assert anual == pytest.approx(1.04 * 1.06 - 1, abs=1e-9)


def test_serie_tem_um_ponto_por_mes_e_investido_acumula():
    produto = PRODUTOS_POR_ID["poupanca"]
    anos = simulador.anos_do_periodo(5)
    taxas = simulador.taxas_mensais_historicas(produto, anos)
    resultado = simulador.simular_produto(
        produto, taxas, 1000, 500, simulador.rotulos_historicos(anos),
    )
    assert len(resultado.serie) == 60
    assert resultado.serie[0].investido == 1500      # inicial + 1º aporte
    assert resultado.serie[-1].investido == 1000 + 500 * 60


def test_aportes_corrigidos_valem_mais_que_a_soma_nominal():
    """Dinheiro depositado há dez anos vale mais, em poder de compra, que o de hoje."""
    anos = simulador.anos_do_periodo(10)
    inflacao = simulador.taxas_inflacao_mensais(anos)
    corrigido = simulador.investido_a_valor_de_hoje(inflacao, 1000, 500)
    nominal = 1000 + 500 * 120
    fator = simulador.inflacao_acumulada(inflacao)

    assert nominal < corrigido < nominal * fator  # entre o piso e o teto possíveis


def test_ganho_real_e_menor_que_o_ganho_nominal():
    produto = PRODUTOS_POR_ID["poupanca"]
    anos = simulador.anos_do_periodo(10)
    inflacao = simulador.taxas_inflacao_mensais(anos)
    resultado = simulador.simular_produto(
        produto,
        simulador.taxas_mensais_historicas(produto, anos),
        1000, 500, simulador.rotulos_historicos(anos),
    )
    simulador.aplicar_inflacao(
        resultado, simulador.investido_a_valor_de_hoje(inflacao, 1000, 500)
    )
    assert resultado.resumo.ganho_real < resultado.resumo.ganho_liquido
    assert resultado.resumo.rentabilidade_real_pct < resultado.resumo.rentabilidade_pct


def test_investido_a_valor_de_hoje_sem_inflacao_e_a_soma_nominal():
    assert simulador.investido_a_valor_de_hoje([0.0] * 12, 1000, 500) == pytest.approx(7000)


def test_anos_do_periodo_respeita_a_serie_disponivel():
    from app.dados import ANO_FINAL, ANO_INICIAL

    assert simulador.anos_do_periodo(3) == [ANO_FINAL - 2, ANO_FINAL - 1, ANO_FINAL]
    # Pedir mais anos do que existe na série devolve a série inteira.
    assert len(simulador.anos_do_periodo(99)) == ANO_FINAL - ANO_INICIAL + 1
