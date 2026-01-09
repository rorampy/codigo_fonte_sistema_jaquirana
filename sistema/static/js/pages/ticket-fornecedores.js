/**
 * Gerenciamento de múltiplos fornecedores com distribuição de peso
 */
class GerenciadorFornecedoresTicket {
  constructor() {
    this.pesoTotal = 0;
    this.contador = 0;
    this.init();
  }

  init() {
    // Elementos principais
    this.container = document.getElementById('fornecedoresContainer');
    this.template = document.getElementById('fornecedorTemplate');
    this.inputPesoTotal = document.getElementById('pesoLiquido');
    this.progressBar = document.getElementById('progressBarDistribuicao');
    this.displayTotal = document.getElementById('pesoTotalDisplay');
    this.displayDistribuido = document.getElementById('pesoDistribuidoDisplay');
    this.displayRestante = document.getElementById('pesoRestanteDisplay');
    this.modalAviso = document.getElementById('modal-aviso');
    this.modalConfirmacao = document.getElementById('modal-confirmacao');

    // Eventos
    document.getElementById('btnAdicionarFornecedor')?.addEventListener('click', () => this.adicionar());
    this.inputPesoTotal?.addEventListener('input', () => this.atualizar());
    
    const form = document.getElementById('formTicket') || document.querySelector('form');
    form?.addEventListener('submit', (e) => this.validar(e));

    // Adicionar primeiro fornecedor (se não estiver em modo edição)
    if (typeof fornecedoresExistentes === 'undefined' || fornecedoresExistentes.length === 0) {
      this.adicionar();
    }

    // Ler valor inicial do peso total (importante para edição)
    this.atualizar();
  }

  adicionar() {
    if (!this.template || !this.container) return;

    const item = this.template.querySelector('.fornecedor-item').cloneNode(true);
    this.contador++;
    item.dataset.id = this.contador;

    // Badge para identificar
    if (this.contador > 1) {
      const badge = document.createElement('span');
      badge.className = 'badge badge-outline text-default ms-2';
      badge.textContent = `#${this.contador}`;
      item.querySelector('label')?.appendChild(badge);
    }

    // Select do fornecedor
    const select = item.querySelector('.fornecedor-select');
    if (select) {
      select.required = true;
      try {
        new TomSelect(select, {
          create: false,
          allowEmptyOption: false,
          sortField: { field: "text", direction: "asc" },
          placeholder: "Selecione um fornecedor..."
        });
      } catch (e) { }
    }

    // Input do peso
    const inputPeso = item.querySelector('.peso-fornecedor');
    if (inputPeso) {
      inputPeso.required = true;
      inputPeso.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^\d.,]/g, '').replace(',', '.');
        this.atualizar();
      });
      inputPeso.addEventListener('blur', (e) => {
        const val = parseFloat(e.target.value) || 0;
        e.target.value = val.toFixed(2);
        this.atualizar();
      });
    }

    // Botão remover
    const btnRemover = item.querySelector('.btn-remover-fornecedor');
    btnRemover?.addEventListener('click', () => this.remover(item));

    this.container.appendChild(item);
    this.atualizarBotoes();
    this.atualizar();
  }

  remover(item) {
    item.remove();
    this.atualizarBotoes();
    this.atualizar();
  }

  atualizarBotoes() {
    const items = this.container.querySelectorAll('.fornecedor-item');
    const unico = items.length === 1;
    items.forEach(item => {
      const btn = item.querySelector('.btn-remover-fornecedor');
      if (btn) {
        btn.disabled = unico;
        btn.classList.toggle('disabled', unico);
      }
    });
  }

  atualizar() {
    this.pesoTotal = parseFloat(this.inputPesoTotal?.value) || 0;
    
    // Calcular peso distribuído
    const inputs = this.container.querySelectorAll('.peso-fornecedor');
    const distribuido = Array.from(inputs).reduce((sum, inp) => sum + (parseFloat(inp.value) || 0), 0);
    const restante = Math.max(0, this.pesoTotal - distribuido);
    const pct = this.pesoTotal > 0 ? (distribuido / this.pesoTotal * 100) : 0;

    // Atualizar displays
    if (this.displayTotal) this.displayTotal.textContent = this.pesoTotal.toFixed(2);
    if (this.displayDistribuido) this.displayDistribuido.textContent = distribuido.toFixed(2);
    if (this.displayRestante) {
      this.displayRestante.textContent = restante.toFixed(2);
      this.displayRestante.className = distribuido > this.pesoTotal ? 'text-danger' : 
        (restante === 0 && this.pesoTotal > 0 ? 'text-success' : 'text-primary');
    }

    // Atualizar barra de progresso
    if (this.progressBar) {
      const prog = Math.min(100, pct);
      this.progressBar.style.width = `${prog}%`;
      this.progressBar.textContent = `${prog.toFixed(0)}%`;
      this.progressBar.className = 'progress-bar ' + (
        distribuido > this.pesoTotal ? 'bg-danger' :
        distribuido === this.pesoTotal && this.pesoTotal > 0 ? 'bg-success' :
        pct > 80 ? 'bg-warning' : 'bg-primary'
      );
    }

    // Validar campos de peso
    inputs.forEach(inp => {
      inp.classList.remove('is-invalid');
      inp.parentElement.querySelector('.invalid-feedback')?.remove();
    });
    
    if (distribuido > this.pesoTotal && this.pesoTotal > 0) {
      inputs.forEach(inp => {
        inp.classList.add('is-invalid');
        const fb = document.createElement('div');
        fb.className = 'invalid-feedback';
        fb.textContent = 'A soma dos pesos excede o peso total!';
        inp.parentElement.appendChild(fb);
      });
    }
  }

  mostrarAviso(titulo, msg, callback) {
    if (!this.modalAviso) {
      alert(msg);
      callback?.();
      return;
    }
    document.getElementById('modal-aviso-titulo').textContent = titulo;
    document.getElementById('modal-aviso-mensagem').textContent = msg;
    const modal = new bootstrap.Modal(this.modalAviso);
    if (callback) {
      this.modalAviso.addEventListener('hidden.bs.modal', function handler() {
        this.removeEventListener('hidden.bs.modal', handler);
        callback();
      });
    }
    modal.show();
  }

  mostrarConfirmacao(titulo, msg, onConfirm, onCancel) {
    if (!this.modalConfirmacao) {
      confirm(msg) ? onConfirm?.() : onCancel?.();
      return;
    }
    document.getElementById('modal-confirmacao-titulo').textContent = titulo;
    document.getElementById('modal-confirmacao-mensagem').textContent = msg;
    
    const modal = new bootstrap.Modal(this.modalConfirmacao);
    const btnOk = document.getElementById('btn-confirmacao-confirmar');
    const btnNo = document.getElementById('btn-confirmacao-cancelar');
    
    // Clonar para limpar eventos antigos
    const newOk = btnOk.cloneNode(true);
    const newNo = btnNo.cloneNode(true);
    btnOk.replaceWith(newOk);
    btnNo.replaceWith(newNo);
    
    newOk.addEventListener('click', () => { modal.hide(); onConfirm?.(); });
    newNo.addEventListener('click', () => { modal.hide(); onCancel?.(); });
    
    modal.show();
  }

  validar(e) {
    const items = this.container.querySelectorAll('.fornecedor-item');
    
    // Sem fornecedores
    if (items.length === 0) {
      e.preventDefault();
      this.mostrarAviso('Atenção', 'Adicione pelo menos um fornecedor!');
      return false;
    }

    // Sem peso total
    if (this.pesoTotal <= 0) {
      e.preventDefault();
      this.mostrarAviso('Atenção', 'Informe o peso total do ticket!', () => this.inputPesoTotal?.focus());
      return false;
    }

    // Coletar e validar dados
    const dados = [];
    let valido = true;
    let distribuido = 0;

    items.forEach(item => {
      const select = item.querySelector('.fornecedor-select');
      const inputPeso = item.querySelector('.peso-fornecedor');
      const fornecedorId = select.tomselect ? select.tomselect.getValue() : select.value;
      const peso = parseFloat(inputPeso.value) || 0;

      // Validar select
      if (!fornecedorId) {
        select.classList.add('is-invalid');
        valido = false;
      } else {
        select.classList.remove('is-invalid');
        dados.push({ fornecedor_id: fornecedorId, peso: peso.toFixed(2) });
      }

      // Validar peso
      if (peso <= 0) {
        inputPeso.classList.add('is-invalid');
        let fb = inputPeso.parentElement.querySelector('.invalid-feedback');
        if (!fb) {
          fb = document.createElement('div');
          fb.className = 'invalid-feedback';
          inputPeso.parentElement.appendChild(fb);
        }
        fb.textContent = 'O peso deve ser maior que zero!';
        valido = false;
      }

      distribuido += peso;
    });

    // Serializar dados
    const hidden = document.getElementById('fornecedoresData');
    if (hidden) hidden.value = JSON.stringify(dados);

    // Peso excede total
    if (distribuido > this.pesoTotal) {
      e.preventDefault();
      return false;
    }

    if (!valido) {
      e.preventDefault();
      return false;
    }

    // Peso não totalmente distribuído - pedir confirmação
    if (distribuido < this.pesoTotal) {
      e.preventDefault();
      const restante = (this.pesoTotal - distribuido).toFixed(2);
      this.mostrarConfirmacao(
        'Peso não distribuído',
        `Ainda há ${restante} Ton. não distribuídas. Deseja continuar?`,
        () => e.target.submit()
      );
      return false;
    }

    return true;
  }
}

// Inicializar
document.readyState === 'loading' 
  ? document.addEventListener('DOMContentLoaded', () => new GerenciadorFornecedoresTicket())
  : new GerenciadorFornecedoresTicket();
