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

// Intervalos "redondos" entre marcas do eixo X, do mais fino ao mais grosso.
const PASSOS_EM_MESES = [1, 2, 3, 6, 12, 24]
const MAXIMO_DE_MARCAS = 10

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

  // O eixo X precisa funcionar tanto para 3 meses quanto para 120. Marcar "só os
  // janeiros" deixava um período de um ano com um único rótulo na tela, então
  // escolhemos um passo proporcional ao tamanho da série — sempre um intervalo
  // redondo, para os rótulos caírem em meses que o olho reconhece.
  const marcas = useMemo(() => {
    const passo = PASSOS_EM_MESES.find((p) => Math.ceil(dados.length / p) <= MAXIMO_DE_MARCAS)
      ?? PASSOS_EM_MESES[PASSOS_EM_MESES.length - 1]

    const indices = []
    for (let i = 0; i < dados.length; i += passo) indices.push(i)

    // O último mês é o que o usuário mais olha; garantimos o rótulo dele, desde
    // que não fique colado no anterior.
    const ultimo = dados.length - 1
    if (ultimo - indices[indices.length - 1] >= passo / 2) indices.push(ultimo)

    return indices.map((i) => dados[i].rotulo)
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
