/**
 * JavaScript para Listagem de Despesas Avulsas
 * Funcionalidades: Seleção múltipla, cálculo de totais, controles de checkboxes
 */

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

    /**
     * Inicializa o componente
     */
    inicializar() {
        this.inicializarElementos();
        this.inicializarTomSelect();
        this.inicializarEventListeners();
        this.inicializarPesquisa();
        this.atualizarTotais();
    }

    /**
     * Inicializa elementos do DOM
     */
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

    /**
     * Inicializa TomSelect para selects
     */
    inicializarTomSelect() {
        // Inicializar TomSelect apenas em selects FORA de modais
        document.querySelectorAll('select.form-select:not(.modal-select)').forEach(function (select) {
            if (!select.closest('.modal')) {
                new TomSelect(select, {
                    create: false,
                    allowEmptyOption: false,
                });
            }
        });
    }

    /**
     * Inicializa event listeners
     */
    inicializarEventListeners() {
        // Event listener para "Selecionar Todos" (painel principal)
        if (this.selecionarTodos) {
            this.selecionarTodos.addEventListener('change', () => {
                this.alternarTodos(this.selecionarTodos.checked);
            });
        }

        // Event listener para "Selecionar Todos" (cabeçalho da tabela)
        if (this.selecionarTodosCabecalho) {
            this.selecionarTodosCabecalho.addEventListener('change', () => {
                this.alternarTodos(this.selecionarTodosCabecalho.checked);
            });
        }

        // Event listeners para checkboxes individuais
        this.checkboxesItens.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.atualizarTotais();
            });
        });
    }

    /**
     * Alterna seleção de todos os itens
     * @param {boolean} marcado - Estado do checkbox
     */
    alternarTodos(marcado) {
        this.checkboxesItens.forEach(checkbox => {
            checkbox.checked = marcado;
        });
        
        if (this.selecionarTodos) this.selecionarTodos.checked = marcado;
        if (this.selecionarTodosCabecalho) this.selecionarTodosCabecalho.checked = marcado;
        
        this.atualizarTotais();
    }

    /**
     * Formata valor em formato BRL
     * @param {number} valor - Valor para formatar
     * @returns {string} Valor formatado
     */
    formatarValor(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    }

    /**
     * Atualiza totais de seleção
     */
    atualizarTotais() {
        let total = 0;
        let quantidade = 0;

        this.checkboxesItens.forEach(checkbox => {
            if (checkbox.checked) {
                const valorString = checkbox.dataset.valor || '0';
                const valorNumerico = parseFloat(valorString.replace(',', '.'));

                // Debug opcional - remover em produção
                if (window.DEBUG_DESPESAS) {
                    console.log('=== CHECKBOX DEBUG ===');
                    console.log('ID:', checkbox.dataset.id);
                    console.log('Valor String:', valorString);
                    console.log('Valor Numérico:', valorNumerico);
                    console.log('Debug Info:', checkbox.dataset.debug);
                    console.log('======================');
                }

                if (!isNaN(valorNumerico) && valorNumerico > 0) {
                    total += valorNumerico;
                    quantidade++;
                }
            }
        });

        // Debug opcional - remover em produção
        if (window.DEBUG_DESPESAS) {
            console.log('TOTAL FINAL:', total.toFixed(2), 'QUANTIDADE:', quantidade);
        }

        // Atualizar elementos de exibição
        if (this.totalSelecionado) {
            this.totalSelecionado.textContent = this.formatarValor(total);
        }
        
        if (this.quantidadeSelecionada) {
            this.quantidadeSelecionada.textContent = quantidade;
        }

        // Atualizar estado dos checkboxes "selecionar todos"
        this.atualizarEstadoCheckboxesMestre();
    }

    /**
     * Atualiza o estado dos checkboxes mestre (selecionar todos)
     */
    atualizarEstadoCheckboxesMestre() {
        const arrayCheckboxes = Array.from(this.checkboxesItens);
        const todosMarcados = arrayCheckboxes.length > 0 && arrayCheckboxes.every(cb => cb.checked);
        const algumMarcado = arrayCheckboxes.some(cb => cb.checked);

        // Atualizar checkboxes "selecionar todos"
        if (this.selecionarTodos) {
            this.selecionarTodos.checked = todosMarcados;
            this.selecionarTodos.indeterminate = algumMarcado && !todosMarcados;
        }

        if (this.selecionarTodosCabecalho) {
            this.selecionarTodosCabecalho.checked = todosMarcados;
            this.selecionarTodosCabecalho.indeterminate = algumMarcado && !todosMarcados;
        }
    }

    /**
     * Obtém IDs dos itens selecionados
     * @returns {Array<string>} Array com IDs dos itens selecionados
     */
    obterItensSelecionados() {
        const selecionados = [];
        this.checkboxesItens.forEach(checkbox => {
            if (checkbox.checked && checkbox.dataset.id) {
                selecionados.push(checkbox.dataset.id);
            }
        });
        return selecionados;
    }

    /**
     * Obtém total de valor selecionado
     * @returns {number} Valor total selecionado
     */
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

    /**
     * Limpa todas as seleções
     */
    limparSelecoes() {
        this.alternarTodos(false);
    }

    /**
     * Inicializa funcionalidade de pesquisa
     */
    inicializarPesquisa() {
        if (!this.inputPesquisa) return;

        // Manter os valores dos filtros no campo após reload
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

        // Event listener para pesquisa - executar quando sair do campo (blur) ou pressionar Enter
        this.inputPesquisa.addEventListener('blur', (e) => {
            this.manipularPesquisa(e);
        });
        
        this.inputPesquisa.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.manipularPesquisa(e);
            }
        });

        // Se houver inputs de data, escutar mudanças e disparar pesquisa
        if (this.inputDataInicio) {
            this.inputDataInicio.addEventListener('change', () => this.manipularFiltroData());
        }
        if (this.inputDataFim) {
            this.inputDataFim.addEventListener('change', () => this.manipularFiltroData());
        }
        
        // Event listener para botão limpar filtros
        if (this.botaoLimparFiltros) {
            this.botaoLimparFiltros.addEventListener('click', () => this.limparFiltros());
        }
    }

    /**
     * Manipula evento de pesquisa
     * @param {Event} e - Evento de blur ou Enter
     */
    manipularPesquisa(e) {
        const termo = this.inputPesquisa.value.trim();
        
        // Limpar timeout anterior
        clearTimeout(this.timeoutPesquisa);
        
        // Se o campo estiver vazio, recarregar a página normal
        if (termo.length === 0) {
            this.executarPesquisa('');
            return;
        }
        
        // Executar pesquisa se tiver pelo menos 2 caracteres
        if (termo.length >= 2) {
            this.executarPesquisa(termo);
        } else {
            // Mostrar feedback se for muito curto
            this.inputPesquisa.style.borderColor = '#ffc107';
            this.inputPesquisa.title = 'Digite pelo menos 2 caracteres para pesquisar';
            
            // Remover feedback após 2 segundos
            setTimeout(() => {
                this.inputPesquisa.style.borderColor = '';
                this.inputPesquisa.title = '';
            }, 2000);
        }
    }

    /**
     * Executa pesquisa
     * @param {string} termo - Termo de pesquisa
     */
    executarPesquisa(termo) {
        // Fazer busca via fetch e atualizar apenas o corpo da tabela e a paginação
        this.mostrarIndicadorCarregamento();

        const url = new URL(window.location.href);
        if (termo && termo.length >= 2) {
            url.searchParams.set('pesquisa', termo);
        } else {
            url.searchParams.delete('pesquisa');
        }
        url.searchParams.set('pagina', 1);

        // incluir filtros de data se existirem
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

        // Executar fetch
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

    /**
     * Manipula filtros de data (change)
     */
    manipularFiltroData() {
        // pequeno debounce para evitar chamadas em sequência rápida
        clearTimeout(this.timeoutPesquisa);
        this.timeoutPesquisa = setTimeout(() => {
            this.executarPesquisa(this.inputPesquisa ? this.inputPesquisa.value.trim() : '');
        }, 300);
    }

    /**
     * Limpa todos os filtros e recarrega a listagem
     */
    limparFiltros() {
        // Limpar valores dos campos
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

        // Fazer uma busca vazia para recarregar todos os dados
        this.executarPesquisa('');
    }

    /**
     * Substitui tbody da tabela e a área de paginação com o HTML retornado pelo servidor
     * @param {string} html
     */
    substituirTabelaEPaginacao(html) {
        const analisador = new DOMParser();
        const documento = analisador.parseFromString(html, 'text/html');

        // Extrair novo corpo da tabela
        const novoTbody = documento.querySelector('#corpo-tabela-despesas');
        const tBodyAtual = document.querySelector('#tabela-despesas-avulsas tbody');
        if (novoTbody && tBodyAtual) {
            tBodyAtual.innerHTML = novoTbody.innerHTML;
        }

        // Extrair nova paginação (card-footer)
        const novoCardFooter = documento.querySelector('#paginacao-despesas');
        const cardFooterAtual = document.querySelector('#paginacao-despesas');
        if (novoCardFooter && cardFooterAtual) {
            cardFooterAtual.innerHTML = novoCardFooter.innerHTML;
        }

        // Substituir containers de modais para que os botões apontem para modais válidos
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

        // Re-bind elementos e eventos (checkboxes etc.)
        this.reconectarAposAtualizacao();
    }

    /**
     * Atualiza referências a elementos e reanexa event listeners após substituição do DOM
     */
    reconectarAposAtualizacao() {
        // atualizar NodeList de checkboxes
        this.checkboxesItens = document.querySelectorAll('.item-checkbox');

        // anexar listeners a cada checkbox
        this.checkboxesItens.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.atualizarTotais();
            });
        });

        // reanexar selecionarTodosCabecalho (se novo)
        this.selecionarTodosCabecalho = document.getElementById('selectAllHeader');
        if (this.selecionarTodosCabecalho) {
            this.selecionarTodosCabecalho.addEventListener('change', () => {
                this.alternarTodos(this.selecionarTodosCabecalho.checked);
            });
        }

        // reformatar totais
        this.atualizarTotais();
    }

    /**
     * Redireciona para página sem parâmetros de pesquisa
     */
    redirecionarParaPagina() {
        // Mostrar indicador de carregamento
        this.mostrarIndicadorCarregamento();
        
        // Criar URL da página sem parâmetros de pesquisa
        const url = new URL(window.location.href);
        url.searchParams.delete('pesquisa');
        url.searchParams.set('pagina', 1);
        
        setTimeout(() => {
            window.location.href = url.toString();
        }, 150);
    }

    /**
     * Mostra indicador de carregamento
     */
    mostrarIndicadorCarregamento() {
        // Trocar ícone de pesquisa por spinner
        const iconeSearch = document.getElementById('search-icon');
        const iconeCarregamento = document.getElementById('search-loading');
        
        if (iconeSearch && iconeCarregamento) {
            iconeSearch.classList.add('d-none');
            iconeCarregamento.classList.remove('d-none');
        }

        // Desabilitar input temporariamente
        if (this.inputPesquisa) {
            this.inputPesquisa.style.opacity = '0.7';
            this.inputPesquisa.disabled = true;
        }
    }

    /**
     * Esconde indicador de carregamento
     */
    esconderIndicadorCarregamento() {
        // Restaurar ícone de pesquisa
        const iconeSearch = document.getElementById('search-icon');
        const iconeCarregamento = document.getElementById('search-loading');
        
        if (iconeSearch && iconeCarregamento) {
            iconeSearch.classList.remove('d-none');
            iconeCarregamento.classList.add('d-none');
        }

        // Reabilitar input
        if (this.inputPesquisa) {
            this.inputPesquisa.style.opacity = '1';
            this.inputPesquisa.disabled = false;
        }
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar o componente
    window.despesaListagem = new DespesaAvulsaListagem();
    
    // Expor métodos úteis globalmente (opcional)
    window.obterItensSelecionados = () => window.despesaListagem.obterItensSelecionados();
    window.obterTotalSelecionado = () => window.despesaListagem.obterTotalSelecionado();
    window.limparSelecoes = () => window.despesaListagem.limparSelecoes();
});