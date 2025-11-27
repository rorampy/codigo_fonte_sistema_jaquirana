/**
 * Nova Transação OFX
 */

class NovaTransacaoOFX {
  constructor(transacaoId, dadosIniciais) {
    this.transacaoId = transacaoId;
    this.dadosIniciais = dadosIniciais;
    
    // Estado do componente 
    this.estado = {
      totalPagar: dadosIniciais.totalPagar || 0,
      mostrarValoresDetalhados: dadosIniciais.mostrarValoresDetalhados || false,
      tipoDistribuicao: 'percentual',
      mapaCategorias: dadosIniciais.mapaCategorias || {},
      lista: [
        {
          nome: '',
          detalhamento: '',
          referencia: '',
          valor: 0 // Valor armazenado como inteiro (centavos)
        }
      ],
      centrosCusto: [
        {
          centro: '',
          percentual: '',
          valor: 0
        }
      ],

      // === PARCELAMENTO ===
      mostrarParcelamento: dadosIniciais.mostrarParcelamento || false,
      qtdParcelas: dadosIniciais.qtdParcelas || 0,
      diasEntre: dadosIniciais.diasEntre || 30,
      parcelas: [],
      totalParcelas: 0
    };

    this.init();
  }

  // === FUNÇÕES DE FORMATAÇÃO ===
  formatarMoeda(centavos) {
    const reais = centavos / 100;
    return 'R$ ' + reais.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  formatarParaExibicao(centavos) {
    const reais = centavos / 100;
    return 'R$ ' + reais.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  // === RENDERIZAÇÃO DOM ===
  renderizarCategorias() {
    const container = document.getElementById(`listaCategorias-${this.transacaoId}`);
    container.innerHTML = '';
    
    this.estado.lista.forEach((categoria, index) => {
      const div = document.createElement('div');
      div.className = 'row mb-3 align-items-center';
      div.innerHTML = this.getHtmlCategoria(categoria, index);
      
      container.appendChild(div);
      
      // Definir valor do select
      const select = div.querySelector('select');
      select.value = categoria.nome;
    });
    
    // Adicionar eventos
    this.adicionarEventosCategorias();
    // Atualizar display do total
    document.getElementById(`totalDisplay-${this.transacaoId}`).textContent = this.formatarMoeda(this.estado.totalPagar);
  }

  getHtmlCategoria(categoria, index) {
    return `
      <div class="col-lg-4 col-md-4 col-sm-6 col-12">
        <select class="form-select categoria-select" data-index="${index}">
          <option value="">Selecione uma categoria...</option>
          ${this.dadosIniciais.opcoesCategoria || ''}
        </select>
      </div>
      <div class="col-lg-4 col-md-4 col-sm-6 col-12">
        <input type="text" class="form-control detalhamento-input" data-index="${index}" 
               value="${categoria.detalhamento}" placeholder="Detalhamento (opcional)">
      </div>
      <div class="col-lg-3 col-md-3 col-sm-10 col-9">
        <input type="text" class="form-control text-end campo-moeda-brl valor-input"
               data-index="${index}" value="${this.formatarParaExibicao(categoria.valor)}" placeholder="R$ 0,00">
      </div>
      <div class="col-lg-1 col-md-1 col-sm-2 col-3 text-center">
        <button type="button" class="btn btn-link text-danger p-1 btn-remover-categoria" data-index="${index}"
                ${this.estado.lista.length <= 1 ? 'style="display:none"' : ''}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="icon icon-tabler icons-tabler-outline icon-tabler-trash">
            <path stroke="none" d="M0 0h24v24H0z" fill="none" />
            <path d="M4 7l16 0" />
            <path d="M10 11l0 6" />
            <path d="M14 11l0 6" />
            <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />
            <path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" />
          </svg>
        </button>
      </div>
    `;
  }

  adicionarEventosCategorias() {
    // Eventos para selects de categoria
    document.querySelectorAll(`#listaCategorias-${this.transacaoId} .categoria-select`).forEach(select => {
      select.addEventListener('change', () => {
        const index = parseInt(select.dataset.index);
        this.estado.lista[index].nome = select.value;
        this.validarTotalCompleto();
      });
    });

    // Eventos para inputs de detalhamento
    document.querySelectorAll(`#listaCategorias-${this.transacaoId} .detalhamento-input`).forEach(input => {
      input.addEventListener('input', () => {
        const index = parseInt(input.dataset.index);
        this.estado.lista[index].detalhamento = input.value;
      });
    });

    // Eventos para inputs de valor
    document.querySelectorAll(`#listaCategorias-${this.transacaoId} .valor-input`).forEach(input => {
      input.addEventListener('input', () => {
        const index = parseInt(input.dataset.index);
        this.aplicarMascara(input, index);
      });
    });

    // Eventos para botões de remover
    document.querySelectorAll(`#listaCategorias-${this.transacaoId} .btn-remover-categoria`).forEach(btn => {
      btn.addEventListener('click', () => {
        const index = parseInt(btn.dataset.index);
        this.removerCategoria(index);
      });
    });
  }

  // === FUNÇÕES DE CATEGORIA ===
  adicionarCategoria() {
    // Calcular valor atual das categorias
    let valorAtual = 0;
    this.estado.lista.forEach(categoria => {
      valorAtual += categoria.valor;
    });
    
    // Se não há valor atribuído ainda, pré-preencher a nova categoria com valor total
    const valorNovaCategoria = valorAtual === 0 ? this.estado.totalPagar : 0;
    
    this.estado.lista.push({
      nome: '',
      detalhamento: '',
      referencia: '',
      valor: valorNovaCategoria
    });
    this.renderizarCategorias();
    
    // Limpar último select adicionado
    setTimeout(() => {
      const selects = document.querySelectorAll('.categoria-select');
      const lastSelect = selects[selects.length - 1];
      if (lastSelect) {
        lastSelect.selectedIndex = 0;
      }
    }, 50);
  }

  removerCategoria(index) {
    if (this.estado.lista.length > 1) {
      this.estado.lista.splice(index, 1);
      this.renderizarCategorias();
      this.validarTotal();
    }
  }

  aplicarMascara(input, index) {
    let valor = input.value.replace(/\D/g, '');
    const valorCentavos = parseInt(valor) || 0;
    this.estado.lista[index].valor = valorCentavos;
    input.value = this.formatarParaExibicao(valorCentavos);
    this.validarTotalCompleto();
  }

  validarTotal() {
    this.validarTotalCompleto();
  }

  validarTotalCompleto() {
    // Primeiro validar categorias duplicadas
    if (this.validarCategoriasDuplicadas()) {
      return false;
    }
    
    let totalCategorias = 0;
    let categoriasPreenchidas = 0;
    this.estado.lista.forEach((categoria, index) => {
      if (categoria.nome && categoria.nome.trim() !== '') {
        categoriasPreenchidas++;
      }
      
      if (categoria.valor && categoria.valor > 0) {
        totalCategorias += categoria.valor;
      }
    });
    
    const btnSalvar = document.getElementById(`btnSalvarAgendamento-${this.transacaoId}`);
    let categoriasValidas = (totalCategorias === this.estado.totalPagar) && categoriasPreenchidas > 0;
    let centrosValidos = true;
    
    if (this.estado.mostrarValoresDetalhados) {
      centrosValidos = this.validarCentrosCusto();
    }
    
    const formularioValido = categoriasValidas && centrosValidos;
    
    if (formularioValido) {
      btnSalvar.disabled = false;
      btnSalvar.classList.remove('btn-secondary');
      btnSalvar.classList.add('btn-primary');
      
      // Fechar modal de validação se estiver aberto
      const modalElement = document.getElementById('modalValidacao');
      if (modalElement && modalElement.classList.contains('show')) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.hide();
      }
    } else {
      btnSalvar.disabled = true;
      btnSalvar.classList.remove('btn-primary');
      btnSalvar.classList.add('btn-secondary');
    }
    
    return formularioValido;
  }

  validarCategoriasDuplicadas() {
    const categoriasUsadas = [];
    let temDuplicada = false;
    let categoriaDuplicada = '';
    let indiceDuplicada = -1;
    
    this.estado.lista.forEach((categoria, index) => {
      if (categoria.nome && categoria.nome.trim() !== '') {
        if (categoriasUsadas.includes(categoria.nome)) {
          temDuplicada = true;
          indiceDuplicada = index;
          // Obter dados da categoria para mensagem mais informativa
          const dadosCategoria = this.estado.mapaCategorias[categoria.nome] || {};
          categoriaDuplicada = dadosCategoria.nome ? 
            `${categoria.nome} - ${dadosCategoria.nome}` : 
            categoria.nome;
        } else {
          categoriasUsadas.push(categoria.nome);
        }
      }
    });
    
    // Se há duplicada, mostrar modal
    if (temDuplicada && categoriaDuplicada) {
      const modalElement = document.getElementById('modalValidacao');
      const modalMensagem = document.getElementById('modalValidacaoMensagem');
      const btnEntendi = document.getElementById('btnEntendidoCategoria');
      
      if (modalElement && modalMensagem) {
        modalMensagem.textContent = `A categoria "${categoriaDuplicada}" foi selecionada mais de uma vez! Por favor, escolha categorias diferentes.`;
        
        // Configurar evento para limpar categoria duplicada ao clicar em "Entendi"
        if (btnEntendi) {
          // Remove listeners anteriores
          btnEntendi.onclick = null;
          
          btnEntendi.onclick = () => {
            
            // Limpa a categoria duplicada
            if (indiceDuplicada >= 0) {
              this.estado.lista[indiceDuplicada].nome = '';
              this.estado.lista[indiceDuplicada].id = '';

              // Atualiza o select correspondente usando o seletor correto
              const selectCategoria = document.querySelector(`#listaCategorias-${this.transacaoId} select[data-index="${indiceDuplicada}"]`);

              if (selectCategoria) {
                selectCategoria.value = '';
                selectCategoria.focus();

                // Força uma nova validação para reabilitar o botão se necessário
                this.validarTotalCompleto();
              } else {
                console.error('Select de categoria não encontrado para índice:', indiceDuplicada);
              }
            }
          };
        }
        
        // Mostrar modal apenas se não estiver já visível
        if (!modalElement.classList.contains('show')) {
          const modal = new bootstrap.Modal(modalElement);
          modal.show();
        }
      }
    }
    
    // Desabilitar botão salvar se há duplicadas
    const btnSalvar = document.getElementById(`btnSalvarAgendamento-${this.transacaoId}`);
    if (btnSalvar && temDuplicada) {
      btnSalvar.disabled = true;
      btnSalvar.classList.remove('btn-primary');
      btnSalvar.classList.add('btn-secondary');
    }
    
    return temDuplicada;
  }

  // === FUNÇÕES DE CENTROS DE CUSTO ===
  renderizarCentrosCusto() {
    const container = document.getElementById(`listaCentrosCusto-${this.transacaoId}`);
    container.innerHTML = '';
    
    this.estado.centrosCusto.forEach((centro, index) => {
      const div = document.createElement('div');
      div.className = 'row mb-3 align-items-center';
      div.innerHTML = this.getHtmlCentroCusto(centro, index);
      
      container.appendChild(div);
      
      // Definir valor do select
      const select = div.querySelector('select');
      select.value = centro.centro;
    });
    
    // Adicionar eventos
    this.adicionarEventosCentrosCusto();
  }

  getHtmlCentroCusto(centro, index) {
    return `
      <div class="col-md-6">
        <select class="form-select centro-select" data-index="${index}">
          <option value="">Selecione um centro de custo...</option>
          ${this.dadosIniciais.opcoesCentros || ''}
        </select>
      </div>
      <div class="col-md-2">
        <input type="text" class="form-control text-center campo-float percentual-input" 
               data-index="${index}" value="${centro.percentual}" placeholder="0,00" 
               ${this.estado.tipoDistribuicao === 'valor' ? 'disabled' : ''}>
      </div>
      <div class="col-md-3">
        <input type="text" class="form-control text-end campo-moeda-brl valor-centro-input"
               data-index="${index}" value="${this.formatarParaExibicao(centro.valor)}" placeholder="R$ 0,00"
               ${this.estado.tipoDistribuicao === 'percentual' ? 'disabled' : ''}>
      </div>
      <div class="col-md-1 text-center">
        <button type="button" class="btn btn-link text-danger p-1 btn-remover-centro" data-index="${index}"
                ${this.estado.centrosCusto.length <= 1 ? 'style="display:none"' : ''}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path stroke="none" d="M0 0h24v24H0z" fill="none" />
            <path d="M4 7l16 0" />
            <path d="M10 11l0 6" />
            <path d="M14 11l0 6" />
            <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />
            <path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" />
          </svg>
        </button>
      </div>
    `;
  }

  adicionarEventosCentrosCusto() {
    // Eventos para selects de centro
    document.querySelectorAll(`#listaCentrosCusto-${this.transacaoId} .centro-select`).forEach(select => {
      select.addEventListener('change', () => {
        const index = parseInt(select.dataset.index);
        this.estado.centrosCusto[index].centro = select.value;
        this.validarTotalCompleto();
      });
    });

    // Eventos para inputs de percentual
    document.querySelectorAll(`#listaCentrosCusto-${this.transacaoId} .percentual-input`).forEach(input => {
      input.addEventListener('input', () => {
        const index = parseInt(input.dataset.index);
        this.estado.centrosCusto[index].percentual = input.value;
        this.validarTotalCompleto();
      });
    });

    // Eventos para inputs de valor
    document.querySelectorAll(`#listaCentrosCusto-${this.transacaoId} .valor-centro-input`).forEach(input => {
      input.addEventListener('input', () => {
        const index = parseInt(input.dataset.index);
        this.aplicarMascaraCentroCusto(input, index);
      });
    });

    // Eventos para botões de remover
    document.querySelectorAll(`#listaCentrosCusto-${this.transacaoId} .btn-remover-centro`).forEach(btn => {
      btn.addEventListener('click', () => {
        const index = parseInt(btn.dataset.index);
        this.removerCentroCusto(index);
      });
    });
  }

  adicionarCentroCusto() {
    this.estado.centrosCusto.push({
      centro: '',
      percentual: '',
      valor: 0
    });
    this.renderizarCentrosCusto();
  }

  removerCentroCusto(index) {
    if (this.estado.centrosCusto.length > 1) {
      this.estado.centrosCusto.splice(index, 1);
      this.renderizarCentrosCusto();
      this.validarTotalCompleto();
    }
  }

  aplicarMascaraCentroCusto(input, index) {
    let valor = input.value.replace(/\D/g, '');
    const valorCentavos = parseInt(valor) || 0;
    this.estado.centrosCusto[index].valor = valorCentavos;
    input.value = this.formatarParaExibicao(valorCentavos);
    if (this.estado.mostrarValoresDetalhados) {
      this.validarTotalCompleto();
    }
  }

  validarCentrosCusto() {
    if (!this.estado.mostrarValoresDetalhados) return true;
    
    if (this.estado.tipoDistribuicao === 'valor') {
      let totalCentros = 0;
      this.estado.centrosCusto.forEach(centro => {
        if (centro.valor && centro.valor > 0) {
          totalCentros += centro.valor;
        }
      });
      return (totalCentros === this.estado.totalPagar || totalCentros === 0);
    } else if (this.estado.tipoDistribuicao === 'percentual') {
      let totalPercentual = 0;
      this.estado.centrosCusto.forEach(centro => {
        if (centro.percentual) {
          const percentual = parseFloat(centro.percentual.replace(',', '.')) || 0;
          totalPercentual += percentual;
        }
      });
      return (Math.abs(totalPercentual - 100) <= 0.01 || totalPercentual === 0);
    }
    return true;
  }

  // === FUNÇÕES DE PARCELAMENTO ===
  renderizarParcelas() {
    const tabelaContainer = document.getElementById(`tabelaParcelas-${this.transacaoId}`);
    const corpoTabela = document.getElementById(`corpoTabelaParcelas-${this.transacaoId}`);
    const totalDisplay = document.getElementById(`totalParcelas-${this.transacaoId}`);
    
    if (this.estado.parcelas.length > 0) {
      tabelaContainer.style.display = 'block';
      corpoTabela.innerHTML = '';
      
      this.estado.parcelas.forEach((parcela, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${(idx + 1)}/${this.estado.qtdParcelas}</td>
          <td>
            <input type="text" class="form-control text-start campo-moeda-brl"
                   value="${this.formatarMoeda(parcela.valor)}" readonly disabled>
          </td>
          <td>
            <input type="date" class="form-control vencimento-parcela" 
                   data-index="${idx}" value="${parcela.vencimento}">
          </td>
          <td>
            <input type="text" class="form-control descricao-parcela" 
                   data-index="${idx}" value="${parcela.descricao}" placeholder="Descrição">
          </td>
          <td>
            <input type="text" class="form-control referencia-parcela" 
                   data-index="${idx}" value="${parcela.referencia}" placeholder="Referência">
          </td>
        `;
        corpoTabela.appendChild(tr);
      });
      
      // Atualizar total
      totalDisplay.textContent = this.formatarMoeda(this.estado.totalParcelas);
      
      // Adicionar eventos
      this.adicionarEventosParcelas();
    } else {
      tabelaContainer.style.display = 'none';
    }
  }

  adicionarEventosParcelas() {
    // Eventos para vencimento
    document.querySelectorAll(`#corpoTabelaParcelas-${this.transacaoId} .vencimento-parcela`).forEach(input => {
      input.addEventListener('change', () => {
        const index = parseInt(input.dataset.index);
        this.estado.parcelas[index].vencimento = input.value;
      });
    });

    // Eventos para descrição
    document.querySelectorAll(`#corpoTabelaParcelas-${this.transacaoId} .descricao-parcela`).forEach(input => {
      input.addEventListener('input', () => {
        const index = parseInt(input.dataset.index);
        this.estado.parcelas[index].descricao = input.value;
      });
    });

    // Eventos para referência
    document.querySelectorAll(`#corpoTabelaParcelas-${this.transacaoId} .referencia-parcela`).forEach(input => {
      input.addEventListener('input', () => {
        const index = parseInt(input.dataset.index);
        this.estado.parcelas[index].referencia = input.value;
      });
    });
  }

  gerarParcelas() {
    if (!this.estado.qtdParcelas || this.estado.qtdParcelas < 1) {
      this.estado.parcelas = [];
      this.estado.totalParcelas = 0;
      this.renderizarParcelas();
      return;
    }
    
    this.estado.parcelas = [];
    const valorAgendamento = this.estado.totalPagar;
    const valorParcela = Math.floor(valorAgendamento / this.estado.qtdParcelas);
    let resto = valorAgendamento - (valorParcela * this.estado.qtdParcelas);
    
    // Definir a data base para o dia 10 do mês atual ou próximo
    let hoje = new Date();
    let ano = hoje.getFullYear();
    let mes = hoje.getMonth();
    if (hoje.getDate() > 10) {
      mes += 1;
      if (mes > 11) { mes = 0; ano += 1; }
    }
    let dataBase = new Date(ano, mes, 10);
    
    for (let i = 0; i < this.estado.qtdParcelas; i++) {
      let valor = valorParcela;
      if (resto > 0) {
        valor += 1;
        resto--;
      }
      let vencimento = new Date(dataBase);
      if (i > 0) {
        vencimento.setDate(vencimento.getDate() + (i * this.estado.diasEntre));
      }
      const vencStr = vencimento.toISOString().slice(0, 10);
      this.estado.parcelas.push({
        valor: valor,
        vencimento: vencStr,
        descricao: '',
        referencia: ''
      });
    }
    this.calcularTotalParcelas();
    this.renderizarParcelas();
  }

  calcularTotalParcelas() {
    this.estado.totalParcelas = this.estado.parcelas.reduce((acc, p) => acc + p.valor, 0);
  }

  initParcelamento() {
    if (this.estado.mostrarParcelamento && this.estado.qtdParcelas > 0) {
      this.gerarParcelas();
    } else {
      this.estado.parcelas = [];
      this.estado.totalParcelas = 0;
      this.renderizarParcelas();
    }
  }

  // === FUNÇÕES DE PREPARAÇÃO PARA ENVIO ===
  prepararEnvio() {
    // Preparar categorias com código + nome combinados
    const categoriasComDados = this.estado.lista.map(categoria => {
      const dadosCategoria = this.estado.mapaCategorias[categoria.nome] || {};
      const categoriaCompleta = dadosCategoria.nome ? 
        `${categoria.nome} - ${dadosCategoria.nome}` : 
        categoria.nome;
      
      return {
        categoria: categoriaCompleta,
        categoria_id: dadosCategoria.id || null,
        detalhamento: categoria.detalhamento,
        referencia: categoria.referencia,
        valor: categoria.valor
      };
    });
    
    // Preparar dados JSON para envio
    document.getElementById(`categorias_json-${this.transacaoId}`).value = JSON.stringify(categoriasComDados);
    
    // Enviar array vazio se valores detalhados não estiver ativo
    const centrosParaEnviar = this.estado.mostrarValoresDetalhados ? this.estado.centrosCusto : [];
    document.getElementById(`centros_custo_json-${this.transacaoId}`).value = JSON.stringify(centrosParaEnviar);
    
    document.getElementById(`parcelas_json-${this.transacaoId}`).value = JSON.stringify(this.estado.parcelas);
    document.getElementById(`valores_detalhados_ativo-${this.transacaoId}`).value = this.estado.mostrarValoresDetalhados;
    
    return true;
  }

  // === ENVIO AJAX ===
  async enviarFormulario() {
    const form = document.getElementById(`formNovaTransacao-${this.transacaoId}`);
    const btnSalvar = document.getElementById(`btnSalvarAgendamento-${this.transacaoId}`);
    
    try {
      // Desabilitar botão
      btnSalvar.disabled = true;
      btnSalvar.innerHTML = `
        <span class="spinner-border spinner-border-sm me-1" role="status"></span>
        Salvando...
      `;

      // Preparar dados
      this.prepararEnvio();

      // Fetch com async/await
      const response = await fetch('/api/salvar-nova-movimentacao', {
        method: 'POST',
        body: new FormData(form)
      });

      const resultado = await response.json();

      if (resultado.erro) {
        throw new Error(resultado.mensagem);
      }

      // Sucesso
      this.mostrarMensagem('Nova movimentação criada e conciliada com sucesso!', 'success');
      this.animarRemocaoTransacao();

    } catch (error) {
      console.error('Erro ao salvar:', error);
      this.mostrarMensagem(error.message || 'Erro ao salvar nova movimentação', 'danger');
      
      // Reabilitar botão
      btnSalvar.disabled = false;
      btnSalvar.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-plus">
          <path stroke="none" d="M0 0h24v24H0z" fill="none" />
          <path d="M12 5l0 14" />
          <path d="M5 12l14 0" />
        </svg>
        Salvar Categorização
      `;
    }
  }

  mostrarMensagem(mensagem, tipo) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1060; max-width: 350px;';
    toast.innerHTML = `
      ${mensagem}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    setTimeout(() => toast?.parentNode && toast.remove(), 5000);
  }

  animarRemocaoTransacao() {
    const linhaTransacao = document.querySelector(`.conciliacao-ofx-id-${this.transacaoId}`);
    
    if (!linhaTransacao) return;
    
    // Animação de sucesso seguida de remoção
    setTimeout(() => {
      Object.assign(linhaTransacao.style, {
        transition: 'all 0.6s ease-out',
        opacity: '0.6',
        backgroundColor: '#d4edda',
        border: '2px solid #28a745',
        borderRadius: '8px'
      });
      
      setTimeout(() => {
        linhaTransacao.style.transform = 'translateX(-100%)';
        setTimeout(() => linhaTransacao.remove(), 300);
      }, 800);
    }, 1000);
  }

  // === CONFIGURAÇÃO DE EVENTOS ===
  configurarEventos() {
    // Botão adicionar categoria
    document.getElementById(`btnAdicionarCategoria-${this.transacaoId}`)
      ?.addEventListener('click', () => this.adicionarCategoria());
    
    // Botão adicionar centro de custo
    document.getElementById(`btnAdicionarCentroCusto-${this.transacaoId}`)
      ?.addEventListener('click', () => this.adicionarCentroCusto());
    
    // Switch valores detalhados
    const switchValoresDetalhados = document.getElementById(`valoresDetalhados-${this.transacaoId}`);
    switchValoresDetalhados?.addEventListener('change', () => {
      this.estado.mostrarValoresDetalhados = switchValoresDetalhados.checked;
      const painel = document.getElementById(`painelValoresDetalhados-${this.transacaoId}`);
      
      if (this.estado.mostrarValoresDetalhados) {
        painel.style.display = 'block';
        this.renderizarCentrosCusto();
      } else {
        painel.style.display = 'none';
      }
      
      // Atualizar campo hidden
      document.getElementById(`valores_detalhados_ativo-${this.transacaoId}`).value = this.estado.mostrarValoresDetalhados;
      this.validarTotalCompleto();
    });
    
    // Switch parcelamento
    const switchParcelamento = document.getElementById(`parcelamento-${this.transacaoId}`);
    switchParcelamento?.addEventListener('change', () => {
      this.estado.mostrarParcelamento = switchParcelamento.checked;
      const painel = document.getElementById(`painelParcelamento-${this.transacaoId}`);
      
      if (this.estado.mostrarParcelamento) {
        painel.style.display = 'block';
        this.initParcelamento();
      } else {
        painel.style.display = 'none';
        this.estado.parcelas = [];
        this.estado.totalParcelas = 0;
        this.renderizarParcelas();
      }
    });
    
    // Eventos para tipo de distribuição
    document.querySelectorAll(`input[name="tipoDistribuicao-${this.transacaoId}"]`).forEach(radio => {
      radio.addEventListener('change', () => {
        this.estado.tipoDistribuicao = radio.value;
        this.renderizarCentrosCusto();
        this.validarTotalCompleto();
      });
    });
    
    // Eventos para parcelamento
    const selectQtdParcelas = document.getElementById(`qtdParcelas-${this.transacaoId}`);
    selectQtdParcelas?.addEventListener('change', () => {
      this.estado.qtdParcelas = parseInt(selectQtdParcelas.value) || 0;
      if (this.estado.qtdParcelas > 0) {
        this.gerarParcelas();
      } else {
        this.estado.parcelas = [];
        this.estado.totalParcelas = 0;
        this.renderizarParcelas();
      }
    });
    
    const selectDiasEntre = document.getElementById(`diasEntre-${this.transacaoId}`);
    selectDiasEntre?.addEventListener('change', () => {
      this.estado.diasEntre = parseInt(selectDiasEntre.value) || 30;
      if (this.estado.qtdParcelas > 0) {
        this.gerarParcelas();
      }
    });
    
    // Evento de submit do formulário
    document.getElementById(`formNovaTransacao-${this.transacaoId}`)
      ?.addEventListener('submit', (event) => {
        event.preventDefault();
        this.prepararEnvio();
        this.enviarFormulario();
        return false;
      });
  }

  // === INICIALIZAÇÃO ===
  init() {
    // Iniciar com uma categoria com o valor total da transação pré-preenchido
    this.estado.lista = [{
      nome: '',
      detalhamento: '',
      referencia: '',
      valor: this.estado.totalPagar // Pré-preencher com valor total da transação
    }];
    
    this.renderizarCategorias();
    
    // Forçar selects de categoria para vazios
    setTimeout(() => {
      document.querySelectorAll('.categoria-select').forEach(select => {
        select.value = '';
        select.selectedIndex = 0;
      });
    }, 50);

    // Inicializar painéis baseado nos dados
    const switchValoresDetalhados = document.getElementById(`valoresDetalhados-${this.transacaoId}`);
    if (switchValoresDetalhados) {
      switchValoresDetalhados.checked = this.estado.mostrarValoresDetalhados;
      const painelDetalhados = document.getElementById(`painelValoresDetalhados-${this.transacaoId}`);
      
      if (this.estado.mostrarValoresDetalhados) {
        painelDetalhados.style.display = 'block';
        this.renderizarCentrosCusto();
      } else {
        painelDetalhados.style.display = 'none';
      }
    }
    
    const switchParcelamento = document.getElementById(`parcelamento-${this.transacaoId}`);
    if (switchParcelamento) {
      switchParcelamento.checked = this.estado.mostrarParcelamento;
      const painelParcelamento = document.getElementById(`painelParcelamento-${this.transacaoId}`);
      
      if (this.estado.mostrarParcelamento) {
        painelParcelamento.style.display = 'block';
        // Definir valores iniciais nos selects
        const qtdSelect = document.getElementById(`qtdParcelas-${this.transacaoId}`);
        const diasSelect = document.getElementById(`diasEntre-${this.transacaoId}`);
        if (qtdSelect) qtdSelect.value = this.estado.qtdParcelas;
        if (diasSelect) diasSelect.value = this.estado.diasEntre;
        this.initParcelamento();
      } else {
        painelParcelamento.style.display = 'none';
      }
    }

    // Configurar todos os event listeners
    this.configurarEventos();

    // Aguardar um pouco e validar
    setTimeout(() => {
      this.validarTotalCompleto();
    }, 100);
  }
}

// Exportar para uso global
window.NovaTransacaoOFX = NovaTransacaoOFX;