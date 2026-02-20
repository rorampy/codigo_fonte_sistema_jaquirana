
class DespesaAvulsaListagem {
    constructor() {
        this.selecionarTodos = null;
        this.selecionarTodosCabecalho = null;
        this.checkboxesItens = null;
        this.totalSelecionado = null;
        this.quantidadeSelecionada = null;
        this.inputPesquisa = null;
        this.timeoutPesquisa = null;
        
        this.inicializar();
    }

    inicializar() {
        this.inicializarElementos();
        this.inicializarTomSelect();
        this.inicializarEventListeners();
        this.inicializarPesquisa();
        this.atualizarTotais();
    }

    inicializarElementos() {
        this.selecionarTodos = document.getElementById('selectAll');
        this.selecionarTodosCabecalho = document.getElementById('selectAllHeader');
        this.checkboxesItens = document.querySelectorAll('.item-checkbox');
        this.totalSelecionado = document.getElementById('totalSelecionado');
        this.quantidadeSelecionada = document.getElementById('quantidadeSelecionada');
        this.inputPesquisa = document.getElementById('search-despesas-avulsas');
        this.inputDataInicio = document.getElementById('data-inicio');
        this.inputDataFim = document.getElementById('data-fim');
        this.botaoLimparFiltros = document.getElementById('limpar-filtros');
    }

    inicializarTomSelect() {
        
        document.querySelectorAll('select.form-select:not(.modal-select)').forEach(function (select) {
            if (!select.closest('.modal')) {
                new TomSelect(select, {
                    create: false,
                    allowEmptyOption: false,
                });
            }
        });
    }

    inicializarEventListeners() {
        
        if (this.selecionarTodos) {
            this.selecionarTodos.addEventListener('change', () => {
                this.alternarTodos(this.selecionarTodos.checked);
            });
        }

        if (this.selecionarTodosCabecalho) {
            this.selecionarTodosCabecalho.addEventListener('change', () => {
                this.alternarTodos(this.selecionarTodosCabecalho.checked);
            });
        }

        this.checkboxesItens.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.atualizarTotais();
            });
        });
    }

    alternarTodos(marcado) {
        this.checkboxesItens.forEach(checkbox => {
            checkbox.checked = marcado;
        });
        
        if (this.selecionarTodos) this.selecionarTodos.checked = marcado;
        if (this.selecionarTodosCabecalho) this.selecionarTodosCabecalho.checked = marcado;
        
        this.atualizarTotais();
    }

    formatarValor(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    }

    atualizarTotais() {
        let total = 0;
        let quantidade = 0;

        this.checkboxesItens.forEach(checkbox => {
            if (checkbox.checked) {
                const valorString = checkbox.dataset.valor || '0';
                const valorNumerico = parseFloat(valorString.replace(',', '.'));

                if (window.DEBUG_DESPESAS) {
                }

                if (!isNaN(valorNumerico) && valorNumerico > 0) {
                    total += valorNumerico;
                    quantidade++;
                }
            }
        });

        if (window.DEBUG_DESPESAS) {
        }

        if (this.totalSelecionado) {
            this.totalSelecionado.textContent = this.formatarValor(total);
        }
        
        if (this.quantidadeSelecionada) {
            this.quantidadeSelecionada.textContent = quantidade;
        }

        this.atualizarEstadoCheckboxesMestre();
    }

    atualizarEstadoCheckboxesMestre() {
        const arrayCheckboxes = Array.from(this.checkboxesItens);
        const todosMarcados = arrayCheckboxes.length > 0 && arrayCheckboxes.every(cb => cb.checked);
        const algumMarcado = arrayCheckboxes.some(cb => cb.checked);

        if (this.selecionarTodos) {
            this.selecionarTodos.checked = todosMarcados;
            this.selecionarTodos.indeterminate = algumMarcado && !todosMarcados;
        }

        if (this.selecionarTodosCabecalho) {
            this.selecionarTodosCabecalho.checked = todosMarcados;
            this.selecionarTodosCabecalho.indeterminate = algumMarcado && !todosMarcados;
        }
    }

    obterItensSelecionados() {
        const selecionados = [];
        this.checkboxesItens.forEach(checkbox => {
            if (checkbox.checked && checkbox.dataset.id) {
                selecionados.push(checkbox.dataset.id);
            }
        });
        return selecionados;
    }

    obterTotalSelecionado() {
        let total = 0;
        this.checkboxesItens.forEach(checkbox => {
            if (checkbox.checked) {
                const valorString = checkbox.dataset.valor || '0';
                const valorNumerico = parseFloat(valorString.replace(',', '.'));
                if (!isNaN(valorNumerico) && valorNumerico > 0) {
                    total += valorNumerico;
                }
            }
        });
        return total;
    }

    limparSelecoes() {
        this.alternarTodos(false);
    }

    inicializarPesquisa() {
        if (!this.inputPesquisa) return;

        const parametrosUrl = new URLSearchParams(window.location.search);
        
        const termoPesquisa = parametrosUrl.get('pesquisa');
        if (termoPesquisa) {
            this.inputPesquisa.value = termoPesquisa;
        }
        
        const dataInicio = parametrosUrl.get('data_inicio');
        if (dataInicio && this.inputDataInicio) {
            this.inputDataInicio.value = dataInicio;
        }
        
        const dataFim = parametrosUrl.get('data_fim');
        if (dataFim && this.inputDataFim) {
            this.inputDataFim.value = dataFim;
        }

        this.inputPesquisa.addEventListener('blur', (e) => {
            this.manipularPesquisa(e);
        });
        
        this.inputPesquisa.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.manipularPesquisa(e);
            }
        });

        if (this.inputDataInicio) {
            this.inputDataInicio.addEventListener('change', () => this.manipularFiltroData());
        }
        if (this.inputDataFim) {
            this.inputDataFim.addEventListener('change', () => this.manipularFiltroData());
        }
        
        if (this.botaoLimparFiltros) {
            this.botaoLimparFiltros.addEventListener('click', () => this.limparFiltros());
        }
    }

    manipularPesquisa(e) {
        const termo = this.inputPesquisa.value.trim();
        
        clearTimeout(this.timeoutPesquisa);
        
        if (termo.length === 0) {
            this.executarPesquisa('');
            return;
        }
        
        if (termo.length >= 2) {
            this.executarPesquisa(termo);
        } else {
            
            this.inputPesquisa.style.borderColor = '#ffc107';
            this.inputPesquisa.title = 'Digite pelo menos 2 caracteres para pesquisar';
            
            setTimeout(() => {
                this.inputPesquisa.style.borderColor = '';
                this.inputPesquisa.title = '';
            }, 2000);
        }
    }

    executarPesquisa(termo) {
        
        this.mostrarIndicadorCarregamento();

        const url = new URL(window.location.href);
        if (termo && termo.length >= 2) {
            url.searchParams.set('pesquisa', termo);
        } else {
            url.searchParams.delete('pesquisa');
        }
        url.searchParams.set('pagina', 1);

        if (this.inputDataInicio && this.inputDataInicio.value) {
            url.searchParams.set('data_inicio', this.inputDataInicio.value);
        } else {
            url.searchParams.delete('data_inicio');
        }
        if (this.inputDataFim && this.inputDataFim.value) {
            url.searchParams.set('data_fim', this.inputDataFim.value);
        } else {
            url.searchParams.delete('data_fim');
        }

        fetch(url.toString(), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => response.text())
            .then(html => {
                this.substituirTabelaEPaginacao(html);
            })
            .catch(err => {
                console.error('Erro na busca:', err);
            })
            .finally(() => {
                this.esconderIndicadorCarregamento();
            });
    }

    manipularFiltroData() {
        
        clearTimeout(this.timeoutPesquisa);
        this.timeoutPesquisa = setTimeout(() => {
            this.executarPesquisa(this.inputPesquisa ? this.inputPesquisa.value.trim() : '');
        }, 300);
    }

    limparFiltros() {
        
        if (this.inputPesquisa) {
            this.inputPesquisa.value = '';
            this.inputPesquisa.style.borderColor = '';
            this.inputPesquisa.title = '';
        }
        if (this.inputDataInicio) {
            this.inputDataInicio.value = '';
        }
        if (this.inputDataFim) {
            this.inputDataFim.value = '';
        }

        this.executarPesquisa('');
    }

    substituirTabelaEPaginacao(html) {
        const analisador = new DOMParser();
        const documento = analisador.parseFromString(html, 'text/html');

        const novoTbody = documento.querySelector('#corpo-tabela-despesas');
        const tBodyAtual = document.querySelector('#tabela-despesas-avulsas tbody');
        if (novoTbody && tBodyAtual) {
            tBodyAtual.innerHTML = novoTbody.innerHTML;
        }

        const novoCardFooter = documento.querySelector('#paginacao-despesas');
        const cardFooterAtual = document.querySelector('#paginacao-despesas');
        if (novoCardFooter && cardFooterAtual) {
            cardFooterAtual.innerHTML = novoCardFooter.innerHTML;
        }

        const idsModais = [
            'container-modais-faturamento',
            'container-modais-excluir',
            'container-modais-lancamento',
            'container-modais-liquidacao'
        ];
        idsModais.forEach(id => {
            const novoContainer = documento.getElementById(id);
            const containerAtual = document.getElementById(id);
            if (novoContainer && containerAtual) {
                containerAtual.innerHTML = novoContainer.innerHTML;
            }
        });

        this.reconectarAposAtualizacao();
    }

    reconectarAposAtualizacao() {
        
        this.checkboxesItens = document.querySelectorAll('.item-checkbox');

        this.checkboxesItens.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.atualizarTotais();
            });
        });

        this.selecionarTodosCabecalho = document.getElementById('selectAllHeader');
        if (this.selecionarTodosCabecalho) {
            this.selecionarTodosCabecalho.addEventListener('change', () => {
                this.alternarTodos(this.selecionarTodosCabecalho.checked);
            });
        }

        this.atualizarTotais();
    }

    redirecionarParaPagina() {
        
        this.mostrarIndicadorCarregamento();
        
        const url = new URL(window.location.href);
        url.searchParams.delete('pesquisa');
        url.searchParams.set('pagina', 1);
        
        setTimeout(() => {
            window.location.href = url.toString();
        }, 150);
    }

    mostrarIndicadorCarregamento() {
        
        const iconeSearch = document.getElementById('search-icon');
        const iconeCarregamento = document.getElementById('search-loading');
        
        if (iconeSearch && iconeCarregamento) {
            iconeSearch.classList.add('d-none');
            iconeCarregamento.classList.remove('d-none');
        }

        if (this.inputPesquisa) {
            this.inputPesquisa.style.opacity = '0.7';
            this.inputPesquisa.disabled = true;
        }
    }

    esconderIndicadorCarregamento() {
        
        const iconeSearch = document.getElementById('search-icon');
        const iconeCarregamento = document.getElementById('search-loading');
        
        if (iconeSearch && iconeCarregamento) {
            iconeSearch.classList.remove('d-none');
            iconeCarregamento.classList.add('d-none');
        }

        if (this.inputPesquisa) {
            this.inputPesquisa.style.opacity = '1';
            this.inputPesquisa.disabled = false;
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    
    window.despesaListagem = new DespesaAvulsaListagem();
    
    window.obterItensSelecionados = () => window.despesaListagem.obterItensSelecionados();
    window.obterTotalSelecionado = () => window.despesaListagem.obterTotalSelecionado();
    window.limparSelecoes = () => window.despesaListagem.limparSelecoes();
});