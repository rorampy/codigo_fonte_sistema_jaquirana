
class ContasBancarias {
  constructor() {
    this.init();
  }

  init() {
    this.setupContasBancarias();
    this.setupModalForm();
    this.setupMascarasMoeda();
  }

  setupContasBancarias() {
    const contasBancarias = document.querySelectorAll('.conta-bancaria');

    contasBancarias.forEach(conta => {
      conta.addEventListener('click', (event) => {
        this.selecionarConta(event.currentTarget, contasBancarias);
      });
    });

  }

  selecionarConta(contaSelecionada, todasAsContas) {
    
    this.removerSelecaoAtual(todasAsContas);

    this.adicionarSelecao(contaSelecionada);

    const contaId = contaSelecionada.getAttribute('data-conta');
    const contaNome = contaSelecionada.getAttribute('data-nome');

    this.redirecionarParaConta(contaId);
  }

  removerSelecaoAtual(contas) {
    contas.forEach(conta => {
      conta.classList.remove('bg-warning-lt');
      const small = conta.querySelector('small');
      if (small && small.textContent.includes('Conta Selecionada')) {
        small.textContent = small.textContent.replace('Conta Selecionada', 'Conta Bancária');
      }
    });
  }

  adicionarSelecao(conta) {
    conta.classList.add('bg-warning-lt');
    const small = conta.querySelector('small');
    if (small) {
      small.textContent = 'Conta Selecionada';
    }
  }

  redirecionarParaConta(contaId) {
    if (contaId && contaId !== 'sem-conta') {
      
      const url = this.construirUrlConta(contaId);
      window.location.href = url;
    } else if (contaId === 'sem-conta') {
      
      const url = this.construirUrlSemConta();
      window.location.href = url;
    }
  }

  construirUrlConta(contaId) {
    const baseUrl = window.location.pathname;
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('conta_bancaria_id', contaId);
    return `${baseUrl}?${urlParams.toString()}`;
  }

  construirUrlSemConta() {
    const baseUrl = window.location.pathname;
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.delete('conta_bancaria_id');
    urlParams.set('sem_conta', '1');
    return `${baseUrl}?${urlParams.toString()}`;
  }

  setupModalForm() {
    const selectConta = document.getElementById('selectConta');
    const filtroForm = document.getElementById('filtroForm');

    if (selectConta && filtroForm) {
      selectConta.addEventListener('change', () => {
        filtroForm.submit();
      });
    }
  }

  setupMascarasMoeda() {
    const camposMoeda = document.querySelectorAll('.campo-moeda-brl');
    
    if (camposMoeda.length > 0) {
      camposMoeda.forEach(campo => {
        this.aplicarMascaraMoeda(campo);
      });
      
    }
  }

  aplicarMascaraMoeda(campo) {
    campo.addEventListener('input', (event) => {
      let valor = event.target.value;
      
      valor = valor.replace(/\D/g, '');
      
      valor = (valor / 100).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
      });
      
      event.target.value = valor;
    });

    if (!campo.placeholder) {
      campo.placeholder = 'R$ 0,00';
    }
  }

  debug() {
    const contas = document.querySelectorAll('.conta-bancaria');
  }
}

const ContasBancariasUtils = {
  
  formatarValorBRL(valor) {
    if (typeof valor !== 'number') return 'R$ 0,00';
    
    return (valor / 100).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  },

  obterParametrosUrl() {
    return Object.fromEntries(new URLSearchParams(window.location.search));
  },

  atualizarUrl(parametros) {
    const url = new URL(window.location);
    
    Object.keys(parametros).forEach(key => {
      if (parametros[key] !== null && parametros[key] !== '') {
        url.searchParams.set(key, parametros[key]);
      } else {
        url.searchParams.delete(key);
      }
    });
    
    window.history.pushState({}, '', url);
  }
};

document.addEventListener('DOMContentLoaded', function() {
  
  window.contasBancariasInstance = new ContasBancarias();
  
  window.ContasBancariasUtils = ContasBancariasUtils;
  
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ContasBancarias, ContasBancariasUtils };
}