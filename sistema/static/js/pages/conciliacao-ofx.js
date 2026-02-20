
class ConciliacaoOFX {
  constructor() {
    
    this.requisicaoAndamento = new Set();             
    
    this.inicializar();
  }

  inicializar() {
    this.configurarEventos();
    
    setTimeout(() => this.buscarSugestoesSemCache(), 100);
  }

  configurarEventos() {
    
    document.addEventListener('shown.bs.tab', (evento) => {
      const linkAba = evento.target.getAttribute('href');
      if (linkAba && linkAba.includes('tabs-sugestao-')) {
        const idTransacao = this.extrairIdTransacao(linkAba);
        if (idTransacao) {
          this.carregarSugestoesSemCache(idTransacao);
        }
      }
    });

    document.addEventListener('conciliacao-realizada', (evento) => {
      
      this.recarregarTodasSugestoes();
    });
  }

  extrairIdTransacao(linkAba) {
    const match = linkAba.match(/tabs-sugestao-(\d+)/);
    return match ? match[1] : null;
  }

  async buscarSugestoesSemCache() {
    const todasTransacoes = this.coletarIdsTransacoes();
    
    if (todasTransacoes.length === 0) {
      return;
    }

    todasTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) {
        container.dataset.carregado = 'false'; 
        this.mostrarCarregamento(container);
      }
    });

    try {
      const resposta = await fetch('/api/sugestoes-ofx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transacoes_ids: todasTransacoes })
      });

      const dados = await resposta.json();

      if (dados.success && dados.sugestoes_por_transacao) {
        this.processarRespostaSemCache(dados.sugestoes_por_transacao);
      } else {
        console.warn('[ConciliacaoOFX] Nenhuma sugestão retornada do servidor');
        this.mostrarMensagemVazioParaTodas(todasTransacoes);
      }

    } catch (erro) {
      console.error('[ConciliacaoOFX] Erro ao buscar sugestões:', erro);
      this.mostrarErroParaTodas(todasTransacoes);
    }
  }

  async carregarSugestoesSemCache(idTransacao) {
    const container = document.getElementById(`tabs-sugestao-${idTransacao}`);
    if (!container) return;

    container.dataset.carregado = 'false';
    this.mostrarCarregamento(container);

    try {
      const resposta = await fetch('/api/sugestoes-ofx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transacao_id: idTransacao })
      });

      const dados = await resposta.json();

      if (dados.success && dados.sugestoes?.length > 0) {
        this.exibirSugestoes(container, dados.sugestoes, idTransacao);
      } else {
        this.mostrarMensagemVazio(container);
      }
      
      container.dataset.carregado = 'true';

    } catch (erro) {
      console.error(`[ConciliacaoOFX] Erro ao carregar sugestões para transação ${idTransacao}:`, erro);
      this.mostrarMensagemErro(container);
    }
  }

  async recarregarTodasSugestoes() {
    const todasTransacoes = this.coletarIdsTransacoes();
    
    const transacoesCarregadas = todasTransacoes.filter(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      return container && container.dataset.carregado === 'true';
    });

    if (transacoesCarregadas.length > 0) {
      
      await this.buscarSugestoesSemCacheEspecificas(transacoesCarregadas);
    }
  }

  async buscarSugestoesSemCacheEspecificas(idsTransacoes) {
    if (idsTransacoes.length === 0) return;

    idsTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) this.mostrarCarregamento(container);
    });

    try {
      const resposta = await fetch('/api/sugestoes-ofx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transacoes_ids: idsTransacoes })
      });

      const dados = await resposta.json();

      if (dados.success && dados.sugestoes_por_transacao) {
        this.processarRespostaSemCache(dados.sugestoes_por_transacao);
      }

    } catch (erro) {
      console.error('[ConciliacaoOFX] Erro ao recarregar sugestões:', erro);
    }
  }

  processarRespostaSemCache(sugestoesPorTransacao) {
    Object.entries(sugestoesPorTransacao).forEach(([transacaoId, sugestoes]) => {
      const container = document.getElementById(`tabs-sugestao-${transacaoId}`);
      if (!container) return;

      if (sugestoes && sugestoes.length > 0) {
        this.exibirSugestoes(container, sugestoes, transacaoId);
        
      } else {
        this.mostrarMensagemVazio(container);
        
      }
      
      container.dataset.carregado = 'true';
    });
  }

  mostrarMensagemVazioParaTodas(idsTransacoes) {
    idsTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) {
        this.mostrarMensagemVazio(container);
        container.dataset.carregado = 'true';
      }
    });
  }

  mostrarErroParaTodas(idsTransacoes) {
    idsTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) {
        this.mostrarMensagemErro(container);
        container.dataset.carregado = 'true';
      }
    });
  }

  coletarIdsTransacoes() {
    const ids = [];
    document.querySelectorAll('[href*="tabs-sugestao-"]').forEach(elemento => {
      const id = this.extrairIdTransacao(elemento.getAttribute('href'));
      if (id && !ids.includes(id)) ids.push(id);
    });
    return ids;
  }

  mostrarCarregamento(container) {
    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'w-100 text-center py-4';

    const spinner = document.createElement('div');
    spinner.className = 'spinner-border text-primary';

    const titulo = document.createElement('h5');
    titulo.className = 'text-muted mt-2';
    titulo.textContent = 'Carregando sugestões...';

    wrapper.appendChild(spinner);
    wrapper.appendChild(titulo);
    container.appendChild(wrapper);
  }

  mostrarMensagemVazio(container) {
    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'w-100 text-center py-4';

    const icone = document.createElement('div');
    icone.innerHTML = '💡';
    icone.style.fontSize = '3rem';
    icone.className = 'mb-3';

    const titulo = document.createElement('h5');
    titulo.className = 'text-muted mb-2';
    titulo.textContent = 'Nenhuma sugestão encontrada';

    const descricao = document.createElement('p');
    descricao.className = 'text-muted small';
    descricao.textContent = 'Não foram encontrados agendamentos compatíveis com esta transação.';

    wrapper.appendChild(icone);
    wrapper.appendChild(titulo);
    wrapper.appendChild(descricao);
    container.appendChild(wrapper);
  }

  mostrarMensagemErro(container) {
    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'w-100 text-center py-4';

    const icone = document.createElement('div');
    icone.innerHTML = '⚠️';
    icone.style.fontSize = '3rem';
    icone.className = 'mb-3';

    const titulo = document.createElement('h5');
    titulo.className = 'text-danger mb-2';
    titulo.textContent = 'Erro ao carregar';

    const descricao = document.createElement('p');
    descricao.className = 'text-muted small';
    descricao.textContent = 'Ocorreu um erro ao buscar as sugestões. Tente novamente.';

    wrapper.appendChild(icone);
    wrapper.appendChild(titulo);
    wrapper.appendChild(descricao);
    container.appendChild(wrapper);
  }

  exibirSugestoes(container, listaSugestoes, idTransacao) {
    container.innerHTML = '';

    const wrapperPrincipal = document.createElement('div');
    wrapperPrincipal.className = 'w-100';

    const containerLinhas = document.createElement('div');
    containerLinhas.className = 'row g-3';

    listaSugestoes.forEach(sugestao => {
      const elementoSugestao = this.criarCardSugestao(sugestao, idTransacao);
      containerLinhas.appendChild(elementoSugestao);
    });

    wrapperPrincipal.appendChild(containerLinhas);
    container.appendChild(wrapperPrincipal);
  }

  criarCardSugestao(sugestao, idTransacao) {
    
    const coluna = document.createElement('div');
    coluna.className = 'col-12';

    const card = document.createElement('div');
    card.className = 'card border-0 shadow-sm sugestao-card';

    const corpoCard = document.createElement('div');
    corpoCard.className = 'card-body p-3';

    const linhaInfo = document.createElement('div');
    linhaInfo.className = 'row align-items-center';

    linhaInfo.appendChild(this.criarColunaTipo(sugestao));
    linhaInfo.appendChild(this.criarColunaValor(sugestao));
    linhaInfo.appendChild(this.criarColunaData(sugestao));
    linhaInfo.appendChild(this.criarColunaBeneficiario(sugestao));
    linhaInfo.appendChild(this.criarColunaDescricao(sugestao));

    const linhaCategorias = document.createElement('div');
    linhaCategorias.className = 'row mt-3';
    linhaCategorias.appendChild(this.criarLinhaCategoria(sugestao));

    const linhaBotao = document.createElement('div');
    linhaBotao.className = 'row mt-3';

    const colunaBotao = document.createElement('div');
    colunaBotao.className = 'col-12 text-end';

    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'btn btn-success btn-sm px-4 btn-conciliar-sugestao';
    botao.setAttribute('data-agendamento-id', sugestao.id);
    botao.setAttribute('data-transacao-id', idTransacao);
    botao.textContent = 'Conciliar';

    colunaBotao.appendChild(botao);
    linhaBotao.appendChild(colunaBotao);

    corpoCard.appendChild(linhaInfo);
    corpoCard.appendChild(linhaCategorias);
    corpoCard.appendChild(linhaBotao);
    card.appendChild(corpoCard);
    coluna.appendChild(card);

    return coluna;
  }

  criarColunaTipo(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-md-2 col-sm-12 text-center mb-2 mb-md-0';

    const badge = document.createElement('span');
    badge.className = 'badge badge-outline text-default';
    badge.textContent = sugestao.codigo_origem || 'N/A';

    coluna.appendChild(badge);
    return coluna;
  }

  criarColunaValor(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-md-2 col-sm-6 text-center mb-2 mb-md-0';

    const wrapper = document.createElement('div');
    wrapper.className = 'valor-sugestao';

    const label = document.createElement('small');
    label.className = 'text-muted d-block';
    label.textContent = 'Valor';
    const valor = document.createElement('strong');
    valor.className = 'fs-5 text-dark';
    valor.textContent = sugestao.valor_formatado || 'R$ 0,00';

    wrapper.appendChild(label);
    wrapper.appendChild(valor);
    coluna.appendChild(wrapper);

    return coluna;
  }

  criarColunaData(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-md-2 col-sm-6 text-center mb-2 mb-md-0';

    const wrapper = document.createElement('div');
    wrapper.className = 'data-sugestao';

    const label = document.createElement('small');
    label.className = 'text-muted d-block';
    label.textContent = 'Vencimento';

    const data = document.createElement('strong');
    data.className = 'fs-5 text-dark';
    data.textContent = sugestao.data_vencimento || 'N/A';

    wrapper.appendChild(label);
    wrapper.appendChild(data);
    coluna.appendChild(wrapper);

    return coluna;
  }

  criarColunaBeneficiario(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-md-3 col-sm-12 mb-2 mb-md-0';

    const wrapper = document.createElement('div');
    wrapper.className = 'beneficiario-sugestao';

    const label = document.createElement('small');
    label.className = 'text-muted d-block';
    label.textContent = 'Beneficiário';

    const nome = document.createElement('strong');
    nome.className = 'fs-5 text-dark';
    nome.textContent = this.truncarTexto(sugestao.pessoa_nome, 25);
    nome.title = sugestao.pessoa_nome || 'Não informado';

    wrapper.appendChild(label);
    wrapper.appendChild(nome);
    coluna.appendChild(wrapper);

    return coluna;
  }

  criarColunaDescricao(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-md-3 col-sm-12 mb-2 mb-md-0';

    const wrapper = document.createElement('div');
    wrapper.className = 'descricao-sugestao';

    const label = document.createElement('small');
    label.className = 'text-muted d-block';
    label.textContent = 'Descrição';

    const descricao = document.createElement('strong');
    descricao.className = 'fs-5 text-dark';
    descricao.textContent = sugestao.descricao || 'Sem descrição';

    wrapper.appendChild(label);
    wrapper.appendChild(descricao);
    coluna.appendChild(wrapper);

    return coluna;
  }

  criarLinhaCategoria(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-12';

    const wrapper = document.createElement('div');
    wrapper.className = 'categorias-sugestao';

    const label = document.createElement('small');
    label.className = 'text-muted d-block mb-2';
    label.textContent = 'Categorias';

    const containerBadges = document.createElement('div');
    containerBadges.className = 'd-flex flex-wrap gap-1';

    if (sugestao.categorias_json && sugestao.categorias_json.length > 0) {
      sugestao.categorias_json.forEach(itemCategoria => {
        const categoriaNome = itemCategoria.categoria || 'Categoria não identificada';
        const categoriaTruncada = categoriaNome.length > 35 ?
          categoriaNome.substring(0, 35) + '...' : categoriaNome;

        const badge = document.createElement('span');
        badge.className = 'badge bg-light text-dark border';
        badge.title = categoriaNome;
        badge.textContent = categoriaTruncada;

        containerBadges.appendChild(badge);
      });
    } else {
      const badgeSemCategoria = document.createElement('span');
      badgeSemCategoria.className = 'badge bg-secondary-subtle text-secondary';
      badgeSemCategoria.textContent = 'Sem categoria definida';
      containerBadges.appendChild(badgeSemCategoria);
    }

    wrapper.appendChild(label);
    wrapper.appendChild(containerBadges);
    coluna.appendChild(wrapper);

    return coluna;
  }

  truncarTexto(texto, limite) {
    if (!texto) return 'Não informado';
    return texto.length > limite ? texto.substring(0, limite) + '...' : texto;
  }

}

document.addEventListener('DOMContentLoaded', () => {
  new ConciliacaoOFX();
});
