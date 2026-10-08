import { useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { moeda, numeroCurto, rotuloCurto, rotuloLongo } from '../formatar'

/** Evolução do patrimônio mês a mês, uma linha por produto.
 *
 * Um único eixo Y (reais) para todas as séries — comparar curvas em escalas
 * diferentes no mesmo gráfico distorce a leitura.
 */
export default function GraficoComparativo({ resultados, visao, escuro }) {
  const corDe = (produto) => (escuro ? produto.cor_escura : produto.cor)

  // Recharts espera uma linha por ponto do eixo X, com uma chave por série.
  const dados = useMemo(() => {
    if (resultados.length === 0) return []
    return resultados[0].serie.map((ponto, indice) => {
      const linha = { rotulo: ponto.rotulo, investido: ponto.investido }
      for (const resultado of resultados) {
        linha[resultado.produto.id] = resultado.serie[indice][visao]
      }
      return linha
    })
  }, [resultados, visao])

  // Marcamos só os janeiros no eixo X; 120 rótulos não caberiam.
  const marcas = useMemo(() => {
    const janeiros = dados.filter((d) => d.rotulo.endsWith('-01')).map((d) => d.rotulo)
    if (janeiros.length > 0) return janeiros
    // Modo projeção: um rótulo a cada 12 meses.
    return dados.filter((_, i) => i % 12 === 11).map((d) => d.rotulo)
  }, [dados])

  if (dados.length === 0) return null

  return (
    <div className="grafico">
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={dados} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="var(--grade)" vertical={false} />
          <XAxis
            dataKey="rotulo"
            ticks={marcas}
            tickFormatter={rotuloCurto}
            stroke="var(--eixo)"
            tick={{ fill: 'var(--texto-fraco)', fontSize: 12 }}
            tickLine={false}
            minTickGap={12}
          />
          <YAxis
            tickFormatter={numeroCurto}
            stroke="var(--eixo)"
            tick={{ fill: 'var(--texto-fraco)', fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            width={56}
          />
          <Tooltip
            content={<DicaDetalhada resultados={resultados} escuro={escuro} />}
            cursor={{ stroke: 'var(--eixo)', strokeWidth: 1 }}
          />

          {/* Referência neutra: o dinheiro que saiu do seu bolso, sem rendimento. */}
          <Line
            type="monotone"
            dataKey="investido"
            stroke="var(--texto-fraco)"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
            isAnimationActive={false}
          />

          {resultados.map((resultado) => (
            <Line
              key={resultado.produto.id}
              type="monotone"
              dataKey={resultado.produto.id}
              stroke={corDe(resultado.produto)}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: 'var(--superficie)' }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Legenda sempre presente e já ordenada do melhor para o pior: ela também
          serve de rótulo direto, já que algumas cores têm contraste baixo. */}
      <ul className="legenda">
        <li className="legenda__item legenda__item--referencia">
          <span className="legenda__traco" aria-hidden="true" />
          <span className="legenda__nome">Total depositado</span>
        </li>
        {resultados.map((resultado) => (
          <li key={resultado.produto.id} className="legenda__item">
            <span
              className="legenda__cor"
              style={{ background: corDe(resultado.produto) }}
              aria-hidden="true"
            />
            <span className="legenda__nome">{resultado.produto.nome}</span>
            <span className="legenda__valor">{moeda(resultado.resumo[`valor_${visao}`])}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Tooltip com todas as séries daquele mês, da maior para a menor. */
function DicaDetalhada({ active, payload, label, resultados, escuro }) {
  if (!active || !payload || payload.length === 0) return null

  const porId = new Map(resultados.map((r) => [r.produto.id, r.produto]))
  const linhas = payload
    .filter((item) => porId.has(item.dataKey))
    .sort((a, b) => b.value - a.value)
  const investido = payload.find((item) => item.dataKey === 'investido')

  return (
    <div className="dica">
      <p className="dica__titulo">{rotuloLongo(label)}</p>
      <table>
        <tbody>
          {linhas.map((item) => {
            const produto = porId.get(item.dataKey)
            return (
              <tr key={item.dataKey}>
                <td>
                  <span
                    className="dica__cor"
                    style={{ background: escuro ? produto.cor_escura : produto.cor }}
                    aria-hidden="true"
                  />
                  {produto.nome}
                </td>
                <td className="dica__valor">{moeda(item.value)}</td>
              </tr>
            )
          })}
          {investido && (
            <tr className="dica__referencia">
              <td>Total depositado</td>
              <td className="dica__valor">{moeda(investido.value)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
