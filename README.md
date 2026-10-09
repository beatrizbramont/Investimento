# Investe Simples

Simulador educativo que mostra, com dados do mercado brasileiro, o que teria
acontecido com o seu dinheiro em cada tipo de investimento.

A maioria das calculadoras de banco responde "quanto rende". Esta responde a
pergunta que importa: **quanto sobra depois do imposto e da inflação** — e por que
duas aplicações com a mesma taxa anunciada terminam com saldos diferentes.

> ⚠️ Material educativo. Não é recomendação de investimento, e as séries
> históricas embutidas são aproximadas (veja [Dados](#dados)).

---

## O que ele faz

| | |
|---|---|
| **Compara 8 investimentos** | Poupança, Tesouro Selic, Tesouro IPCA+, CDB 100% e 120% do CDI, LCI/LCA, ETF de Ibovespa e fundos imobiliários |
| **Modo histórico** | Aplica a rentabilidade que cada classe realmente teve entre 2016 e 2025 |
| **Modo projeção** | Repete uma taxa estimada, com o CDI futuro ajustável |
| **Bruto × líquido** | Um clique alterna entre o número que o banco anuncia e o que sobra na conta |
| **Ganho real** | Corrige cada aporte pelo IPCA para mostrar o ganho de poder de compra |

### As três lições que o simulador ensina sozinho

1. **Taxa bruta não é o que importa.** Uma LCI que paga 90% do CDI termina acima
   de um CDB de 100% do CDI, porque é isenta de Imposto de Renda. Alterne entre
   "Bruto" e "Líquido" no gráfico e veja as linhas trocarem de posição.
2. **Inflação come quase tudo.** Com aportes de R$ 500/mês entre 2016 e 2025, a
   poupança rendeu **+38,3% nominais** e apenas **+5,4% acima da inflação** —
   enquanto um CDB de 120% do CDI entregou **+31% reais** no mesmo período.
3. **Prazo pesa mais que taxa.** O IR da renda fixa cai de 22,5% para 15% conforme
   o dinheiro envelhece — e os juros compostos aceleram no fim da curva.

---

## Stack

**Backend** — Python 3.11+ · FastAPI · Pydantic v2 · pytest
**Frontend** — React 18 · Vite · Recharts

Sem banco de dados e sem dependência de API externa em tempo de execução: a
simulação é determinística e roda offline.

---

## Como rodar

Você vai precisar de **dois terminais**.

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API em `http://127.0.0.1:8000` · documentação interativa em
`http://127.0.0.1:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Site em `http://localhost:5173`. O Vite faz proxy de `/api` para o backend, então
não há configuração de CORS para ajustar em desenvolvimento.

### Testes

```bash
cd backend
pytest
```

---

## Como o cálculo funciona

### Cada aporte é um lote independente

O ponto onde a maioria dos simuladores erra. O Imposto de Renda da renda fixa é
**regressivo** — cai conforme o dinheiro envelhece:

| Prazo da aplicação | Alíquota |
|---|---|
| até 180 dias | 22,5% |
| 181 a 360 dias | 20% |
| 361 a 720 dias | 17,5% |
| acima de 720 dias | 15% |

Quem aporta todo mês tem dinheiro de várias idades ao mesmo tempo. Aplicar uma
alíquota única sobre o saldo inteiro superestima o valor líquido. Aqui cada aporte
é rastreado como um lote com a sua própria data de entrada e o seu próprio imposto
(`backend/app/simulador.py`).

### Taxa mensal é raiz, não divisão

12% ao ano **não** são 1% ao mês. A taxa mensal equivalente é
`(1 + 0,12)^(1/12) − 1 = 0,949%`.

### Ganho real compara maçãs com maçãs

Comparar o saldo final com a soma nominal dos aportes é injusto: os R$ 500
depositados em 2015 valiam muito mais do que os R$ 500 do mês passado. O simulador
corrige **cada aporte pelo IPCA do seu próprio período** antes de calcular o ganho
real.

### Tesouro IPCA+ compõe, não soma

`IPCA + 6%` com inflação de 4% rende 10,24% ao ano, não 10%:
`(1 + 0,04) × (1 + 0,06) − 1`.

---

## API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/produtos` | Catálogo com descrição, risco, liquidez e tributação |
| `GET` | `/api/glossario` | Termos de investimento em linguagem simples |
| `POST` | `/api/simular` | Roda a simulação e devolve série mensal + resumo |
| `GET` | `/api/saude` | Health check |

<details>
<summary>Exemplo de requisição</summary>

```bash
curl -X POST http://127.0.0.1:8000/api/simular \
  -H "Content-Type: application/json" \
  -d '{
        "aporte_inicial": 1000,
        "aporte_mensal": 500,
        "meses": 120,
        "modo": "historico",
        "produtos": ["poupanca", "lci_90", "tesouro_ipca"]
      }'
```

O prazo vai em `meses` (1 a 120), o que permite períodos quebrados como 7 meses.
O campo `anos` continua aceito como atalho para períodos redondos; se os dois
vierem, `meses` prevalece.

No modo `historico` a série termina sempre em dezembro de `ANO_FINAL` e anda para
trás a partir dali. No modo `projecao` ela começa no mês corrente. Os dois usam o
mesmo formato de rótulo (`"AAAA-MM"`), então o eixo do gráfico é o mesmo.

</details>

---

## Dados

| Série | Fonte | Como atualiza |
|---|---|---|
| CDI, poupança, IPCA | [API SGS do Banco Central](https://dadosabertos.bcb.gov.br/) (4391, 196, 433) | **Automático** — GitHub Action mensal |
| Ibovespa, IFIX | [B3](https://www.b3.com.br/) | Manual (não existem no SGS) |

```bash
cd backend
python scripts/atualizar_dados.py             # imprime o bloco na tela
python scripts/atualizar_dados.py --escrever  # grava direto em app/dados.py
```

O `--escrever` troca apenas o trecho entre os marcadores `# BCB:INICIO` e
`# BCB:FIM`; o resto do arquivo fica intacto. A operação é idempotente — rodar
duas vezes com os mesmos dados não altera nada, que é o que impede a Action de
abrir Pull Request vazio todo mês.

### Por que o ano corrente não aparece

Só entram anos com os **doze meses publicados**. Cada índice sai num ritmo
diferente — em outubro de 2026, o CDI já tinha dez meses divulgados e o IPCA
apenas oito. Compor um ano a partir de períodos desiguais faria o cálculo de
ganho real comparar coisas diferentes, então o script descarta anos incompletos.

### O que fica de fora da conta

Taxa de administração, corretagem, IOF em resgates com menos de 30 dias,
come-cotas de fundos e marcação a mercado de títulos vendidos antes do
vencimento.

---

## Deploy

O projeto vai inteiro para a **Vercel** — frontend estático e backend como função
serverless, numa única URL e sem hibernação. A configuração está em `vercel.json`:

| Caminho | Destino |
|---|---|
| `/api/*` | `api/index.py` — função Python que expõe o mesmo app FastAPI |
| `/` | `frontend/index.html` |
| resto | `frontend/$1` (assets compilados) |

`api/index.py` não duplica código: ele apenas importa `backend/app`, e o
`includeFiles` do `vercel.json` garante que essa pasta seja empacotada junto com a
função. As dependências de produção ficam em `api/requirements.txt` (só FastAPI e
Pydantic — uvicorn e pytest não sobem).

> **Por que as rotas apontam para `/frontend/…` e não para a raiz**
>
> O `@vercel/static-build` publica o conteúdo de `distDir` sob o prefixo do
> diretório onde está o `package.json` de origem. Como o nosso vive em
> `frontend/`, o `index.html` compilado fica em `/frontend/index.html` — não em
> `/index.html`. Apontar as rotas para a raiz faz o site inteiro responder 404
> enquanto a função Python continua funcionando normalmente, o que torna o
> sintoma confuso de diagnosticar.

```bash
npm i -g vercel
vercel          # primeira vez: cria o projeto e faz preview
vercel --prod   # publica
```

Ou conecte o repositório em [vercel.com/new](https://vercel.com/new) para publicar
a cada `git push`.

> Em produção, frontend e API ficam na mesma origem — não há CORS a configurar.

---

## Decisões de design

As cores das séries saem da paleta categórica de 8 slots validada para daltonismo
(ΔE mínimo entre pares adjacentes de 24,2 no modo claro). Cada cor pertence ao
**produto**, não à sua posição no ranking — filtrar investimentos reordena o
gráfico sem repintar as linhas que ficaram.

Como três slots do modo claro ficam abaixo de 3:1 de contraste com o fundo, a
identidade nunca depende só da cor: há legenda nomeada, rótulos diretos com o valor
final e uma tabela completa com os mesmos dados.

Um único eixo Y para todas as séries, modo escuro com passos próprios (não é
inversão automática) e tooltip com crosshair no gráfico de linha.

---

## Próximos passos

- [ ] Buscar as séries direto da API do Banco Central, com cache local
- [ ] Carteira composta (ex.: 60% renda fixa + 40% ações) com rebalanceamento
- [ ] Questionário de perfil de investidor sugerindo uma alocação
- [ ] Simular aporte corrigido pela inflação ao longo do tempo
- [ ] Deploy (backend no Render/Fly, frontend na Vercel)

---

## Licença

MIT
