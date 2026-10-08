/** Chamadas à API do backend.
 *
 * O caminho começa em `/api` porque o Vite faz proxy para o FastAPI
 * (veja `vite.config.js`). Em produção, basta servir os dois sob o mesmo domínio.
 */

async function requisitar(caminho, opcoes) {
  const resposta = await fetch(`/api${caminho}`, opcoes)

  if (!resposta.ok) {
    // O FastAPI devolve o motivo em `detail` — às vezes string, às vezes lista.
    let detalhe = `Erro ${resposta.status}`
    try {
      const corpo = await resposta.json()
      if (typeof corpo.detail === 'string') {
        detalhe = corpo.detail
      } else if (Array.isArray(corpo.detail) && corpo.detail.length > 0) {
        detalhe = corpo.detail[0].msg ?? detalhe
      }
    } catch {
      // resposta sem JSON: mantemos a mensagem genérica
    }
    throw new Error(detalhe)
  }

  return resposta.json()
}

export function listarProdutos() {
  return requisitar('/produtos')
}

export function listarGlossario() {
  return requisitar('/glossario')
}

export function simular(parametros) {
  return requisitar('/simular', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parametros),
  })
}
