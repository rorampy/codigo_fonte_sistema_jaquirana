// Sistema de Conciliação OFX - Busca sempre dados atualizados do servidor
class ConciliacaoOFX {
  constructor() {
    // Controles internos
    this.requisicaoAndamento = new Set();             // Evita requisições duplicadas
    
    this.inicializar();
  }

  // Inicialização do sistema
  inicializar() {
    this.configurarEventos();
    // Sempre buscar dados atualizados do servidor
    setTimeout(() => this.buscarSugestoesSemCache(), 100);
  }

  // Configura eventos do sistema
  configurarEventos() {
    // Quando usuário clica em abas de sugestão - sempre carrega do servidor
    document.addEventListener('shown.bs.tab', (evento) => {
      const linkAba = evento.target.getAttribute('href');
      if (linkAba && linkAba.includes('tabs-sugestao-')) {
        const idTransacao = this.extrairIdTransacao(linkAba);
        if (idTransacao) {
          this.carregarSugestoesSemCache(idTransacao);
        }
      }
    });

    // Quando uma conciliação é feita - recarrega sugestões
    document.addEventListener('conciliacao-realizada', (evento) => {
      
      // Recarrega todas as abas abertas
      this.recarregarTodasSugestoes();
    });
  }

  // Extrai ID da transação a partir do link da aba
  extrairIdTransacao(linkAba) {
    const match = linkAba.match(/tabs-sugestao-(\d+)/);
    return match ? match[1] : null;
  }

  // Busca sugestões sem usar cache - sempre do servidor
  async buscarSugestoesSemCache() {
    const todasTransacoes = this.coletarIdsTransacoes();
    
    if (todasTransacoes.length === 0) {
      return;
    }

    

    // Mostra loading em todas
    todasTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) {
        container.dataset.carregado = 'false'; // Reset status
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

  // Carrega sugestões para uma transação específica sem cache
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

  // Recarrega todas as sugestões abertas
  async recarregarTodasSugestoes() {
    const todasTransacoes = this.coletarIdsTransacoes();
    
    // Recarrega apenas as que já foram carregadas
    const transacoesCarregadas = todasTransacoes.filter(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      return container && container.dataset.carregado === 'true';
    });

    if (transacoesCarregadas.length > 0) {
      
      await this.buscarSugestoesSemCacheEspecificas(transacoesCarregadas);
    }
  }

  // Busca sugestões para transações específicas
  async buscarSugestoesSemCacheEspecificas(idsTransacoes) {
    if (idsTransacoes.length === 0) return;

    // Mostra loading
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

  // Processa resposta do servidor sem salvar em cache
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

  // Mostra mensagem vazio para todas as transações
  mostrarMensagemVazioParaTodas(idsTransacoes) {
    idsTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) {
        this.mostrarMensagemVazio(container);
        container.dataset.carregado = 'true';
      }
    });
  }

  // Mostra erro para todas as transações
  mostrarErroParaTodas(idsTransacoes) {
    idsTransacoes.forEach(id => {
      const container = document.getElementById(`tabs-sugestao-${id}`);
      if (container) {
        this.mostrarMensagemErro(container);
        container.dataset.carregado = 'true';
      }
    });
  }

  // Coleta todos os IDs de transações presentes na página
  coletarIdsTransacoes() {
    const ids = [];
    document.querySelectorAll('[href*="tabs-sugestao-"]').forEach(elemento => {
      const id = this.extrairIdTransacao(elemento.getAttribute('href'));
      if (id && !ids.includes(id)) ids.push(id);
    });
    return ids;
  }

  // Exibe tela de carregamento no container
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

  // Exibe mensagem quando não há sugestões disponíveis
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

  // Exibe mensagem de erro quando falha o carregamento
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

  // Exibe lista de sugestões no container
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

  // Cria card HTML para uma sugestão
  criarCardSugestao(sugestao, idTransacao) {
    // Coluna principal
    const coluna = document.createElement('div');
    coluna.className = 'col-12';

    // Card
    const card = document.createElement('div');
    card.className = 'card border-0 shadow-sm sugestao-card';

    // Corpo do card
    const corpoCard = document.createElement('div');
    corpoCard.className = 'card-body p-3';

    // Linha de informações
    const linhaInfo = document.createElement('div');
    linhaInfo.className = 'row align-items-center';

    // Colunas de informação
    linhaInfo.appendChild(this.criarColunaTipo(sugestao));
    linhaInfo.appendChild(this.criarColunaValor(sugestao));
    linhaInfo.appendChild(this.criarColunaData(sugestao));
    linhaInfo.appendChild(this.criarColunaBeneficiario(sugestao));
    linhaInfo.appendChild(this.criarColunaDescricao(sugestao));

    // Linha das Categorias
    const linhaCategorias = document.createElement('div');
    linhaCategorias.className = 'row mt-3';
    linhaCategorias.appendChild(this.criarLinhaCategoria(sugestao));

    // Linha do botão
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

    // Montar estrutura
    corpoCard.appendChild(linhaInfo);
    corpoCard.appendChild(linhaCategorias);
    corpoCard.appendChild(linhaBotao);
    card.appendChild(corpoCard);
    coluna.appendChild(card);

    return coluna;
  }

  // Cria coluna com tipo/origem da sugestão
  criarColunaTipo(sugestao) {
    const coluna = document.createElement('div');
    coluna.className = 'col-md-2 col-sm-12 text-center mb-2 mb-md-0';

    const badge = document.createElement('span');
    badge.className = 'badge badge-outline text-default';
    badge.textContent = sugestao.codigo_origem || 'N/A';

    coluna.appendChild(badge);
    return coluna;
  }

  // Cria coluna com valor da sugestão
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

  // Cria coluna com data de vencimento da sugestão
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

  // Cria coluna com beneficiário da sugestão
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

  // Cria coluna com descrição da sugestão
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

  // Cria linha com categorias da sugestão
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

    // Verifica se tem categorias
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

  // Trunca texto se exceder o limite especificado
  truncarTexto(texto, limite) {
    if (!texto) return 'Não informado';
    return texto.length > limite ? texto.substring(0, limite) + '...' : texto;
  }

}

// Inicializa quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
  new ConciliacaoOFX();
});
