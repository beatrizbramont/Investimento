"""Testes do script de atualização que NÃO dependem de rede.

O download em si não é testado aqui (exigiria bater no Banco Central). O que
importa garantir é a parte que mexe no código-fonte: compor os anos, formatar o
bloco e reescrever `dados.py` sem corromper o arquivo.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from atualizar_dados import compor_por_ano, escrever_em_dados, formatar_bloco  # noqa: E402

SERIES_EXEMPLO = {
    "cdi": {2023: 13.03, 2024: 10.89},
    "poupanca": {2023: 8.04, 2024: 7.03},
    "ipca": {2023: 4.62, 2024: 4.83},
}


def test_compor_por_ano_compoe_meses_em_taxa_anual():
    """Doze meses de 1% compõem 12,68% ao ano, não 12%."""
    registros = [{"data": f"01/{mes:02d}/2024", "valor": "1.0"} for mes in range(1, 13)]
    assert compor_por_ano(registros) == {2024: pytest.approx(12.68, abs=0.01)}


def test_compor_por_ano_descarta_ano_incompleto():
    """O ano corrente só entra quando os doze meses estiverem publicados."""
    registros = [{"data": f"01/{mes:02d}/2026", "valor": "1.0"} for mes in range(1, 11)]
    assert compor_por_ano(registros) == {}


def test_formatar_bloco_inclui_os_marcadores():
    bloco = formatar_bloco(SERIES_EXEMPLO)
    assert bloco.lstrip().startswith("# BCB:INICIO")
    assert bloco.rstrip().endswith("# BCB:FIM")
    assert '"cdi": {' in bloco
    assert "2024: 10.89" in bloco


def _arquivo_exemplo(tmp_path: Path) -> Path:
    destino = tmp_path / "dados.py"
    destino.write_text(
        "ANTES = 1\n"
        "DADOS = {\n"
        "    # BCB:INICIO\n"
        '    "cdi": {2020: 1.0},\n'
        "    # BCB:FIM\n"
        '    "ibovespa": {2020: 2.92},\n'
        "}\n"
        "DEPOIS = 2\n",
        encoding="utf-8",
    )
    return destino


def test_escrever_preserva_o_que_esta_fora_dos_marcadores(tmp_path):
    destino = _arquivo_exemplo(tmp_path)
    escrever_em_dados(formatar_bloco(SERIES_EXEMPLO), destino)
    conteudo = destino.read_text(encoding="utf-8")

    assert "ANTES = 1" in conteudo
    assert "DEPOIS = 2" in conteudo
    assert '"ibovespa": {2020: 2.92},' in conteudo  # série da B3 fica intacta
    assert "2024: 10.89" in conteudo                # série do BCB foi atualizada
    assert "2020: 1.0" not in conteudo              # valor antigo foi embora


def test_escrever_e_idempotente(tmp_path):
    """Rodar duas vezes com os mesmos dados não pode sujar o arquivo.

    É isso que impede a GitHub Action de abrir um Pull Request vazio todo mês.
    """
    destino = _arquivo_exemplo(tmp_path)
    bloco = formatar_bloco(SERIES_EXEMPLO)

    assert escrever_em_dados(bloco, destino) is True
    primeira = destino.read_text(encoding="utf-8")

    assert escrever_em_dados(bloco, destino) is False
    assert destino.read_text(encoding="utf-8") == primeira


def test_escrever_falha_alto_se_os_marcadores_sumirem(tmp_path):
    destino = tmp_path / "dados.py"
    destino.write_text('DADOS = {"cdi": {}}\n', encoding="utf-8")

    with pytest.raises(SystemExit, match="Marcadores"):
        escrever_em_dados(formatar_bloco(SERIES_EXEMPLO), destino)
