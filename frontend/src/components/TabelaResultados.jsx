import { moedaPrecisa, percentual } from '../formatar'

/** Os mesmos dados do gráfico em forma de tabela.
 *
 * Não é um extra: é o caminho de leitura para quem usa leitor de tela e para
 * quem não distingue bem as cores das linhas.
 */
export default function TabelaResultados({ resultados, escuro }) {
  return (
    <div className="tabela-rolagem">
      <table className="tabela">
        <caption className="sr-only">
          Resultado de cada investimento ao fim do período simulado
        </caption>
        <thead>
          <tr>
            <th scope="col">Investimento</th>
            <th scope="col">Risco</th>
            <th scope="col" className="num">Valor bruto</th>
            <th scope="col" className="num">Imposto</th>
            <th scope="col" className="num">Valor líquido</th>
            <th scope="col" className="num">Rentabilidade</th>
            <th scope="col" className="num">Acima da inflação</th>
          </tr>
        </thead>
        <tbody>
          {resultados.map(({ produto, resumo }) => (
            <tr key={produto.id}>
              <th scope="row">
                <span
                  className="tabela__cor"
                  style={{ background: escuro ? produto.cor_escura : produto.cor }}
                  aria-hidden="true"
                />
                {produto.nome}
              </th>
              <td>
                <span aria-label={`${produto.risco} de 5`}>{'•'.repeat(produto.risco)}</span>
              </td>
              <td className="num">{moedaPrecisa(resumo.valor_bruto)}</td>
              <td className="num">
                {resumo.imposto === 0 ? (
                  <span className="isento">isento</span>
                ) : (
                  `− ${moedaPrecisa(resumo.imposto)}`
                )}
              </td>
              <td className="num forte">{moedaPrecisa(resumo.valor_liquido)}</td>
              <td className="num">{percentual(resumo.rentabilidade_pct)}</td>
              <td className={`num ${resumo.rentabilidade_real_pct >= 0 ? 'positivo' : 'negativo'}`}>
                {percentual(resumo.rentabilidade_real_pct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
