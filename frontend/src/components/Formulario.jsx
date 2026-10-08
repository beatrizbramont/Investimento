import { moeda } from '../formatar'

/** Painel de controles: quanto, por quanto tempo e em quê.
 *
 * O componente não guarda estado próprio — recebe `parametros` e avisa o App a
 * cada mudança através de `aoMudar`. Isso mantém uma única fonte da verdade.
 */
export default function Formulario({ parametros, aoMudar, produtos, desabilitado }) {
  function atualizar(campo, valor) {
    aoMudar({ ...parametros, [campo]: valor })
  }

  function alternarProduto(id) {
    const selecionados = parametros.produtos.includes(id)
      ? parametros.produtos.filter((p) => p !== id)
      : [...parametros.produtos, id]

    // O backend recusa uma simulação sem nenhum produto; evitamos chegar lá.
    if (selecionados.length === 0) return
    atualizar('produtos', selecionados)
  }

  return (
    <form className="painel" onSubmit={(e) => e.preventDefault()}>
      <fieldset disabled={desabilitado}>
        <legend className="painel__titulo">Seu plano</legend>

        <label className="campo">
          <span className="campo__rotulo">Quanto você tem hoje</span>
          <div className="campo__moeda">
            <span aria-hidden="true">R$</span>
            <input
              type="number"
              min="0"
              step="100"
              value={parametros.aporte_inicial}
              onChange={(e) => atualizar('aporte_inicial', Number(e.target.value))}
            />
          </div>
        </label>

        <label className="campo">
          <span className="campo__rotulo">Quanto consegue guardar por mês</span>
          <div className="campo__moeda">
            <span aria-hidden="true">R$</span>
            <input
              type="number"
              min="0"
              step="50"
              value={parametros.aporte_mensal}
              onChange={(e) => atualizar('aporte_mensal', Number(e.target.value))}
            />
          </div>
        </label>

        <label className="campo">
          <span className="campo__rotulo">
            Por quanto tempo
            <strong className="campo__valor">
              {parametros.anos} {parametros.anos === 1 ? 'ano' : 'anos'}
            </strong>
          </span>
          <input
            type="range"
            min="1"
            max="10"
            value={parametros.anos}
            onChange={(e) => atualizar('anos', Number(e.target.value))}
          />
        </label>

        <div className="campo">
          <span className="campo__rotulo">Como calcular</span>
          <div className="segmentado" role="radiogroup" aria-label="Modo de cálculo">
            {[
              { id: 'historico', nome: 'Histórico real' },
              { id: 'projecao', nome: 'Projeção' },
            ].map((opcao) => (
              <button
                key={opcao.id}
                type="button"
                role="radio"
                aria-checked={parametros.modo === opcao.id}
                className={parametros.modo === opcao.id ? 'ativo' : ''}
                onClick={() => atualizar('modo', opcao.id)}
              >
                {opcao.nome}
              </button>
            ))}
          </div>
          <p className="campo__ajuda">
            {parametros.modo === 'historico'
              ? 'Usa a rentabilidade que esses investimentos realmente tiveram no Brasil.'
              : 'Repete uma taxa estimada todos os meses, como fazem as calculadoras de banco.'}
          </p>
        </div>

        {parametros.modo === 'projecao' && (
          <label className="campo">
            <span className="campo__rotulo">
              CDI estimado
              <strong className="campo__valor">{parametros.cdiProjetado}% a.a.</strong>
            </span>
            <input
              type="range"
              min="2"
              max="20"
              step="0.5"
              value={parametros.cdiProjetado}
              onChange={(e) => atualizar('cdiProjetado', Number(e.target.value))}
            />
          </label>
        )}

        <div className="campo">
          <span className="campo__rotulo">Comparar</span>
          <ul className="lista-produtos">
            {produtos.map((produto) => {
              const marcado = parametros.produtos.includes(produto.id)
              return (
                <li key={produto.id}>
                  <label className="produto" title={produto.descricao}>
                    <input
                      type="checkbox"
                      checked={marcado}
                      onChange={() => alternarProduto(produto.id)}
                    />
                    <span
                      className="produto__cor"
                      style={{ '--cor': produto.cor, '--cor-escura': produto.cor_escura }}
                      aria-hidden="true"
                    />
                    <span className="produto__nome">{produto.nome}</span>
                    <span className="produto__risco" aria-label={`Risco ${produto.risco} de 5`}>
                      {'•'.repeat(produto.risco)}
                    </span>
                  </label>
                </li>
              )
            })}
          </ul>
        </div>

        <p className="painel__rodape">
          Total depositado no período:{' '}
          <strong>
            {moeda(parametros.aporte_inicial + parametros.aporte_mensal * parametros.anos * 12)}
          </strong>
        </p>
      </fieldset>
    </form>
  )
}
