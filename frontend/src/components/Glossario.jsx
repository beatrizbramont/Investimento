import { useState } from 'react'

/** Glossário em acordeão: o jargão explicado sem jargão. */
export default function Glossario({ termos }) {
  const [aberto, setAberto] = useState(null)

  return (
    <section className="glossario" aria-labelledby="glossario-titulo">
      <h2 id="glossario-titulo">Para destravar o vocabulário</h2>
      <p className="glossario__intro">
        Boa parte da dificuldade com investimentos é de linguagem, não de matemática.
      </p>
      <ul>
        {termos.map((item) => {
          const expandido = aberto === item.termo
          return (
            <li key={item.termo}>
              <button
                type="button"
                aria-expanded={expandido}
                onClick={() => setAberto(expandido ? null : item.termo)}
              >
                <span>{item.termo}</span>
                <span className="glossario__sinal" aria-hidden="true">
                  {expandido ? '−' : '+'}
                </span>
              </button>
              {expandido && <p className="glossario__definicao">{item.definicao}</p>}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
