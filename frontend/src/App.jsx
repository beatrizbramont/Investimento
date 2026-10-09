import { useEffect, useState } from 'react'

import { listarGlossario, listarProdutos, simular } from './api'
import { duracao, rotuloCurto } from './formatar'
import { useTemaEscuro } from './useTemaEscuro'
import Destaques from './components/Destaques'
import Formulario from './components/Formulario'
import GraficoComparativo from './components/GraficoComparativo'
import Glossario from './components/Glossario'
import TabelaResultados from './components/TabelaResultados'

const PARAMETROS_INICIAIS = {
  aporte_inicial: 1000,
  aporte_mensal: 500,
  meses: 120,
  modo: 'historico',
  cdiProjetado: 10.5,
  produtos: [],
}

/** "2016–2025", ou só "2025" quando o período cabe num ano. */
function faixaDeAnos({ inicio, fim }) {
  const primeiro = inicio.slice(0, 4)
  const ultimo = fim.slice(0, 4)
  return primeiro === ultimo ? primeiro : `${primeiro}–${ultimo}`
}

export default function App() {
  const escuro = useTemaEscuro()

  const [produtos, setProdutos] = useState([])
  const [termos, setTermos] = useState([])
  const [parametros, setParametros] = useState(PARAMETROS_INICIAIS)
  const [dados, setDados] = useState(null)
  const [visao, setVisao] = useState('liquido')
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(true)

  // Catálogo e glossário são fixos: buscamos uma vez só.
  useEffect(() => {
    Promise.all([listarProdutos(), listarGlossario()])
      .then(([listaProdutos, listaTermos]) => {
        setProdutos(listaProdutos)
        setTermos(listaTermos)
        setParametros((atuais) => ({
          ...atuais,
          produtos: listaProdutos.map((p) => p.id),
        }))
      })
      .catch((e) =>
        setErro(
          `Não consegui falar com a API (${e.message}). ` +
            'Confira se o backend está rodando em http://127.0.0.1:8000.',
        ),
      )
  }, [])

  // Simula de novo a cada ajuste, com um respiro para não disparar uma
  // requisição por tecla digitada.
  useEffect(() => {
    if (parametros.produtos.length === 0) return

    const cancelar = setTimeout(() => {
      setCarregando(true)
      simular({
        aporte_inicial: parametros.aporte_inicial,
        aporte_mensal: parametros.aporte_mensal,
        meses: parametros.meses,
        modo: parametros.modo,
        produtos: parametros.produtos,
        premissas: parametros.modo === 'projecao' ? { cdi: parametros.cdiProjetado } : {},
      })
        .then((resposta) => {
          setDados(resposta)
          setErro(null)
        })
        .catch((e) => setErro(e.message))
        .finally(() => setCarregando(false))
    }, 300)

    return () => clearTimeout(cancelar)
  }, [parametros])

  return (
    <div className="app">
      <header className="cabecalho">
        <p className="cabecalho__etiqueta">
          <span>Investe Simples</span>
          <span>
            {dados ? faixaDeAnos(dados.periodo) : '—'}
          </span>
        </p>
        <div className="cabecalho__corpo">
          <h1>Onde seu dinheiro realmente cresce</h1>
          <p className="cabecalho__linha-fina">
            Pare de decorar siglas. Veja, com dados do mercado brasileiro, o que
            acontece com o seu dinheiro em cada tipo de investimento.
          </p>
        </div>
      </header>

      <main className="conteudo">
        <aside>
          <Formulario
            parametros={parametros}
            aoMudar={setParametros}
            produtos={produtos}
            desabilitado={produtos.length === 0}
          />
        </aside>

        <div className="resultados">
          {erro && (
            <p className="aviso aviso--erro" role="alert">
              {erro}
            </p>
          )}

          {!dados && !erro && <p className="aviso">Calculando sua simulação…</p>}

          {dados && (
            <>
              <Destaques dados={dados} />

              <section className="cartao" aria-labelledby="grafico-titulo">
                <div className="cartao__cabecalho">
                  <div>
                    <h2 id="grafico-titulo">Evolução do seu patrimônio</h2>
                    <p className="cartao__subtitulo">
                      {dados.periodo.modo === 'historico'
                        ? `Rentabilidade real de ${rotuloCurto(dados.periodo.inicio)} a ${rotuloCurto(dados.periodo.fim)}`
                        : `Projeção para ${duracao(dados.periodo.meses)}`}
                      {' · inflação acumulada de '}
                      {dados.periodo.inflacao_acumulada_pct.toLocaleString('pt-BR')}%
                    </p>
                  </div>

                  <div className="segmentado" role="radiogroup" aria-label="Valor exibido">
                    {[
                      { id: 'liquido', nome: 'Líquido' },
                      { id: 'bruto', nome: 'Bruto' },
                    ].map((opcao) => (
                      <button
                        key={opcao.id}
                        type="button"
                        role="radio"
                        aria-checked={visao === opcao.id}
                        className={visao === opcao.id ? 'ativo' : ''}
                        onClick={() => setVisao(opcao.id)}
                      >
                        {opcao.nome}
                      </button>
                    ))}
                  </div>
                </div>

                <p className="cartao__dica">
                  {visao === 'liquido'
                    ? 'O que sobraria na sua conta. Troque para "Bruto" e veja a LCI isenta cair atrás de CDBs que rendem menos no fim das contas.'
                    : 'O número antes do imposto — é este que os bancos anunciam.'}
                </p>

                <GraficoComparativo
                  resultados={dados.resultados}
                  visao={visao}
                  escuro={escuro}
                />
              </section>

              <section className="cartao" aria-labelledby="tabela-titulo">
                <h2 id="tabela-titulo">Resultado em números</h2>
                <TabelaResultados resultados={dados.resultados} escuro={escuro} />
                <ul className="observacoes">
                  {dados.observacoes.map((nota) => (
                    <li key={nota}>{nota}</li>
                  ))}
                </ul>
              </section>

              <section className="cartao">
                <h2>O que cada um desses é</h2>
                <ul className="fichas">
                  {dados.resultados.map(({ produto }) => (
                    <li key={produto.id} className="ficha">
                      <h3>
                        <span
                          className="ficha__cor"
                          style={{ background: escuro ? produto.cor_escura : produto.cor }}
                          aria-hidden="true"
                        />
                        {produto.nome}
                      </h3>
                      <p>{produto.descricao}</p>
                      <dl>
                        <div>
                          <dt>Liquidez</dt>
                          <dd>{produto.liquidez}</dd>
                        </div>
                        <div>
                          <dt>Imposto de Renda</dt>
                          <dd>
                            {produto.isento_ir
                              ? 'Isento'
                              : produto.aliquota_ir
                                ? `${(produto.aliquota_ir * 100).toLocaleString('pt-BR')}% sobre o ganho`
                                : 'Tabela regressiva (22,5% a 15%)'}
                          </dd>
                        </div>
                      </dl>
                    </li>
                  ))}
                </ul>
              </section>

              <Glossario termos={termos} />
            </>
          )}

          {carregando && dados && <p className="aviso aviso--sutil">Atualizando…</p>}
        </div>
      </main>

      <footer className="rodape">
        <p>
          <strong>Isto é material educativo, não recomendação de investimento.</strong> As
          séries históricas são aproximadas e rentabilidade passada não se repete no
          futuro. Antes de investir, procure um profissional certificado.
        </p>
      </footer>
    </div>
  )
}
