/**
 * JavaScript para a página de Contas Bancárias
 * Responsável pelas funcionalidades de seleção de contas e interatividade da interface
 */

class ContasBancarias {
  constructor() {
    this.init();
  }

  /**
   * Inicializa todas as funcionalidades da página
   */
  init() {
    this.setupContasBancarias();
    this.setupModalForm();
    this.setupMascarasMoeda();
    console.log('ContasBancarias: Funcionalidades inicializadas');
  }

  /**
   * Configura a funcionalidade de seleção de contas bancárias
   */
  setupContasBancarias() {
    const contasBancarias = document.querySelectorAll('.conta-bancaria');

    contasBancarias.forEach(conta => {
      conta.addEventListener('click', (event) => {
        this.selecionarConta(event.currentTarget, contasBancarias);
      });
    });

    console.log(`ContasBancarias: ${contasBancarias.length} contas configuradas`);
  }

  /**
   * Seleciona uma conta bancária e atualiza a interface
   * @param {HTMLElement} contaSelecionada - Elemento da conta clicada
   * @param {NodeList} todasAsContas - Lista de todas as contas
   */
  selecionarConta(contaSelecionada, todasAsContas) {
    // Remove a seleção atual
    this.removerSelecaoAtual(todasAsContas);

    // Adiciona seleção na conta clicada
    this.adicionarSelecao(contaSelecionada);

    // Obtém dados da conta
    const contaId = contaSelecionada.getAttribute('data-conta');
    const contaNome = contaSelecionada.getAttribute('data-nome');

    // Log para debugging
    console.log('ContasBancarias: Conta selecionada:', { id: contaId, nome: contaNome });

    // Redireciona para a página com a conta selecionada
    this.redirecionarParaConta(contaId);
  }

  /**
   * Remove a seleção visual de todas as contas
   * @param {NodeList} contas - Lista de todas as contas
   */
  removerSelecaoAtual(contas) {
    contas.forEach(conta => {
      conta.classList.remove('bg-warning-lt');
      const small = conta.querySelector('small');
      if (small && small.textContent.includes('Conta Selecionada')) {
        small.textContent = small.textContent.replace('Conta Selecionada', 'Conta Bancária');
      }
    });
  }

  /**
   * Adiciona seleção visual na conta especificada
   * @param {HTMLElement} conta - Conta a ser selecionada
   */
  adicionarSelecao(conta) {
    conta.classList.add('bg-warning-lt');
    const small = conta.querySelector('small');
    if (small) {
      small.textContent = 'Conta Selecionada';
    }
  }

  /**
   * Redireciona para a página com a conta selecionada
   * @param {string} contaId - ID da conta selecionada
   */
  redirecionarParaConta(contaId) {
    if (contaId && contaId !== 'sem-conta') {
      // Para contas bancárias normais
      const url = this.construirUrlConta(contaId);
      window.location.href = url;
    } else if (contaId === 'sem-conta') {
      // Para lançamentos sem conta
      const url = this.construirUrlSemConta();
      window.location.href = url;
    }
  }

  /**
   * Constrói a URL para uma conta específica
   * @param {string} contaId - ID da conta
   * @returns {string} URL construída
   */
  construirUrlConta(contaId) {
    const baseUrl = window.location.pathname;
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('conta_bancaria_id', contaId);
    return `${baseUrl}?${urlParams.toString()}`;
  }

  /**
   * Constrói a URL para lançamentos sem conta
   * @returns {string} URL construída
   */
  construirUrlSemConta() {
    const baseUrl = window.location.pathname;
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.delete('conta_bancaria_id');
    urlParams.set('sem_conta', '1');
    return `${baseUrl}?${urlParams.toString()}`;
  }

  /**
   * Configura a funcionalidade do modal de seleção de conta
   */
  setupModalForm() {
    const selectConta = document.getElementById('selectConta');
    const filtroForm = document.getElementById('filtroForm');

    if (selectConta && filtroForm) {
      selectConta.addEventListener('change', () => {
        console.log('ContasBancarias: Submetendo formulário do modal');
        filtroForm.submit();
      });
    }
  }

  /**
   * Configura máscaras de moeda nos campos de filtro
   */
  setupMascarasMoeda() {
    const camposMoeda = document.querySelectorAll('.campo-moeda-brl');
    
    if (camposMoeda.length > 0) {
      camposMoeda.forEach(campo => {
        this.aplicarMascaraMoeda(campo);
      });
      
      console.log(`ContasBancarias: ${camposMoeda.length} campos de moeda configurados`);
    }
  }

  /**
   * Aplica máscara de moeda brasileira em um campo
   * @param {HTMLElement} campo - Campo de input
   */
  aplicarMascaraMoeda(campo) {
    campo.addEventListener('input', (event) => {
      let valor = event.target.value;
      
      // Remove tudo que não for dígito
      valor = valor.replace(/\D/g, '');
      
      // Converte para formato de moeda
      valor = (valor / 100).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
      });
      
      event.target.value = valor;
    });

    // Placeholder padrão
    if (!campo.placeholder) {
      campo.placeholder = 'R$ 0,00';
    }
  }

  /**
   * Método utilitário para debugs
   */
  debug() {
    const contas = document.querySelectorAll('.conta-bancaria');
    console.log('ContasBancarias: Debug Info', {
      totalContas: contas.length,
      contaSelecionada: document.querySelector('.conta-bancaria.bg-warning-lt'),
      url: window.location.href,
      parametros: Object.fromEntries(new URLSearchParams(window.location.search))
    });
  }
}

/**
 * Funcionalidades auxiliares globais
 */
const ContasBancariasUtils = {
  /**
   * Formata valor para exibição em BRL
   * @param {number} valor - Valor em centavos
   * @returns {string} Valor formatado
   */
  formatarValorBRL(valor) {
    if (typeof valor !== 'number') return 'R$ 0,00';
    
    return (valor / 100).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  },

  /**
   * Obtém parâmetros da URL
   * @returns {Object} Objeto com os parâmetros
   */
  obterParametrosUrl() {
    return Object.fromEntries(new URLSearchParams(window.location.search));
  },

  /**
   * Atualiza URL sem recarregar a página
   * @param {Object} parametros - Novos parâmetros
   */
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

/**
 * Inicialização quando o DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('ContasBancarias: Inicializando página de Contas Bancárias...');
  
  // Instancia a classe principal
  window.contasBancariasInstance = new ContasBancarias();
  
  // Adiciona utilitários ao window para acesso global
  window.ContasBancariasUtils = ContasBancariasUtils;
  
  console.log('ContasBancarias: Página inicializada com sucesso!');
});

/**
 * Exporta para uso em outros módulos (se necessário)
 */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ContasBancarias, ContasBancariasUtils };
}