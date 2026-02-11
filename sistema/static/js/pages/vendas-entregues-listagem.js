/**
 * JavaScript para Listagem de Vendas Entregues
 * Funcionalidades: Busca rápida com AJAX, filtros em tempo real
 */

class VendasEntreguesListagem {
    constructor() {
        this.timeoutId = null;
        this.DELAY = 500; // 500ms de delay para debouncing
        this.loadingIndicator = null;
        this.tabelaResultados = null;
        this.campos = {};
        
        this.inicializar();
    }

    /**
     * Inicializa o componente
     */
    inicializar() {
        this.inicializarElementos();
        this.inicializarEventListeners();
        this.preencherValoresExistentes();
    }

    /**
     * Inicializa elementos do DOM
     */
    inicializarElementos() {
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.tabelaResultados = document.getElementById('tabela-resultados');
        
        this.campos = {
            cliente: document.getElementById('search-cliente'),
            nf: document.getElementById('search-nf'),
            fornecedor: document.getElementById('search-fornecedor'),
            dataInicio: document.getElementById('data-inicio'),
            dataFim: document.getElementById('data-fim'),
            tipoDataFiltro: document.getElementById('tipo-data-filtro')
        };
    }

    /**
     * Preenche valores existentes dos filtros (se estiver vindo de uma busca)
     */
    preencherValoresExistentes() {
        // Manter os valores dos filtros se estiver vindo de uma busca com parâmetros
        const parametrosUrl = new URLSearchParams(window.location.search);
        
        const clienteVenda = parametrosUrl.get('cliente_venda');
        if (clienteVenda && this.campos.cliente) {
            this.campos.cliente.value = clienteVenda;
        }
        
        const nfVenda = parametrosUrl.get('nf_venda');
        if (nfVenda && this.campos.nf) {
            this.campos.nf.value = nfVenda;
        }
        
        const origemVenda = parametrosUrl.get('origem_venda');
        if (origemVenda && this.campos.fornecedor) {
            this.campos.fornecedor.value = origemVenda;
        }

        const dataInicio = parametrosUrl.get('data_inicio');
        if (dataInicio && this.campos.dataInicio) {
            this.campos.dataInicio.value = dataInicio;
        }

        const dataFim = parametrosUrl.get('data_fim');
        if (dataFim && this.campos.dataFim) {
            this.campos.dataFim.value = dataFim;
        }

        const tipoDataFiltro = parametrosUrl.get('tipo_data_filtro');
        if (tipoDataFiltro && this.campos.tipoDataFiltro) {
            this.campos.tipoDataFiltro.value = tipoDataFiltro;
        }
    }

    /**
     * Inicializa event listeners
     */
    inicializarEventListeners() {
        // Adiciona event listeners para campos de texto
        if (this.campos.cliente) {
            this.campos.cliente.addEventListener('input', () => this.buscarComDelay());
        }
        if (this.campos.nf) {
            this.campos.nf.addEventListener('input', () => this.buscarComDelay());
        }
        if (this.campos.fornecedor) {
            this.campos.fornecedor.addEventListener('input', () => this.buscarComDelay());
        }

        // Adiciona event listeners para campos de data (usar 'change' em vez de 'input')
        if (this.campos.dataInicio) {
            this.campos.dataInicio.addEventListener('change', () => this.buscarComDelay());
        }
        if (this.campos.dataFim) {
            this.campos.dataFim.addEventListener('change', () => this.buscarComDelay());
        }

        // Adiciona event listener para select de tipo de data
        if (this.campos.tipoDataFiltro) {
            this.campos.tipoDataFiltro.addEventListener('change', () => this.buscarComDelay());
        }

        // Event listener para detectar quando todos os campos ficam vazios
        Object.values(this.campos).forEach(campo => {
            if (campo) {
                const eventType = campo.type === 'date' ? 'change' : 'input';
                campo.addEventListener(eventType, () => {
                    if (this.campoVazio(campo)) {
                        setTimeout(() => this.verificarCamposVazios(), 100);
                    }
                });
            }
        });
    }

    /**
     * Verifica se um campo está vazio
     * @param {HTMLElement} campo - Campo para verificar
     * @returns {boolean}
     */
    campoVazio(campo) {
        return campo.value.trim() === '';
    }

    /**
     * Função para mostrar loading
     */
    mostrarLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'block';
        }
    }

    /**
     * Função para esconder loading
     */
    esconderLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
        }
    }

    /**
     * Função para realizar a busca AJAX
     */
    realizarBusca() {
        // Coleta todos os valores dos campos
        const params = new URLSearchParams();
        
        if (this.campos.cliente && this.campos.cliente.value.trim()) {
            params.append('cliente_venda', this.campos.cliente.value.trim());
        }
        if (this.campos.nf && this.campos.nf.value.trim()) {
            params.append('nf_venda', this.campos.nf.value.trim());
        }
        if (this.campos.fornecedor && this.campos.fornecedor.value.trim()) {
            params.append('origem_venda', this.campos.fornecedor.value.trim());
        }
        if (this.campos.dataInicio && this.campos.dataInicio.value) {
            params.append('data_inicio', this.campos.dataInicio.value);
        }
        if (this.campos.dataFim && this.campos.dataFim.value) {
            params.append('data_fim', this.campos.dataFim.value);
        }
        if (this.campos.tipoDataFiltro && this.campos.tipoDataFiltro.value) {
            params.append('tipo_data_filtro', this.campos.tipoDataFiltro.value);
        }

        // Verifica se pelo menos um campo tem valor
        const temFiltro = Array.from(params.values()).some(value => value.trim() !== '');

        if (!temFiltro) {
            // Se não há filtros, recarrega a página original
            this.redirecionarParaPaginaOriginal();
            return;
        }

        this.mostrarLoading();

        // Obtém a URL da função AJAX
        const urlAjax = this.obterUrlAjax();

        // Realiza a requisição AJAX
        fetch(`${urlAjax}?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            this.atualizarTabelaEPaginacao(html);
        })
        .catch(error => {
            console.error('Erro na busca:', error);
            this.exibirErro();
        })
        .finally(() => {
            this.esconderLoading();
        });
    }

    /**
     * Obtém a URL da função AJAX (configurável)
     * @returns {string} URL da função AJAX
     */
    obterUrlAjax() {
        // URL da rota AJAX - pode ser configurada via data attribute ou global
        const elemento = document.querySelector('[data-ajax-url]');
        if (elemento) {
            return elemento.dataset.ajaxUrl;
        }
        
        // Fallback: construir URL baseada na URL atual
        const url = new URL(window.location.href);
        const pathname = url.pathname;
        
        // Se já está na rota de filtro, manter
        if (pathname.includes('/busca-rapida-ajax')) {
            return pathname;
        }
        
        // Caso contrário, adicionar /busca-rapida-ajax
        return pathname + '/busca-rapida-ajax';
    }

    /**
     * Atualiza tabela e paginação com novo HTML
     * @param {string} html - HTML retornado do servidor
     */
    atualizarTabelaEPaginacao(html) {
        // Cria um documento temporário para parsear o HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Extrai apenas o conteúdo da tabela
        const novoTbody = doc.getElementById('tabela-resultados');
        
        if (novoTbody && this.tabelaResultados) {
            // Substitui o conteúdo da tabela
            this.tabelaResultados.innerHTML = novoTbody.innerHTML;

            // Atualiza a paginação se existir
            const novaPaginacao = doc.querySelector('.card-footer');
            const paginacaoAtual = document.querySelector('.card-footer');
            if (paginacaoAtual && novaPaginacao) {
                paginacaoAtual.innerHTML = novaPaginacao.innerHTML;
            }

            // Reativar tooltips se necessário
            this.reativarTooltips();
        }
    }

    /**
     * Reativa tooltips do Bootstrap nos novos elementos
     */
    reativarTooltips() {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            // Verificar se o Bootstrap está disponível
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                new bootstrap.Tooltip(tooltip);
            }
        });
    }

    /**
     * Exibe mensagem de erro na tabela
     */
    exibirErro() {
        if (this.tabelaResultados) {
            this.tabelaResultados.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-danger p-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mb-2">
                            <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                            <path d="M12 9v4"/>
                            <path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z"/>
                            <path d="M12 16h.01"/>
                        </svg>
                        <br>
                        Erro ao carregar os dados. Tente novamente.
                    </td>
                </tr>
            `;
        }
    }

    /**
     * Função debounced para busca
     */
    buscarComDelay() {
        clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(() => this.realizarBusca(), this.DELAY);
    }

    /**
     * Verifica se todos os campos estão vazios e redireciona se necessário
     */
    verificarCamposVazios() {
        const todosVazios = Object.values(this.campos).every(campo => {
            if (!campo) return true;
            return campo.value.trim() === '';
        });

        if (todosVazios) {
            clearTimeout(this.timeoutId);
            this.redirecionarParaPaginaOriginal();
        }
    }

    /**
     * Redireciona para a página original sem filtros
     */
    redirecionarParaPaginaOriginal() {
        // Obtém URL original sem parâmetros de busca
        const url = new URL(window.location.href);
        
        // Remove parâmetros de filtro
        url.searchParams.delete('cliente_venda');
        url.searchParams.delete('nf_venda');
        url.searchParams.delete('origem_venda');
        url.searchParams.delete('data_inicio');
        url.searchParams.delete('data_fim');
        url.searchParams.delete('pagina');
        
        // Simplifica a URL removendo '/busca-rapida-ajax' se existir
        let pathname = url.pathname;
        if (pathname.includes('/busca-rapida-ajax')) {
            pathname = pathname.replace('/busca-rapida-ajax', '');
        }
        
        // Constrói URL final
        const urlFinal = `${url.origin}${pathname}`;
        
        window.location.href = urlFinal;
    }

    /**
     * Limpa todos os filtros
     */
    limparFiltros() {
        Object.values(this.campos).forEach(campo => {
            if (campo) {
                campo.value = '';
            }
        });
        this.redirecionarParaPaginaOriginal();
    }

    /**
     * Obtém valores atuais dos filtros
     * @returns {Object} Objeto com valores dos filtros
     */
    obterFiltros() {
        const filtros = {};
        
        if (this.campos.cliente && this.campos.cliente.value.trim()) {
            filtros.cliente_venda = this.campos.cliente.value.trim();
        }
        if (this.campos.nf && this.campos.nf.value.trim()) {
            filtros.nf_venda = this.campos.nf.value.trim();
        }
        if (this.campos.fornecedor && this.campos.fornecedor.value.trim()) {
            filtros.origem_venda = this.campos.fornecedor.value.trim();
        }
        if (this.campos.dataInicio && this.campos.dataInicio.value) {
            filtros.data_inicio = this.campos.dataInicio.value;
        }
        if (this.campos.dataFim && this.campos.dataFim.value) {
            filtros.data_fim = this.campos.dataFim.value;
        }
        
        return filtros;
    }

    /**
     * Define valores dos filtros
     * @param {Object} filtros - Objeto com valores dos filtros
     */
    definirFiltros(filtros) {
        if (filtros.cliente_venda && this.campos.cliente) {
            this.campos.cliente.value = filtros.cliente_venda;
        }
        if (filtros.nf_venda && this.campos.nf) {
            this.campos.nf.value = filtros.nf_venda;
        }
        if (filtros.origem_venda && this.campos.fornecedor) {
            this.campos.fornecedor.value = filtros.origem_venda;
        }
        if (filtros.data_inicio && this.campos.dataInicio) {
            this.campos.dataInicio.value = filtros.data_inicio;
        }
        if (filtros.data_fim && this.campos.dataFim) {
            this.campos.dataFim.value = filtros.data_fim;
        }
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar o componente
    window.vendasEntreguesListagem = new VendasEntreguesListagem();
    
    // Expor métodos úteis globalmente (opcional)
    window.obterFiltrosVendasEntregues = () => window.vendasEntreguesListagem.obterFiltros();
    window.definirFiltrosVendasEntregues = (filtros) => window.vendasEntreguesListagem.definirFiltros(filtros);
    window.limparFiltrosVendasEntregues = () => window.vendasEntreguesListagem.limparFiltros();
});