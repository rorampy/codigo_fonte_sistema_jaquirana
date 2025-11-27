/**
 * ============================================================================
 * SISTEMA DE FILTROS PARA CONCILIAÇÃO OFX - ES6
 * ============================================================================
 * 
 * Módulo responsável por gerenciar filtros de busca de agendamentos
 * na funcionalidade "Buscar Existente" da conciliação OFX.
 * 
 * FUNCIONALIDADES:
 * - Coleta de dados dos filtros (valor, data, categoria, beneficiário, descrição)
 * - Requisições AJAX para endpoint de busca
 * - Renderização dinâmica dos resultados na tabela
 * - Integração com sistema de loading e estados
 * - Conversão automática de valores monetários
 * - Tratamento de erros e feedback visual
 * 
 * ARQUITETURA ES6:
 * - Classe principal: ConciliacaoOfxFiltros
 * - Métodos privados com #
 * - Async/await para operações assíncronas
 * - Destructuring e arrow functions
 * - Template literals para strings
 * 
 * ============================================================================
 */

class ConciliacaoOfxFiltros {
    constructor() {
        this.endpoints = {
            buscarAgendamentos: '/api/buscar-agendamentos'
        };
        
        this.seletores = {
            btnBuscar: (transacaoId) => `#btn-buscar-agendamentos-${transacaoId}`,
            filtros: {
                valorMin: (transacaoId) => `#filtro-valor-min-${transacaoId}`,
                valorMax: (transacaoId) => `#filtro-valor-max-${transacaoId}`,
                dataInicio: (transacaoId) => `#filtro-data-inicio-${transacaoId}`,
                dataFim: (transacaoId) => `#filtro-data-fim-${transacaoId}`,
                categoria: (transacaoId) => `#filtro-categoria-${transacaoId}`,
                beneficiario: (transacaoId) => `#filtro-beneficiario-${transacaoId}`,
                descricao: (transacaoId) => `#filtro-descricao-${transacaoId}`
            },
            tabela: {
                tbody: (transacaoId) => `#tbody-agendamentos-${transacaoId}`,
                info: (transacaoId) => `#info-agendamentos-${transacaoId}`
            }
        };
        
        this.#inicializar();
    }

    /**
     * Inicializa os event listeners
     * @private
     */
    #inicializar() {
        // Inicializar imediatamente se DOM já estiver pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.#configurarEventos();
            });
        } else {
            // DOM já carregado, configurar eventos diretamente
            this.#configurarEventos();
        }
    }

    /**
     * Configura event listeners para todos os botões de busca
     * @private
     */
    #configurarEventos() {
        // Usar delegação de eventos no document para capturar todos os cliques
        document.addEventListener('click', (event) => {
            // Verificar se o clique foi em um botão de busca ou seus elementos filhos
            const btnBuscar = event.target.closest('[id^="btn-buscar-agendamentos-"]');
            
            if (btnBuscar) {
                event.preventDefault();
                event.stopPropagation();
                
                const transacaoId = btnBuscar.dataset.transacaoId;
                if (transacaoId) {
                    this.buscarAgendamentos(transacaoId);
                }
                return false;
            }
            
            // Botões de conciliação individual
            const btnConciliacao = event.target.closest('.btn.conciliacao-btn[data-agendamento-id]');
            if (btnConciliacao) {
                event.preventDefault();
                const agendamentoId = btnConciliacao.dataset.agendamentoId;
                const transacaoId = btnConciliacao.dataset.transacaoId;
                
                if (agendamentoId && transacaoId) {
                    this.#processarConciliacao(agendamentoId, transacaoId);
                }
            }
        }, true); // Usar captura para garantir que pegamos o evento antes de outros handlers
    }

    /**
     * Executa a busca de agendamentos com filtros
     * @param {string} transacaoId - ID da transação
     * @public
     */
    async buscarAgendamentos(transacaoId) {
        try {
            // Mostrar loading
            this.#exibirCarregando(transacaoId);
            
            // Coletar filtros
            const filtros = this.#coletarFiltros(transacaoId);
            
            // Fazer requisição AJAX
            const response = await fetch(this.endpoints.buscarAgendamentos, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(filtros)
            });

            if (!response.ok) {
                throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success && Array.isArray(data.agendamentos)) {
                await this.#renderResults(transacaoId, data.agendamentos);
                this.#showSuccessToast(data.agendamentos.length);
            } else {
                throw new Error(data.error || data.message || 'Nenhum agendamento encontrado');
            }

        } catch (error) {
            this.#showError(transacaoId);
            this.#showErrorToast(error.message);
        }
    }

    /**
     * Coleta dados de todos os filtros de busca
     * @param {string} transacaoId - ID da transação para identificar os filtros
     * @returns {Object} Objeto com todos os filtros coletados
     * @private
     */
    #coletarFiltros(transacaoId) {
        const btnBuscar = document.querySelector(this.seletores.btnBuscar(transacaoId));
        
        // Extrair conta_bancaria_id da URL atual (formato: /conciliacao-ofx/<conta_id>)
        const urlPath = window.location.pathname;
        const contaIdMatch = urlPath.match(/\/conciliacao-ofx\/(\d+)/);
        const contaBancariaId = contaIdMatch ? contaIdMatch[1] : null;
        
        return {
            is_credit: btnBuscar?.dataset.isCredit || 'false',
            conta_bancaria_id: contaBancariaId,
            valor_min: this.#converterMoedaParaFloat(
                document.querySelector(this.seletores.filtros.valorMin(transacaoId))?.value
            ),
            valor_max: this.#converterMoedaParaFloat(
                document.querySelector(this.seletores.filtros.valorMax(transacaoId))?.value
            ),
            data_inicio: document.querySelector(this.seletores.filtros.dataInicio(transacaoId))?.value || null,
            data_fim: document.querySelector(this.seletores.filtros.dataFim(transacaoId))?.value || null,
            categoria: document.querySelector(this.seletores.filtros.categoria(transacaoId))?.value || null,
            beneficiario_id: document.querySelector(this.seletores.filtros.beneficiario(transacaoId))?.value || null,
            descricao: document.querySelector(this.seletores.filtros.descricao(transacaoId))?.value?.trim() || null
        };
    }

    /**
     * Converte valor monetário para float
     * @param {string} valorString - Valor no formato "R$ 1.234,56"
     * @returns {number|null} Valor convertido ou null se inválido
     * @private
     */
    #converterMoedaParaFloat(valorString) {
        if (!valorString?.trim()) return null;
        
        // Remover R$, espaços, pontos de milhares e converter vírgula para ponto decimal
        const cleanValue = valorString
            .replace(/R\$\s?/g, '')
            .replace(/\./g, '')
            .replace(',', '.')
            .trim();
        
        const parsedValue = parseFloat(cleanValue);
        return isNaN(parsedValue) ? null : parsedValue;
    }

    /**
     * Renderiza os resultados na tabela
     * @param {string} transacaoId - ID da transação
     * @param {Array} agendamentos - Lista de agendamentos encontrados
     * @private
     */
    async #renderResults(transacaoId, agendamentos) {
        const tbody = document.querySelector(this.seletores.tabela.tbody(transacaoId));
        
        if (!tbody) {
            return;
        }

        // Limpar tabela
        tbody.innerHTML = '';

        if (agendamentos.length === 0) {
            this.#showEmptyState(transacaoId);
            return;
        }

        // Criar fragmento para melhor performance
        const fragment = document.createDocumentFragment();
        
        agendamentos.forEach((agendamento) => {
            const row = this.#createAgendamentoRow(agendamento, transacaoId);
            fragment.appendChild(row);
        });

        tbody.appendChild(fragment);

        // Configurar eventos e mostrar tabela
        this.#setupTableEvents(transacaoId);
        this.#showTable(transacaoId);
        this.#updateInfo(transacaoId, agendamentos.length);
    }

    /**
     * Cria uma linha da tabela para um agendamento
     * @param {Object} agendamento - Dados do agendamento
     * @param {string} transacaoId - ID da transação
     * @returns {HTMLTableRowElement} Elemento TR da tabela
     * @private
     */
    #createAgendamentoRow(agendamento, transacaoId) {
        const tr = document.createElement('tr');
        tr.dataset.agendamentoId = agendamento.id;
        
        const {
            categoriasHtml,
            descricaoTruncada,
            origemDisplay,
            valorDisplay,
            valorTitulo
        } = this.#prepareRowData(agendamento);

        tr.innerHTML = `
            <td>
                <input class="form-check-input m-0 align-middle agendamento-checkbox-${transacaoId}" 
                       type="checkbox"
                       data-agendamento-id="${agendamento.id}" 
                       name="agendamentos_selecionados_${transacaoId}[]"
                       value="${agendamento.id}"
                       aria-label="Selecionar agendamento">
            </td>
            <td class="text-center">${origemDisplay}</td>
            <td class="text-center">${agendamento.data_vencimento || '-'}</td>
            <td class="text-center">${agendamento.pessoa_nome || 'Não informado'}</td>
            <td class="text-center" title="${agendamento.descricao || ''}">${descricaoTruncada}</td>
            <td class="text-center">${categoriasHtml}</td>
            <td class="text-center" title="${valorTitulo}">${valorDisplay}</td>
            <td class="text-center">
                <button type="button" 
                        class="btn btn-icon btn-primary conciliacao-btn" 
                        data-agendamento-id="${agendamento.id}"
                        data-transacao-id="${transacaoId}"
                        title="Conciliar este agendamento"
                        aria-label="Conciliar agendamento">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" 
                         fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
                         stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-check">
                        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                        <path d="M5 12l5 5l10 -10"/>
                    </svg>
                </button>
            </td>
        `;

        return tr;
    }

    /**
     * Prepara dados específicos para exibição na linha
     * @param {Object} agendamento - Dados do agendamento
     * @returns {Object} Dados formatados para a linha
     * @private
     */
    #prepareRowData(agendamento) {
        // Preparar categorias
        const categorias = agendamento.categorias || [];
        const categoriasHtml = categorias.length > 0 
            ? categorias
                .map(cat => `<div class="badge bg-light text-dark mb-1 d-block">${cat}</div>`)
                .join('')
            : '<span class="text-muted">-</span>';

        // Preparar descrição truncada
        const descricaoTruncada = agendamento.descricao && agendamento.descricao.length > 50 
            ? `${agendamento.descricao.substring(0, 50)}...` 
            : agendamento.descricao || 'Sem descrição';

        // Determinar origem
        const origemDisplay = agendamento.faturamento_codigo || agendamento.origem || 'Sistema';

        // Sistema de exibição de valor restante
        let valorDisplay = agendamento.valor_formatado || 'R$ 0,00';
        let valorTitulo = `Valor Total: ${agendamento.valor_formatado || 'R$ 0,00'}`;
        
        if (agendamento.conciliacao_parcial) {
            const percentual = agendamento.percentual_conciliado?.toFixed(1) || '0.0';
            valorDisplay = `
                <div class="d-flex flex-column align-items-center">
                    <span class="text-warning fw-bold">${agendamento.valor_restante_formatado}</span>
                    <small class="text-muted">Restante (${percentual}% pago)</small>
                </div>
            `;
            valorTitulo = [
                `Valor Total: ${agendamento.valor_formatado}`,
                `Já Conciliado: ${agendamento.valor_conciliado_formatado}`,
                `Restante: ${agendamento.valor_restante_formatado}`
            ].join(' | ');
        }

        return {
            categoriasHtml,
            descricaoTruncada,
            origemDisplay,
            valorDisplay,
            valorTitulo
        };
    }

    /**
     * Configura eventos da tabela (checkboxes, etc.)
     * @param {string} transacaoId - ID da transação
     * @private
     */
    #setupTableEvents(transacaoId) {
        // Integrar com sistema existente se disponível
        if (window.conciliacaoOfxBuscarExistente?.configurarEventosCheckbox) {
            window.conciliacaoOfxBuscarExistente.configurarEventosCheckbox(transacaoId);
        }
    }

    /**
     * Manipula clique em conciliação individual
     * @param {string} agendamentoId - ID do agendamento
     * @param {string} transacaoId - ID da transação
     * @private
     */
    #processarConciliacao(agendamentoId, transacaoId) {
        // Integrar com sistema de conciliação existente
        if (window.conciliacaoOfxBuscarExistente?.executarConciliacaoIndividual) {
            window.conciliacaoOfxBuscarExistente.executarConciliacaoIndividual(agendamentoId, transacaoId);
        } else {
            console.warn('⚠️ Sistema de conciliação não disponível');
        }
    }

    /**
     * Mostra loading
     * @param {string} transacaoId - ID da transação
     * @private
     */
    #exibirCarregando(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarLoading) {
            window.conciliacaoOfxBuscarExistente.mostrarLoading(transacaoId);
        }
    }

    /**
     * Mostra estado de erro
     * @param {string} transacaoId - ID da transação
     * @private
     */
    #showError(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarEstadoErro) {
            window.conciliacaoOfxBuscarExistente.mostrarEstadoErro(transacaoId);
        }
    }

    /**
     * Mostra estado vazio
     * @param {string} transacaoId - ID da transação
     * @private
     */
    #showEmptyState(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarEstadoVazio) {
            window.conciliacaoOfxBuscarExistente.mostrarEstadoVazio(transacaoId);
        }
    }

    /**
     * Mostra tabela
     * @param {string} transacaoId - ID da transação
     * @private
     */
    #showTable(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarTabela) {
            window.conciliacaoOfxBuscarExistente.mostrarTabela(transacaoId);
        }
    }

    /**
     * Atualiza informações da tabela
     * @param {string} transacaoId - ID da transação
     * @param {number} count - Quantidade de agendamentos
     * @private
     */
    #updateInfo(transacaoId, count) {
        if (window.conciliacaoOfxBuscarExistente?.atualizarInfoAgendamentos) {
            window.conciliacaoOfxBuscarExistente.atualizarInfoAgendamentos(transacaoId, count);
        }
    }

    /**
     * Mostra toast de sucesso
     * @param {number} count - Quantidade de agendamentos encontrados
     * @private
     */
    #showSuccessToast(count) {
        const message = `${count} agendamento${count !== 1 ? 's' : ''} encontrado${count !== 1 ? 's' : ''}`;
        
        if (typeof mostrarToast === 'function') {
            mostrarToast('success', message);
        } else {
            console.log(`✅ ${message}`);
        }
    }

    /**
     * Mostra toast de erro
     * @param {string} message - Mensagem de erro
     * @private
     */
    #showErrorToast(message) {
        const errorMessage = `Erro ao buscar agendamentos: ${message}`;
        
        if (typeof mostrarToast === 'function') {
            mostrarToast('error', errorMessage);
        } else {
            console.error(`❌ ${errorMessage}`);
        }
    }

    /**
     * Limpa filtros de uma transação específica
     * @param {string} transacaoId - ID da transação
     * @public
     */
    clearFilters(transacaoId) {
        const filterElements = [
            this.seletores.filtros.valorMin(transacaoId),
            this.seletores.filtros.valorMax(transacaoId),
            this.seletores.filtros.dataInicio(transacaoId),
            this.seletores.filtros.dataFim(transacaoId),
            this.seletores.filtros.categoria(transacaoId),
            this.seletores.filtros.beneficiario(transacaoId),
            this.seletores.filtros.descricao(transacaoId)
        ];

        filterElements.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.value = '';
                // Trigger change event para Tom Select
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        console.log(`🧹 Filtros limpos para transação ${transacaoId}`);
    }

    /**
     * Obtém filtros atuais de uma transação
     * @param {string} transacaoId - ID da transação
     * @returns {Object} Filtros atuais
     * @public
     */
    getCurrentFilters(transacaoId) {
        return this.#coletarFiltros(transacaoId);
    }
}

// ============================================================================
// INICIALIZAÇÃO E EXPORTAÇÃO
// ============================================================================

// Inicialização automática
let conciliacaoOfxFiltros;

function inicializarConciliacaoOfxFiltros() {
    try {
        conciliacaoOfxFiltros = new ConciliacaoOfxFiltros();
        window.conciliacaoOfxFiltros = conciliacaoOfxFiltros;
    } catch (error) {
        console.error('❌ Erro ao inicializar sistema de filtros:', error);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarConciliacaoOfxFiltros);
} else {
    // DOM já carregado
    inicializarConciliacaoOfxFiltros();
}