import { moeda, percentual } from '../formatar'

/** A leitura rápida: o melhor resultado, quanto foi para o leão e o ganho real.
 *
 * O número que mais ensina aqui é o último — rentabilidade acima da inflação.
 * É comum um investimento "render 35%" e não ter aumentado nada o poder de compra.
 */
export default function Destaques({ dados }) {
  const { resultados, periodo, total_investido, investido_corrigido } = dados
  const melhor = resultados[0] // o backend já devolve ordenado pelo líquido
  const pior = resultados[resultados.length - 1]
  const diferenca = melhor.resumo.valor_liquido - pior.resumo.valor_liquido

  return (
    <section className="destaques" aria-label="Resumo da simulação">
      <article className="destaque destaque--principal">
        <p className="destaque__rotulo">Melhor resultado — {melhor.produto.nome}</p>
        <p className="destaque__numero">{moeda(melhor.resumo.valor_liquido)}</p>
        <p className="destaque__apoio">
          sobre {moeda(total_investido)} depositados ·{' '}
          <strong>{percentual(melhor.resumo.rentabilidade_pct)}</strong>
        </p>
      </article>

      <article className="destaque">
        <p className="destaque__rotulo">Ganho acima da inflação</p>
        <p
          className={`destaque__numero ${
            melhor.resumo.ganho_real >= 0 ? 'positivo' : 'negativo'
          }`}
        >
          {moeda(melhor.resumo.ganho_real)}
        </p>
        <p className="destaque__apoio">
          seus aportes valem {moeda(investido_corrigido)} em dinheiro de hoje ·{' '}
          <strong>{percentual(melhor.resumo.rentabilidade_real_pct)}</strong> real
        </p>
      </article>

      <article className="destaque">
        <p className="destaque__rotulo">Imposto de Renda</p>
        <p className="destaque__numero">{moeda(melhor.resumo.imposto)}</p>
        <p className="destaque__apoio">
          {melhor.resumo.imposto === 0
            ? 'este investimento é isento para pessoa física'
            : 'calculado aporte a aporte pela tabela regressiva'}
        </p>
      </article>

      <article className="destaque">
        <p className="destaque__rotulo">O custo de escolher mal</p>
        <p className="destaque__numero">{moeda(diferenca)}</p>
        <p className="destaque__apoio">
          diferença entre {melhor.produto.nome} e {pior.produto.nome} em{' '}
          {Math.round(periodo.meses / 12)} anos
        </p>
      </article>
    </section>
  )
}
