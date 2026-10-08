import { useEffect, useState } from 'react'

/** Diz se o sistema está em modo escuro, reagindo a mudanças em tempo real.
 *
 * O gráfico precisa disso porque as cores das séries têm uma versão para cada
 * fundo — as do modo claro não teriam contraste suficiente sobre o fundo escuro.
 */
export function useTemaEscuro() {
  const [escuro, setEscuro] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches,
  )

  useEffect(() => {
    const consulta = window.matchMedia('(prefers-color-scheme: dark)')
    const aoMudar = (evento) => setEscuro(evento.matches)
    consulta.addEventListener('change', aoMudar)
    return () => consulta.removeEventListener('change', aoMudar)
  }, [])

  return escuro
}
