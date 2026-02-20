
class VendasEmTransitoListagem {
    constructor() {
        this.timeoutId = null;
        this.DELAY = 500; 
        this.loadingIndicator = null;
        this.tabelaResultados = null;
        this.campos = {};
        
        this.inicializar();
    }

    inicializar() {
        this.inicializarElementos();
        this.inicializarEventListeners();
        this.preencherValoresExistentes();
    }

    inicializarElementos() {
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.tabelaResultados = document.getElementById('tabela-resultados');
        
        this.campos = {
            cliente: document.getElementById('search-cliente'),
            nf: document.getElementById('search-nf'),
            transportadora: document.getElementById('search-transportadora'),
            dataInicio: document.getElementById('data-inicio'),
            dataFim: document.getElementById('data-fim')
        };
    }

    preencherValoresExistentes() {
        
        const parametrosUrl = new URLSearchParams(window.location.search);
        
        const clienteVenda = parametrosUrl.get('cliente_venda');
        if (clienteVenda && this.campos.cliente) {
            this.campos.cliente.value = clienteVenda;
        }
        
        const nfVenda = parametrosUrl.get('nf_venda');
        if (nfVenda && this.campos.nf) {
            this.campos.nf.value = nfVenda;
        }
        
        const transportadora = parametrosUrl.get('transportadora_venda');
        if (transportadora && this.campos.transportadora) {
            this.campos.transportadora.value = transportadora;
        }

        const dataInicio = parametrosUrl.get('data_inicio');
        if (dataInicio && this.campos.dataInicio) {
            this.campos.dataInicio.value = dataInicio;
        }

        const dataFim = parametrosUrl.get('data_fim');
        if (dataFim && this.campos.dataFim) {
            this.campos.dataFim.value = dataFim;
        }
    }

    inicializarEventListeners() {
        
        if (this.campos.cliente) {
            this.campos.cliente.addEventListener('input', () => this.buscarComDelay());
        }
        if (this.campos.nf) {
            this.campos.nf.addEventListener('input', () => this.buscarComDelay());
        }
        if (this.campos.transportadora) {
            this.campos.transportadora.addEventListener('input', () => this.buscarComDelay());
        }

        if (this.campos.dataInicio) {
            this.campos.dataInicio.addEventListener('change', () => this.buscarComDelay());
        }
        if (this.campos.dataFim) {
            this.campos.dataFim.addEventListener('change', () => this.buscarComDelay());
        }

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

    campoVazio(campo) {
        return campo.value.trim() === '';
    }

    mostrarLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'block';
        }
    }

    esconderLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
        }
    }

    realizarBusca() {
        
        const params = new URLSearchParams();
        
        if (this.campos.cliente && this.campos.cliente.value.trim()) {
            params.append('cliente_venda', this.campos.cliente.value.trim());
        }
        if (this.campos.nf && this.campos.nf.value.trim()) {
            params.append('nf_venda', this.campos.nf.value.trim());
        }
        if (this.campos.transportadora && this.campos.transportadora.value.trim()) {
            params.append('transportadora_venda', this.campos.transportadora.value.trim());
        }
        if (this.campos.dataInicio && this.campos.dataInicio.value) {
            params.append('data_inicio', this.campos.dataInicio.value);
        }
        if (this.campos.dataFim && this.campos.dataFim.value) {
            params.append('data_fim', this.campos.dataFim.value);
        }

        const temFiltro = Array.from(params.values()).some(value => value.trim() !== '');

        if (!temFiltro) {
            
            this.redirecionarParaPaginaOriginal();
            return;
        }

        this.mostrarLoading();

        const urlAjax = this.obterUrlAjax();

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

    obterUrlAjax() {
        
        const elemento = document.querySelector('[data-ajax-url]');
        if (elemento) {
            return elemento.dataset.ajaxUrl;
        }
        
        const url = new URL(window.location.href);
        const pathname = url.pathname;
        
        if (pathname.includes('/busca-rapida-ajax')) {
            return pathname;
        }
        
        return pathname + '/busca-rapida-ajax';
    }

    atualizarTabelaEPaginacao(html) {
        
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const novoTbody = doc.getElementById('tabela-resultados');
        
        if (novoTbody && this.tabelaResultados) {
            
            this.tabelaResultados.innerHTML = novoTbody.innerHTML;

            const novaPaginacao = doc.querySelector('.card-footer');
            const paginacaoAtual = document.querySelector('.card-footer');
            if (paginacaoAtual && novaPaginacao) {
                paginacaoAtual.innerHTML = novaPaginacao.innerHTML;
            }

            this.reativarTooltips();
        }
    }

    reativarTooltips() {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                new bootstrap.Tooltip(tooltip);
            }
        });
    }

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

    buscarComDelay() {
        clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(() => this.realizarBusca(), this.DELAY);
    }

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

    redirecionarParaPaginaOriginal() {
        
        const url = new URL(window.location.href);
        
        url.searchParams.delete('cliente_venda');
        url.searchParams.delete('nf_venda');
        url.searchParams.delete('transportadora_venda');
        url.searchParams.delete('data_inicio');
        url.searchParams.delete('data_fim');
        url.searchParams.delete('pagina');
        
        let pathname = url.pathname;
        if (pathname.includes('/busca-rapida-ajax')) {
            pathname = pathname.replace('/busca-rapida-ajax', '');
        }
        
        const urlFinal = `${url.origin}${pathname}`;
        
        window.location.href = urlFinal;
    }

    limparFiltros() {
        Object.values(this.campos).forEach(campo => {
            if (campo) {
                campo.value = '';
            }
        });
        this.redirecionarParaPaginaOriginal();
    }

    obterFiltros() {
        const filtros = {};
        
        if (this.campos.cliente && this.campos.cliente.value.trim()) {
            filtros.cliente_venda = this.campos.cliente.value.trim();
        }
        if (this.campos.nf && this.campos.nf.value.trim()) {
            filtros.nf_venda = this.campos.nf.value.trim();
        }
        if (this.campos.transportadora && this.campos.transportadora.value.trim()) {
            filtros.transportadora_venda = this.campos.transportadora.value.trim();
        }
        if (this.campos.dataInicio && this.campos.dataInicio.value) {
            filtros.data_inicio = this.campos.dataInicio.value;
        }
        if (this.campos.dataFim && this.campos.dataFim.value) {
            filtros.data_fim = this.campos.dataFim.value;
        }
        
        return filtros;
    }

    definirFiltros(filtros) {
        if (filtros.cliente_venda && this.campos.cliente) {
            this.campos.cliente.value = filtros.cliente_venda;
        }
        if (filtros.nf_venda && this.campos.nf) {
            this.campos.nf.value = filtros.nf_venda;
        }
        if (filtros.transportadora_venda && this.campos.transportadora) {
            this.campos.transportadora.value = filtros.transportadora_venda;
        }
        if (filtros.data_inicio && this.campos.dataInicio) {
            this.campos.dataInicio.value = filtros.data_inicio;
        }
        if (filtros.data_fim && this.campos.dataFim) {
            this.campos.dataFim.value = filtros.data_fim;
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    
    window.vendasEmTransitoListagem = new VendasEmTransitoListagem();
    
    window.obterFiltrosVendasEmTransito = () => window.vendasEmTransitoListagem.obterFiltros();
    window.definirFiltrosVendasEmTransito = (filtros) => window.vendasEmTransitoListagem.definirFiltros(filtros);
    window.limparFiltrosVendasEmTransito = () => window.vendasEmTransitoListagem.limparFiltros();
});