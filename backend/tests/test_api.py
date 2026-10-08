"""Testes dos endpoints HTTP."""

import pytest
from fastapi.testclient import TestClient

from app.dados import ANO_FINAL
from app.main import app

cliente = TestClient(app)


def test_saude():
    assert cliente.get("/api/saude").json() == {"status": "ok"}


def test_listar_produtos():
    resposta = cliente.get("/api/produtos")
    assert resposta.status_code == 200
    produtos = resposta.json()
    assert len(produtos) == 8
    assert {p["id"] for p in produtos} >= {"poupanca", "lci_90", "ibovespa"}


def test_glossario_tem_termos_essenciais():
    termos = {t["termo"] for t in cliente.get("/api/glossario").json()}
    assert {"CDI", "IPCA", "Juros compostos", "FGC"} <= termos


def test_simulacao_historica_completa():
    resposta = cliente.post(
        "/api/simular",
        json={"aporte_inicial": 1000, "aporte_mensal": 500, "anos": 10, "modo": "historico"},
    )
    assert resposta.status_code == 200
    dados = resposta.json()

    assert dados["periodo"]["meses"] == 120
    assert dados["periodo"]["inicio"] == f"{ANO_FINAL - 9}-01"
    assert dados["periodo"]["fim"] == f"{ANO_FINAL}-12"
    assert dados["total_investido"] == 1000 + 500 * 120
    assert len(dados["resultados"]) == 8
    assert all(len(r["serie"]) == 120 for r in dados["resultados"])


def test_resultados_vem_ordenados_do_melhor_para_o_pior():
    dados = cliente.post("/api/simular", json={"anos": 10}).json()
    liquidos = [r["resumo"]["valor_liquido"] for r in dados["resultados"]]
    assert liquidos == sorted(liquidos, reverse=True)


def test_poupanca_perde_do_tesouro_selic_no_historico():
    """Resultado conhecido do período: a poupança fica para trás."""
    dados = cliente.post(
        "/api/simular",
        json={"anos": 10, "produtos": ["poupanca", "tesouro_selic"]},
    ).json()
    por_id = {r["produto"]["id"]: r["resumo"] for r in dados["resultados"]}
    assert por_id["poupanca"]["valor_liquido"] < por_id["tesouro_selic"]["valor_liquido"]


def test_modo_projecao_usa_premissas_informadas():
    dados = cliente.post(
        "/api/simular",
        json={
            "aporte_inicial": 0,
            "aporte_mensal": 1000,
            "anos": 5,
            "modo": "projecao",
            "produtos": ["cdb_100"],
            "premissas": {"cdi": 12.0},
        },
    ).json()
    assert dados["periodo"]["modo"] == "projecao"
    assert dados["periodo"]["inicio"] == "Mês 1"
    assert dados["total_investido"] == 60_000
    assert dados["resultados"][0]["resumo"]["valor_bruto"] > 60_000


def test_produto_desconhecido_e_rejeitado():
    resposta = cliente.post("/api/simular", json={"produtos": ["bitcoin"]})
    assert resposta.status_code == 422


def test_simulacao_sem_nenhum_aporte_e_rejeitada():
    resposta = cliente.post(
        "/api/simular", json={"aporte_inicial": 0, "aporte_mensal": 0}
    )
    assert resposta.status_code == 422


@pytest.mark.parametrize("anos", [0, 11])
def test_prazo_fora_do_intervalo_e_rejeitado(anos):
    assert cliente.post("/api/simular", json={"anos": anos}).status_code == 422
