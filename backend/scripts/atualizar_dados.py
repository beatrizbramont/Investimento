"""Baixa as séries oficiais do Banco Central e gera as tabelas de `dados.py`.

As séries do SGS vêm em variação MENSAL (% ao mês). O script compõe os doze meses
de cada ano para chegar ao % ao ano que o simulador usa.

Uso:
    python scripts/atualizar_dados.py                 # imprime o bloco Python
    python scripts/atualizar_dados.py --inicio 2010   # período maior

Ibovespa e IFIX não estão no SGS — continuam vindo da B3 e precisam ser
atualizados à mão em `app/dados.py`.
"""

import argparse
import re
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

import httpx

SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

#: código da série no SGS -> chave usada em RENTABILIDADE_ANUAL
SERIES = {
    4391: "cdi",       # CDI acumulado no mês
    196: "poupanca",   # Rendimento mensal da poupança (regra pós-maio/2012)
    433: "ipca",       # IPCA — variação mensal
}


#: O SGS costuma devolver timeout esporádico; vale insistir antes de desistir.
TENTATIVAS = 3


def baixar_serie(codigo: int, inicio: int, fim: int) -> list[dict]:
    try:
        resposta = _get_com_retry(codigo, inicio, fim)
    except httpx.ConnectError as erro:
        if "CERTIFICATE_VERIFY_FAILED" in str(erro):
            raise SystemExit(
                "Falha ao validar o certificado TLS.\n\n"
                "Redes corporativas costumam inspecionar o tráfego com um "
                "certificado raiz próprio. Exporte o CA da sua empresa e aponte "
                "a variável de ambiente para ele antes de rodar:\n"
                "    Windows:  $env:SSL_CERT_FILE = 'C:\\caminho\\ca-empresa.pem'\n"
                "    Linux:    export SSL_CERT_FILE=/caminho/ca-empresa.pem"
            ) from erro
        raise SystemExit(f"Não consegui falar com a API do Banco Central: {erro}") from erro
    except httpx.TimeoutException as erro:
        raise SystemExit(
            f"A API do Banco Central não respondeu após {TENTATIVAS} tentativas. "
            "Tente de novo em alguns minutos."
        ) from erro

    resposta.raise_for_status()
    return resposta.json()


def _get_com_retry(codigo: int, inicio: int, fim: int) -> httpx.Response:
    """GET com nova tentativa em timeout, esperando um pouco mais a cada vez."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return httpx.get(
                SGS.format(codigo=codigo),
                params={
                    "formato": "json",
                    "dataInicial": f"01/01/{inicio}",
                    "dataFinal": f"31/12/{fim}",
                },
                timeout=30,
            )
        except httpx.TimeoutException:
            if tentativa == TENTATIVAS:
                raise
            time.sleep(2 * tentativa)
    raise AssertionError("inalcançável")


def compor_por_ano(registros: list[dict]) -> dict[int, float]:
    """Compõe as variações mensais em rentabilidade anual (% a.a.)."""
    mensais: dict[int, list[float]] = defaultdict(list)
    for registro in registros:
        ano = int(registro["data"].split("/")[-1])
        mensais[ano].append(float(registro["valor"]) / 100)

    anuais: dict[int, float] = {}
    for ano, valores in sorted(mensais.items()):
        if len(valores) < 12:
            continue  # ano incompleto: não dá para anualizar com honestidade
        fator = 1.0
        for valor in valores:
            fator *= 1 + valor
        anuais[ano] = round((fator - 1) * 100, 2)
    return anuais


def formatar_bloco(series: dict[str, dict[int, float]]) -> str:
    """Monta o trecho Python que vai entre os marcadores de `dados.py`."""
    linhas = [
        "    # BCB:INICIO — bloco gerado por `scripts/atualizar_dados.py --escrever`.",
        "    # Não edite à mão: a GitHub Action reescreve tudo entre os marcadores.",
    ]
    for chave, anuais in series.items():
        linhas.append(f'    "{chave}": {{')
        itens = [f"{ano}: {valor}" for ano, valor in sorted(anuais.items())]
        # Cinco anos por linha mantém o arquivo legível no diff do Pull Request.
        for i in range(0, len(itens), 5):
            linhas.append("        " + ", ".join(itens[i : i + 5]) + ",")
        linhas.append("    },")
    linhas.append("    # BCB:FIM")
    return "\n".join(linhas)


def escrever_em_dados(bloco: str, destino: Path) -> bool:
    """Substitui o trecho entre os marcadores. Devolve True se algo mudou."""
    original = destino.read_text(encoding="utf-8")
    padrao = re.compile(
        r"^[ \t]*# BCB:INICIO.*?^[ \t]*# BCB:FIM[ \t]*$",
        re.DOTALL | re.MULTILINE,
    )
    if not padrao.search(original):
        raise SystemExit(
            f"Marcadores '# BCB:INICIO' e '# BCB:FIM' não encontrados em {destino}."
        )

    atualizado = padrao.sub(lambda _: bloco, original, count=1)
    if atualizado == original:
        return False
    destino.write_text(atualizado, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inicio", type=int, default=2015)
    parser.add_argument("--fim", type=int, default=date.today().year)
    parser.add_argument(
        "--escrever",
        action="store_true",
        help="grava direto em app/dados.py em vez de imprimir na tela",
    )
    args = parser.parse_args()

    series = {
        chave: compor_por_ano(baixar_serie(codigo, args.inicio, args.fim))
        for codigo, chave in SERIES.items()
    }

    vazias = [chave for chave, anuais in series.items() if not anuais]
    if vazias:
        raise SystemExit(f"Séries vieram vazias do BCB: {', '.join(vazias)}")

    bloco = formatar_bloco(series)

    if not args.escrever:
        print(bloco)
        return

    destino = Path(__file__).resolve().parent.parent / "app" / "dados.py"
    if escrever_em_dados(bloco, destino):
        ultimo = max(max(anuais) for anuais in series.values())
        print(f"{destino} atualizado — séries completas até {ultimo}.")
    else:
        print("Nada mudou: os dados do BCB já estão iguais aos do arquivo.")


if __name__ == "__main__":
    main()
