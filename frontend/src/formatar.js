/** Funções de formatação em português do Brasil. */

const moedaCheia = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

const moedaExata = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function moeda(valor) {
  return moedaCheia.format(valor ?? 0)
}

export function moedaPrecisa(valor) {
  return moedaExata.format(valor ?? 0)
}

/** Rótulo do eixo Y: "120 mil". Sem "R$", que o eixo não precisa repetir em
 *  cada marca — isso mantém a coluna estreita e evita a quebra em duas linhas. */
export function numeroCurto(valor) {
  const absoluto = Math.abs(valor)
  if (absoluto >= 1_000_000) {
    return `${(valor / 1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi`
  }
  if (absoluto >= 1000) {
    return `${Math.round(valor / 1000)} mil`
  }
  return String(Math.round(valor))
}

/** Versão curta com símbolo, para uso fora do eixo. */
export function moedaCurta(valor) {
  const absoluto = Math.abs(valor)
  if (absoluto >= 1_000_000) {
    return `R$ ${(valor / 1_000_000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi`
  }
  if (absoluto >= 1000) {
    return `R$ ${Math.round(valor / 1000)} mil`
  }
  return `R$ ${Math.round(valor)}`
}

export function percentual(valor, casas = 1) {
  const numero = (valor ?? 0).toLocaleString('pt-BR', {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  })
  return `${valor > 0 ? '+' : ''}${numero}%`
}

const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

/** "2015-01" vira "jan/15"; rótulos de projeção ("Mês 12") passam direto. */
export function rotuloCurto(rotulo) {
  const partes = /^(\d{4})-(\d{2})$/.exec(rotulo)
  if (!partes) return rotulo
  const [, ano, mes] = partes
  return `${MESES[Number(mes) - 1]}/${ano.slice(2)}`
}

export function rotuloLongo(rotulo) {
  const partes = /^(\d{4})-(\d{2})$/.exec(rotulo)
  if (!partes) return rotulo
  const [, ano, mes] = partes
  return `${MESES[Number(mes) - 1]}/${ano}`
}
