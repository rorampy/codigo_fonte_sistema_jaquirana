
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

    #inicializar() {
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.#configurarEventos();
            });
        } else {
            
            this.#configurarEventos();
        }
    }

    #configurarEventos() {
        
        document.addEventListener('click', (event) => {
            
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
            
            const btnConciliacao = event.target.closest('.btn.conciliacao-btn[data-agendamento-id]');
            if (btnConciliacao) {
                event.preventDefault();
                const agendamentoId = btnConciliacao.dataset.agendamentoId;
                const transacaoId = btnConciliacao.dataset.transacaoId;
                
                if (agendamentoId && transacaoId) {
                    this.#processarConciliacao(agendamentoId, transacaoId);
                }
            }
        }, true); 
    }

    async buscarAgendamentos(transacaoId) {
        try {
            
            this.#exibirCarregando(transacaoId);
            
            const filtros = this.#coletarFiltros(transacaoId);
            
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

    #coletarFiltros(transacaoId) {
        const btnBuscar = document.querySelector(this.seletores.btnBuscar(transacaoId));
        
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

    #converterMoedaParaFloat(valorString) {
        if (!valorString?.trim()) return null;
        
        const cleanValue = valorString
            .replace(/R\$\s?/g, '')
            .replace(/\./g, '')
            .replace(',', '.')
            .trim();
        
        const parsedValue = parseFloat(cleanValue);
        return isNaN(parsedValue) ? null : parsedValue;
    }

    async #renderResults(transacaoId, agendamentos) {
        const tbody = document.querySelector(this.seletores.tabela.tbody(transacaoId));
        
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        if (agendamentos.length === 0) {
            this.#showEmptyState(transacaoId);
            return;
        }

        const fragment = document.createDocumentFragment();
        
        agendamentos.forEach((agendamento) => {
            const row = this.#createAgendamentoRow(agendamento, transacaoId);
            fragment.appendChild(row);
        });

        tbody.appendChild(fragment);

        this.#setupTableEvents(transacaoId);
        this.#showTable(transacaoId);
        this.#updateInfo(transacaoId, agendamentos.length);
    }

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

    #prepareRowData(agendamento) {
        
        const categorias = agendamento.categorias || [];
        const categoriasHtml = categorias.length > 0 
            ? categorias
                .map(cat => `<div class="badge bg-light text-dark mb-1 d-block">${cat}</div>`)
                .join('')
            : '<span class="text-muted">-</span>';

        const descricaoTruncada = agendamento.descricao && agendamento.descricao.length > 50 
            ? `${agendamento.descricao.substring(0, 50)}...` 
            : agendamento.descricao || 'Sem descrição';

        const origemDisplay = agendamento.faturamento_codigo || agendamento.origem || 'Sistema';

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

    #setupTableEvents(transacaoId) {
        
        if (window.conciliacaoOfxBuscarExistente?.configurarEventosCheckbox) {
            window.conciliacaoOfxBuscarExistente.configurarEventosCheckbox(transacaoId);
        }
    }

    #processarConciliacao(agendamentoId, transacaoId) {
        
        if (window.conciliacaoOfxBuscarExistente?.executarConciliacaoIndividual) {
            window.conciliacaoOfxBuscarExistente.executarConciliacaoIndividual(agendamentoId, transacaoId);
        } else {
            console.warn('⚠️ Sistema de conciliação não disponível');
        }
    }

    #exibirCarregando(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarLoading) {
            window.conciliacaoOfxBuscarExistente.mostrarLoading(transacaoId);
        }
    }

    #showError(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarEstadoErro) {
            window.conciliacaoOfxBuscarExistente.mostrarEstadoErro(transacaoId);
        }
    }

    #showEmptyState(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarEstadoVazio) {
            window.conciliacaoOfxBuscarExistente.mostrarEstadoVazio(transacaoId);
        }
    }

    #showTable(transacaoId) {
        if (window.conciliacaoOfxBuscarExistente?.mostrarTabela) {
            window.conciliacaoOfxBuscarExistente.mostrarTabela(transacaoId);
        }
    }

    #updateInfo(transacaoId, count) {
        if (window.conciliacaoOfxBuscarExistente?.atualizarInfoAgendamentos) {
            window.conciliacaoOfxBuscarExistente.atualizarInfoAgendamentos(transacaoId, count);
        }
    }

    #showSuccessToast(count) {
        const message = `${count} agendamento${count !== 1 ? 's' : ''} encontrado${count !== 1 ? 's' : ''}`;
        
        if (typeof mostrarToast === 'function') {
            mostrarToast('success', message);
        } else {
        }
    }

    #showErrorToast(message) {
        const errorMessage = `Erro ao buscar agendamentos: ${message}`;
        
        if (typeof mostrarToast === 'function') {
            mostrarToast('error', errorMessage);
        } else {
            console.error(`❌ ${errorMessage}`);
        }
    }

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
                
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

    }

    getCurrentFilters(transacaoId) {
        return this.#coletarFiltros(transacaoId);
    }
}

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
    
    inicializarConciliacaoOfxFiltros();
}