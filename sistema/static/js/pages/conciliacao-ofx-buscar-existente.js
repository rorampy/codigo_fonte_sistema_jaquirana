// ============================================================================
// SISTEMA DE CONCILIAÇÃO OFX - BUSCAR AGENDAMENTOS EXISTENTES
// ============================================================================
// 
// FUNCIONALIDADES IMPLEMENTADAS:
// 
// 1. BUSCA INTELIGENTE DE AGENDAMENTOS
//    - Filtragem automática por tipo (receitas/despesas)
//    - Busca por valor, data, categoria e beneficiário
//    - Paginação e carregamento otimizado
// 
// 2. EXIBIÇÃO DE VALOR RESTANTE (NOVA FUNCIONALIDADE)
//    - Agendamentos normais: Mostra valor total
//    - Agendamentos parcialmente conciliados: Mostra valor restante em destaque
//    - Tooltip com informações completas (total, pago, restante)
//    - Indicador visual de percentual já pago
// 
// 3. CONCILIAÇÃO INDIVIDUAL INTELIGENTE
//    - Detecta automaticamente se agendamento excede valor da transação
//    - Concilia automaticamente valor disponível (pagamento parcial)
//    - Permite múltiplas conciliações até completar o pagamento
//    - Integração com sistema de sugestões existente
// 
// 4. CONCILIAÇÃO EM MASSA COM DISTRIBUIÇÃO PROPORCIONAL
//    - Seleção múltipla de agendamentos
//    - Cálculo automático de proporção quando valor excede transação
//    - Distribuição justa entre todos os agendamentos selecionados
//    - Modal de confirmação com preview detalhado
// 
// 5. CONTROLE DE ESTADO E INTERFACE
//    - Checkbox "Selecionar Todos" inteligente
//    - Contador dinâmico de selecionados
//    - Estados visuais para carregamento, vazio e erro
//    - Integração com sistema de toasts
// 
// 6. COMPATIBILIDADE E INTEGRAÇÃO
//    - Compatível com sistema de sugestões existente
//    - Eventos customizados para comunicação entre componentes
//    - Fallback para conciliação direta quando necessário
//    - Reutilização de modais e componentes existentes
// 
// ARQUITETURA:
// - Classe principal: ConciliacaoOfxBuscarExistente
// - Métodos de configuração: configurar eventos, checkboxes, conciliação
// - Métodos de busca: carregarAgendamentos, extrairDados*
// - Métodos de conciliação: executar*, processar*, abrir*
// - Métodos de interface: mostrar*, ocultar*, atualizar*
// 
// PRINCIPAIS MELHORIAS IMPLEMENTADAS:
// - Sistema de pagamento automático inteligente
// - Exibição visual de valores restantes
// - Distribuição proporcional em massa
// - Controle preciso de valores utilizados
// - Interface responsiva e intuitiva
// 
// ============================================================================

// Sistema de Buscar Existente para Conciliação OFX
class ConciliacaoOfxBuscarExistente {
    constructor() {
        this.inicializar();
    }

    // Inicializa os eventos e configurações
    inicializar() {
        this.configurarEventos();
        this.configurarEventosCheckbox();
        this.configurarEventosConciliacao();
        this.configurarEventosAjax();
    }

    // Carrega agendamentos via AJAX para uma transação específica
    async carregarAgendamentos(transacaoId) {
        // Evitar chamadas duplas
        if (this.carregandoAgendamentos && this.carregandoAgendamentos.has(transacaoId)) {
            return;
        }
        
        if (!this.carregandoAgendamentos) {
            this.carregandoAgendamentos = new Set();
        }
        this.carregandoAgendamentos.add(transacaoId);
        
        try {
            // Mostrar loading
            this.mostrarLoading(transacaoId);
            
            // Determinar tipo de transação (crédito ou débito) baseado no valor
            const isCredit = this.determinarTipoTransacao(transacaoId);
            
            // Fazer requisição AJAX com o tipo correto
            const response = await fetch('/api/buscar-agendamentos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    is_credit: isCredit ? 'true' : 'false',
                    conta_bancaria_id: window.contaBancariaId, // Enviando o conta_bancaria_id
                    valor_min: null,
                    valor_max: null,
                    data_inicio: null,
                    data_fim: null,
                    categoria: null,
                    beneficiario_id: null
                })
            });

            if (!response.ok) {
                throw new Error(`Erro na requisição: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success && data.agendamentos) {
                // Tentar chamar os métodos com proteção individual
                try {
                    const tbody = document.getElementById(`tbody-agendamentos-${transacaoId}`);
                    if (!tbody) {
                        console.error('Tbody não encontrado para transação:', transacaoId);
                        return;
                    }

                    // Limpar conteúdo anterior
                    tbody.innerHTML = '';

                    if (data.agendamentos.length === 0) {
                        this.mostrarEstadoVazio(transacaoId);
                        return;
                    }

                    // Criar linhas completas com todas as colunas
                    data.agendamentos.forEach((agendamento, index) => {
                        const tr = document.createElement('tr');
                        tr.dataset.agendamentoId = agendamento.id;
                        
                        // Preparar dados para exibição
                        const categorias = agendamento.categorias || [];
                        const categoriasHtml = categorias.length > 0 
                            ? categorias.map(cat => `<div class="badge bg-light text-dark mb-1 d-block">${cat}</div>`).join('')
                            : '<span class="text-muted">-</span>';

                        const descricaoTruncada = agendamento.descricao && agendamento.descricao.length > 50 
                            ? agendamento.descricao.substring(0, 50) + '...' 
                            : agendamento.descricao || 'Sem descrição';

                        // Determinar origem - mostrar apenas o código
                        let origemCompleta = agendamento.faturamento_codigo || agendamento.origem || 'Sistema';

                        // ================================================================
                        // SISTEMA DE EXIBIÇÃO DE VALOR RESTANTE INTELIGENTE
                        // ================================================================
                        // Esta lógica determina como exibir o valor do agendamento:
                        // - Agendamentos normais: Mostra valor total
                        // - Agendamentos parcialmente conciliados: Mostra valor restante 
                        //   em destaque com informações do percentual já pago
                        // ================================================================
                        
                        let valorDisplay = agendamento.valor_formatado || 'R$ 0,00';
                        let valorTitulo = '';
                        
                        // Verificar se o agendamento possui conciliação parcial
                        if (agendamento.conciliacao_parcial) {
                            // EXIBIÇÃO PARA AGENDAMENTOS PARCIALMENTE CONCILIADOS
                            // Mostra o valor restante em destaque e o percentual já pago
                            const percentual = agendamento.percentual_conciliado ? agendamento.percentual_conciliado.toFixed(1) : '0.0';
                            valorDisplay = `
                                <div class="d-flex flex-column align-items-center">
                                    <span class="text-warning fw-bold">${agendamento.valor_restante_formatado}</span>
                                    <small class="text-muted">Restante (${percentual}% pago)</small>
                                </div>
                            `;
                            // Tooltip com informações completas do pagamento
                            valorTitulo = `Valor Total: ${agendamento.valor_formatado} | Já Conciliado: ${agendamento.valor_conciliado_formatado} | Restante: ${agendamento.valor_restante_formatado}`;
                        } else {
                            // EXIBIÇÃO PARA AGENDAMENTOS NORMAIS
                            // Mostra apenas o valor total
                            valorTitulo = `Valor Total: ${agendamento.valor_formatado}`;
                        }

                        tr.innerHTML = `
                            <td>
                                <input class="form-check-input m-0 align-middle agendamento-checkbox-${transacaoId}" 
                                       type="checkbox"
                                       data-agendamento-id="${agendamento.id}" 
                                       name="agendamentos_selecionados_${transacaoId}[]"
                                       value="${agendamento.id}">
                            </td>
                            <td style="text-align: center;">${origemCompleta}</td>
                            <td style="text-align: center;">${agendamento.data_vencimento || '-'}</td>
                            <td style="text-align: center;">${agendamento.pessoa_nome || 'Não informado'}</td>
                            <td style="text-align: center;" title="${agendamento.descricao || ''}">${descricaoTruncada}</td>
                            <td style="text-align: center;">${categoriasHtml}</td>
                            <td style="text-align: center;" title="${valorTitulo}">${valorDisplay}</td>
                            <td style="text-align: center;">
                                <button type="button" class="btn btn-icon btn-primary conciliacao-btn" 
                                        onclick="window.conciliacaoOfxBuscarExistente.executarConciliacaoIndividual('${agendamento.id}', '${transacaoId}')"
                                        title="Conciliar este agendamento">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                                         class="icon icon-tabler icons-tabler-outline icon-tabler-check">
                                        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                                        <path d="M5 12l5 5l10 -10"/>
                                    </svg>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });

                    // Configurar eventos para checkboxes
                    this.configurarEventosCheckbox(transacaoId);

                    this.mostrarTabela(transacaoId);
                    
                } catch (error) {
                    console.error('Erro em preencherTabelaAgendamentos:', error);
                }
                
                try {
                    this.atualizarInfoAgendamentos(transacaoId, data.agendamentos.length);
                } catch (error) {
                    console.error('Erro em atualizarInfoAgendamentos:', error);
                }
            } else {
                throw new Error(data.error || data.message || 'Erro desconhecido');
            }

        } catch (error) {
            console.error('Erro ao carregar agendamentos:', error);
            this.mostrarEstadoErro(transacaoId);
            
            // Mostrar toast de erro
            if (typeof mostrarToast === 'function') {
                mostrarToast('error', 'Erro ao carregar agendamentos: ' + error.message);
            }
        } finally {
            // Remover da lista de carregamento
            if (this.carregandoAgendamentos) {
                this.carregandoAgendamentos.delete(transacaoId);
            }
        }
    }

    // Determina se a transação é crédito ou débito baseado no valor
    determinarTipoTransacao(transacaoId) {
        // Buscar o card da transação para pegar o valor original
        const cardTransacao = document.querySelector(`.conciliacao-ofx-id-${transacaoId} .card[data-transacao-id="${transacaoId}"]`);
        
        if (!cardTransacao) {
            // Transação não encontrada - retornar valor padrão
            return false; // Default para débito se não encontrar
        }

        // Usar o valor original (com sinal) direto do banco de dados
        const valorOriginal = parseFloat(cardTransacao.dataset.transacaoValorOriginal) || 0;
        
        // Positivo = Crédito (receita), Negativo = Débito (despesa)
        const isCredit = valorOriginal > 0;
        
        // Determinar tipo de transação baseado no valor para buscar agendamentos corretos
        // Transações positivas = créditos (receitas) | Transações negativas = débitos (despesas)
        
        return isCredit;
    }

    // Converte valor formatado (R$ 1.234,56) para número
    converterValorParaNumero(valorFormatado) {
        if (!valorFormatado || typeof valorFormatado !== 'string') {
            return 0;
        }
        
        // Remover símbolos e espaços, trocar vírgula por ponto
        const valorLimpo = valorFormatado
            .replace(/R\$\s?/g, '')
            .replace(/\./g, '')
            .replace(',', '.')
            .trim();
        
        return parseFloat(valorLimpo) || 0;
    }

    // Mostra o estado de loading
    mostrarLoading(transacaoId) {
        const loading = document.getElementById(`loading-agendamentos-${transacaoId}`);
        const tabela = document.getElementById(`tabela-agendamentos-${transacaoId}`);
        const estadoVazio = document.getElementById(`estado-vazio-${transacaoId}`);
        const estadoErro = document.getElementById(`estado-erro-${transacaoId}`);
        
        if (loading) {
            loading.classList.remove('d-none');
            loading.style.display = 'flex';
        }
        if (tabela) {
            tabela.classList.add('d-none');
            tabela.style.display = 'none';
        }
        if (estadoVazio) {
            estadoVazio.classList.add('d-none');
            estadoVazio.style.display = 'none';
        }
        if (estadoErro) {
            estadoErro.classList.add('d-none');
            estadoErro.style.display = 'none';
        }
    }

    // Mostra o estado de erro
    mostrarEstadoErro(transacaoId) {
        const loading = document.getElementById(`loading-agendamentos-${transacaoId}`);
        const tabela = document.getElementById(`tabela-agendamentos-${transacaoId}`);
        const estadoVazio = document.getElementById(`estado-vazio-${transacaoId}`);
        const estadoErro = document.getElementById(`estado-erro-${transacaoId}`);
        
        if (loading) loading.classList.add('d-none');
        if (tabela) tabela.classList.add('d-none');
        if (estadoVazio) estadoVazio.classList.add('d-none');
        if (estadoErro) estadoErro.classList.remove('d-none');
    }

    // Mostra o estado vazio
    mostrarEstadoVazio(transacaoId) {
        const loading = document.getElementById(`loading-agendamentos-${transacaoId}`);
        const tabela = document.getElementById(`tabela-agendamentos-${transacaoId}`);
        const estadoVazio = document.getElementById(`estado-vazio-${transacaoId}`);
        const estadoErro = document.getElementById(`estado-erro-${transacaoId}`);
        
        if (loading) loading.classList.add('d-none');
        if (tabela) tabela.classList.add('d-none');
        if (estadoVazio) estadoVazio.classList.remove('d-none');
        if (estadoErro) estadoErro.classList.add('d-none');
    }

    // Mostra a tabela com dados
    mostrarTabela(transacaoId) {
        const loading = document.getElementById(`loading-agendamentos-${transacaoId}`);
        const tabela = document.getElementById(`tabela-agendamentos-${transacaoId}`);
        const estadoVazio = document.getElementById(`estado-vazio-${transacaoId}`);
        const estadoErro = document.getElementById(`estado-erro-${transacaoId}`);
        
        // Forçar ocultar loading
        if (loading) {
            loading.classList.add('d-none');
            loading.style.display = 'none';
        }
        
        // Forçar mostrar tabela
        if (tabela) {
            tabela.classList.remove('d-none');
            tabela.style.display = 'block';
        }
        
        // Ocultar outros estados
        if (estadoVazio) {
            estadoVazio.classList.add('d-none');
            estadoVazio.style.display = 'none';
        }
        if (estadoErro) {
            estadoErro.classList.add('d-none');
            estadoErro.style.display = 'none';
        }
    }

    // Cria uma linha da tabela para um agendamento
    criarLinhaAgendamento(transacaoId, agendamento) {
        const tr = document.createElement('tr');
        tr.dataset.agendamentoId = agendamento.id;
        
        // Truncar descrição se necessário
        const descricaoTruncada = agendamento.descricao.length > 50 
            ? agendamento.descricao.substring(0, 50) + '...' 
            : agendamento.descricao;
        
        // Criar badges de categorias
        let categoriasHtml = '';
        if (agendamento.categorias && agendamento.categorias.length > 0) {
            categoriasHtml = '<div class="d-flex flex-column">';
            agendamento.categorias.forEach(categoria => {
                categoriasHtml += `<span class="badge bg-light text-dark mb-1">${categoria}</span>`;
            });
            categoriasHtml += '</div>';
        } else {
            categoriasHtml = '<span class="text-muted">-</span>';
        }

        tr.innerHTML = `
            <td>
                <input class="form-check-input m-0 align-middle agendamento-checkbox-${transacaoId}" 
                       type="checkbox" 
                       data-agendamento-id="${agendamento.id}" 
                       aria-label="Selecionar agendamento"
                       name="agendamentos_selecionados_${transacaoId}[]"
                       value="${agendamento.id}">
            </td>
            <td style="text-align: center;">
                <div class="d-flex align-items-center justify-content-center">
                    <span class="badge bg-light text-light-fg">${agendamento.faturamento_codigo || 'ID: ' + agendamento.id}</span>
                </div>
            </td>
            <td style="text-align: center;">
                <div>
                    <div>${agendamento.data_vencimento}</div>
                </div>
            </td>
            <td style="text-align: center;">
                <span class="text-reset">${agendamento.pessoa_nome}</span>
            </td>
            <td style="text-align: center;">
                <span title="${agendamento.descricao}">${descricaoTruncada}</span>
            </td>
            <td style="text-align: center;">
                ${categoriasHtml}
            </td>
            <td style="text-align: center;">
                <div class="fw-bold">${agendamento.valor_formatado}</div>
                ${agendamento.conciliacao_parcial ? `
                    <div class="text-xs text-warning">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-coin">
                            <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                            <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"/>
                            <path d="M14.8 9a2 2 0 0 0 -1.8 -1h-2a2 2 0 1 0 0 4h2a2 2 0 1 1 0 4h-2a2 2 0 0 1 -1.8 -1"/>
                            <path d="M12 7v10"/>
                        </svg>
                        Parcialmente conciliado
                        <br>
                        Pendente: ${agendamento.valor_pendente_formatado || 'R$ 0,00'}
                    </div>
                ` : ''}
            </td>
            <td>
                <button type="button" 
                        class="btn btn-icon btn-primary conciliacao-btn conciliar-individual-${transacaoId}" 
                        data-agendamento-id="${agendamento.id}" 
                        data-transacao-id="${transacaoId}"
                        title="Conciliar este agendamento">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                         class="icon icon-tabler icons-tabler-outline icon-tabler-checks">
                        <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                        <path d="M7 12l5 5l10 -10" />
                        <path d="M2 12l5 5m5 -5l5 -5" />
                    </svg>
                </button>
                <button type="button" 
                        class="btn btn-icon btn-success conciliacao-btn ms-1 btn-conciliar-parcial" 
                        data-agendamento-id="${agendamento.id}" 
                        data-transacao-id="${transacaoId}"
                        data-agendamento-valor="${agendamento.valor_total_100}"
                        data-agendamento-valor-conciliado="${agendamento.valor_conciliado_100 || 0}"
                        title="Conciliação parcial">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                         class="icon icon-tabler icons-tabler-outline icon-tabler-coin">
                        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                        <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"/>
                        <path d="M14.8 9a2 2 0 0 0 -1.8 -1h-2a2 2 0 1 0 0 4h2a2 2 0 1 1 0 4h-2a2 2 0 0 1 -1.8 -1"/>
                        <path d="M12 7v10"/>
                    </svg>
                </button>
            </td>
        `;

        return tr;
    }

    // Atualiza as informações de quantidade de agendamentos
    atualizarInfoAgendamentos(transacaoId, quantidade) {
        const infoElement = document.getElementById(`info-agendamentos-${transacaoId}`);
        if (infoElement) {
            if (quantidade > 0) {
                infoElement.textContent = `Mostrando ${quantidade} agendamentos recentes`;
            } else {
                infoElement.textContent = 'Nenhum agendamento encontrado';
            }
        }
    }

    // Configura eventos AJAX para buscar agendamentos
    configurarEventosAjax() {
        // Escuta eventos de conciliação para atualizar listas
        document.addEventListener('conciliacao-realizada', (event) => {
            const { agendamentoId } = event.detail;
            if (agendamentoId) {
                this.removerAgendamentoDaLista(agendamentoId);
            }
        });
    }

    // Configura os eventos de clique nas abas
    configurarEventos() {
        // Escutar cliques em todas as abas de "Buscar Existente"
        document.addEventListener('click', (event) => {
            const link = event.target.closest('a[href*="tabs-buscar-existente"]');
            if (link) {
                this.aoClicarBuscarExistente(event, link);
            }
        });

        // Escutar quando a aba é ativada pelo Bootstrap
        document.addEventListener('shown.bs.tab', (event) => {
            if (event.target.href && event.target.href.includes('tabs-buscar-existente')) {
                this.aoAtivarAbaBuscarExistente(event);
            } else {
                // Se mudou para aba que não é "Buscar Existente", ocultar tabelas
                this.aoMudarParaOutraAba(event);
            }
        });
    }

    // Manipula o clique na aba "Buscar Existente"
    aoClicarBuscarExistente(event, link) {
        const href = link.getAttribute('href');
        const transacaoId = this.extrairTransacaoId(href);
        
        // Mostrar a tabela (que irá carregar dados via AJAX automaticamente)
        this.mostrarTabelaBuscarExistente(transacaoId);
    }

    // Manipula a ativação da aba "Buscar Existente"
    aoAtivarAbaBuscarExistente(event) {
        const href = event.target.href;
        const transacaoId = this.extrairTransacaoId(href);
        
        // Garantir que a tabela está visível (que irá carregar dados via AJAX automaticamente)
        this.mostrarTabelaBuscarExistente(transacaoId);
    }

    // Mostra loading na tabela
    mostrarLoadingTabela(transacaoId) {
        const tbody = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId} tbody`);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Carregando...</span>
                        </div>
                        <p class="mt-2 mb-0 text-muted">Buscando agendamentos...</p>
                    </td>
                </tr>
            `;
        }
    }

    // Preenche a tabela com os agendamentos recebidos
    preencherTabelaAgendamentos(transacaoId, agendamentos) {
        const tbody = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId} tbody`);
        if (!tbody) return;

        if (agendamentos.length === 0) {
            this.mostrarMensagemVazia(transacaoId);
            return;
        }

        let html = '';
        agendamentos.forEach(agendamento => {
            html += this.criarLinhaAgendamento(transacaoId, agendamento);
        });

        tbody.innerHTML = html;

        // Atualizar contador no footer
        this.atualizarContadorAgendamentos(transacaoId, agendamentos.length);
    }

    // Mostra mensagem quando não há agendamentos
    mostrarMensagemVazia(transacaoId, mensagem = 'Nenhum agendamento recente encontrado para este tipo de movimentação') {
        const tbody = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId} tbody`);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                             class="icon icon-tabler icons-tabler-outline icon-tabler-search-off mb-2">
                            <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                            <path d="M3 3l18 18" />
                            <path d="M10 10m-7 0a7 7 0 1 0 14 0a7 7 0 1 0 -14 0" />
                            <path d="M21 21l-6 -6" />
                        </svg>
                        <p class="mb-0">${mensagem}</p>
                    </td>
                </tr>
            `;
        }
        this.atualizarContadorAgendamentos(transacaoId, 0);
    }

    // Mostra mensagem de erro
    mostrarMensagemErro(transacaoId) {
        const tbody = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId} tbody`);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger py-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
                             class="icon icon-tabler icons-tabler-outline icon-tabler-alert-circle mb-2">
                            <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                            <path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" />
                            <path d="M12 8v4" />
                            <path d="M12 16h.01" />
                        </svg>
                        <p class="mb-0">Erro ao carregar agendamentos. Tente novamente.</p>
                        <button type="button" class="btn btn-sm btn-outline-primary mt-2" 
                                onclick="window.conciliacaoOfxBuscarExistente.carregarAgendamentos('${transacaoId}')">
                            Tentar Novamente
                        </button>
                    </td>
                </tr>
            `;
        }
    }

    // Atualiza contador de agendamentos no footer
    atualizarContadorAgendamentos(transacaoId, quantidade) {
        const footerText = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId} .card-footer p`);
        if (footerText) {
            if (quantidade > 0) {
                footerText.innerHTML = `Mostrando <span>${quantidade}</span> agendamentos recentes`;
            } else {
                footerText.innerHTML = 'Nenhum agendamento encontrado';
            }
        }
    }

    // Remove agendamento da lista após conciliação
    removerAgendamentoDaLista(agendamentoId) {
        const linha = document.querySelector(`tr[data-agendamento-id="${agendamentoId}"]`);
        if (linha) {
            // Animação de fade out
            linha.style.transition = 'opacity 0.3s ease-out';
            linha.style.opacity = '0';
            
            setTimeout(() => {
                linha.remove();
                
                // Atualizar contadores após remoção
                this.atualizarContadoresAposRemocao();
            }, 300);
        }
    }

    // Atualiza todos os contadores após remoção de agendamento
    atualizarContadoresAposRemocao() {
        // Buscar todas as tabelas de buscar existente visíveis
        const tabelasVisiveis = document.querySelectorAll('[class*="conciliacao-ofx-buscar-existente-"]:not(.d-none)');
        
        tabelasVisiveis.forEach(tabela => {
            const match = tabela.className.match(/conciliacao-ofx-buscar-existente-(\d+)/);
            if (match) {
                const transacaoId = match[1];
                const linhasRestantes = tabela.querySelectorAll('tbody tr[data-agendamento-id]').length;
                
                this.atualizarContadorAgendamentos(transacaoId, linhasRestantes);
                this.atualizarContadorSelecionados(transacaoId);
                this.atualizarBotaoConciliacaoMultipla(transacaoId);
                
                // Se não há mais agendamentos, mostrar mensagem vazia
                if (linhasRestantes === 0) {
                    this.mostrarMensagemVazia(transacaoId);
                }
            }
        });
    }

    // Extrai o ID da transação do href
    extrairTransacaoId(href) {
        const match = href.match(/tabs-buscar-existente-(\d+)/);
        return match ? match[1] : null;
    }

    // Mostra a tabela de buscar existente para uma transação específica
    mostrarTabelaBuscarExistente(transacaoId) {
        // Primeiro, ocultar todas as outras tabelas de buscar existente
        this.ocultarTodasTabelasBuscarExistente();
        
        // Encontrar e mostrar a tabela correspondente à transação
        const tabelaContainer = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId}`);
        
        if (tabelaContainer) {
            tabelaContainer.classList.remove('d-none');
            
            // Adicionar animação suave
            tabelaContainer.style.opacity = '0';
            setTimeout(() => {
                tabelaContainer.style.transition = 'opacity 0.3s ease-in-out';
                tabelaContainer.style.opacity = '1';
            }, 50);

            // Carregar dados via AJAX se ainda não foram carregados
            const tbody = document.getElementById(`tbody-agendamentos-${transacaoId}`);
            if (tbody && tbody.children.length === 0) {
                this.carregarAgendamentos(transacaoId);
            }
        }
    }

    // Oculta todas as tabelas de buscar existente
    ocultarTodasTabelasBuscarExistente() {
        const todasTabelas = document.querySelectorAll('[class*="conciliacao-ofx-buscar-existente"]');
        todasTabelas.forEach(tabela => {
            tabela.classList.add('d-none');
        });
    }

    // Oculta a tabela de buscar existente para uma transação específica
    ocultarTabelaBuscarExistente(transacaoId) {
        const tabelaContainer = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId}`);
        
        if (tabelaContainer) {
            // Adicionar animação suave antes de ocultar
            tabelaContainer.style.transition = 'opacity 0.3s ease-in-out';
            tabelaContainer.style.opacity = '0';
            
            setTimeout(() => {
                tabelaContainer.classList.add('d-none');
                tabelaContainer.style.opacity = '1'; // Reset para próxima exibição
            }, 300);
        }
    }

    // Manipula a mudança para outras abas (Sugestão ou Nova Transação)
    aoMudarParaOutraAba(event) {
        const href = event.target.href;
        let transacaoId = null;
        
        // Extrair ID da transação baseado no tipo de aba
        if (href && href.includes('tabs-sugestao-')) {
            transacaoId = href.match(/tabs-sugestao-(\d+)/)?.[1];
        } else if (href && href.includes('tabs-nova-transacao-')) {
            transacaoId = href.match(/tabs-nova-transacao-(\d+)/)?.[1];
        }
        
        if (transacaoId) {
            this.ocultarTabelaBuscarExistente(transacaoId);
        }
    }

    // Configura os eventos dos checkboxes
    configurarEventosCheckbox() {
        document.addEventListener('change', (event) => {
            // Checkbox individual de agendamento
            if (event.target.matches('input[name*="agendamentos_selecionados"]')) {
                this.aoMudarCheckboxAgendamento(event.target);
            }
            
            // Checkbox "Selecionar Todos"
            if (event.target.matches('input[id*="selecionar-todos-"]')) {
                this.aoClicarSelecionarTodos(event.target);
            }
        });
    }

    // Configura os eventos de conciliação
    configurarEventosConciliacao() {
        document.addEventListener('click', (event) => {
            // Botão de conciliação individual
            if (event.target.closest('.btn-conciliar-individual')) {
                this.aoConciliarIndividual(event.target.closest('.btn-conciliar-individual'));
            }
            
            // Botão de conciliação parcial
            if (event.target.closest('.btn-conciliar-parcial')) {
                this.abrirModalConciliacaoParcial(event.target.closest('.btn-conciliar-parcial'));
            }
            
            // Botão de conciliação múltipla
            if (event.target.closest('[class*="conciliar-multiplos-"]')) {
                this.aoConciliarMultiplos(event.target.closest('[class*="conciliar-multiplos-"]'));
            }
        });
    }

    // Manipula a mudança de um checkbox de agendamento
    aoMudarCheckboxAgendamento(checkbox) {
        const transacaoId = this.extrairTransacaoIdDoCheckbox(checkbox);
        if (transacaoId) {
            this.atualizarContadorSelecionados(transacaoId);
            this.atualizarBotaoConciliacaoMultipla(transacaoId);
            this.atualizarCheckboxSelecionarTodos(transacaoId);
        }
    }

    // Manipula o clique no checkbox "Selecionar Todos"
    aoClicarSelecionarTodos(checkbox) {
        const transacaoId = checkbox.id.replace('selecionar-todos-', '');
        const checkboxesAgendamentos = document.querySelectorAll(`input[name="agendamentos_selecionados_${transacaoId}[]"]`);
        
        checkboxesAgendamentos.forEach(cb => {
            cb.checked = checkbox.checked;
        });

        this.atualizarContadorSelecionados(transacaoId);
        this.atualizarBotaoConciliacaoMultipla(transacaoId);
    }

    // Extrai o ID da transação de um checkbox de agendamento
    extrairTransacaoIdDoCheckbox(checkbox) {
        const name = checkbox.getAttribute('name');
        const match = name ? name.match(/agendamentos_selecionados_(\d+)\[\]/) : null;
        return match ? match[1] : null;
    }

    // Atualiza o contador de agendamentos selecionados
    atualizarContadorSelecionados(transacaoId) {
        const checkboxesMarcados = document.querySelectorAll(`input[name="agendamentos_selecionados_${transacaoId}[]"]:checked`);
        const contador = document.querySelector(`.contador-selecionados-${transacaoId}`);
        const botao = document.querySelector(`.conciliar-multiplos-${transacaoId}`);
        
        if (contador) {
            contador.textContent = checkboxesMarcados.length;
        }
        
        // Atualizar texto do botão se não tiver contador separado
        if (botao && !contador) {
            const count = checkboxesMarcados.length;
            botao.textContent = count > 0 ? `Conciliar Selecionados (${count})` : 'Conciliar Selecionados';
        }
    }

    // Mostra/oculta o botão de conciliação múltipla baseado na seleção
    atualizarBotaoConciliacaoMultipla(transacaoId) {
        const checkboxesMarcados = document.querySelectorAll(`input[name="agendamentos_selecionados_${transacaoId}[]"]:checked`);
        const botao = document.querySelector(`.conciliar-multiplos-${transacaoId}`);
        
        if (botao) {
            if (checkboxesMarcados.length > 0) {
                botao.classList.remove('d-none');
            } else {
                botao.classList.add('d-none');
            }
        }
    }

    // Atualiza o estado do checkbox "Selecionar Todos"
    atualizarCheckboxSelecionarTodos(transacaoId) {
        const checkboxTodos = document.getElementById(`selecionar-todos-${transacaoId}`);
        const checkboxesAgendamentos = document.querySelectorAll(`input[name="agendamentos_selecionados_${transacaoId}[]"]`);
        const checkboxesMarcados = document.querySelectorAll(`input[name="agendamentos_selecionados_${transacaoId}[]"]:checked`);
        
        if (checkboxTodos && checkboxesAgendamentos.length > 0) {
            if (checkboxesMarcados.length === checkboxesAgendamentos.length) {
                checkboxTodos.checked = true;
                checkboxTodos.indeterminate = false;
            } else if (checkboxesMarcados.length > 0) {
                checkboxTodos.checked = false;
                checkboxTodos.indeterminate = true;
            } else {
                checkboxTodos.checked = false;
                checkboxTodos.indeterminate = false;
            }
        }
    }

    // Manipula a conciliação individual de um agendamento
    aoConciliarIndividual(botao) {
        const agendamentoId = botao.dataset.agendamentoId;
        const transacaoId = botao.dataset.transacaoId;
        
        if (!agendamentoId || !transacaoId) {
            console.error('IDs de agendamento ou transação não encontrados');
            return;
        }

        // Usar o sistema de conciliação existente
        this.executarConciliacaoIndividual(agendamentoId, transacaoId);
    }

    // Executa a conciliação individual de um agendamento
    async executarConciliacaoIndividual(agendamentoId, transacaoId) {
        // Verificar se existe o sistema de conciliação de sugestões
        if (window.conciliacaoSugestoes && window.conciliacaoSugestoes.abrirModalConciliacao) {
            try {
                // Criar dados de conciliação compatíveis - preparar os dados que o sistema de sugestões espera
                const dadosTransacao = this.extrairDadosTransacao(transacaoId);
                const dadosAgendamento = this.extrairDadosAgendamento(agendamentoId);

                if (!dadosTransacao || !dadosAgendamento) {
                    throw new Error('Dados da transação ou agendamento não encontrados');
                }

                // Configurar dados para o sistema de sugestões
                window.conciliacaoSugestoes.dadosConciliacao = {
                    transacao_id: transacaoId,
                    agendamento_id: agendamentoId,
                    transacao: dadosTransacao,
                    agendamento: dadosAgendamento
                };

                // Preencher modal e mostrar
                window.conciliacaoSugestoes.preencherModal();
                window.conciliacaoSugestoes.modal.show();

            } catch (error) {
                console.error('Erro ao abrir modal de sugestões:', error);
                // Fallback para conciliação direta
                await this.conciliacaoIndividualDireta(agendamentoId, transacaoId);
            }
        } else {
            // Fallback: implementação direta
            await this.conciliacaoIndividualDireta(agendamentoId, transacaoId);
        }
    }

    // Extrai dados da transação OFX para compatibilidade com sistema de sugestões
    extrairDadosTransacao(transacaoId) {
        // Buscar o card da transação principal - usar a mesma estrutura das sugestões
        let cardTransacao = document.querySelector(`.conciliacao-ofx-id-${transacaoId} .card[data-transacao-id="${transacaoId}"]`);
        
        if (!cardTransacao) {
            console.error(`Card da transação ${transacaoId} não encontrado`);
            // Retornar dados básicos mesmo sem encontrar o card
            return {
                valor: 'R$ 0,00',
                valorOriginal: 'R$ 0,00',
                valorDisponivel: 'R$ 0,00',
                isParcial: false,
                data: new Date().toLocaleDateString('pt-BR'),
                descricao: 'Transação via Buscar Existente',
                fitid: transacaoId
            };
        }

        // Verificar se é conciliação parcial e usar valor disponível
        const isParcial = cardTransacao.dataset.conciliacaoParcial === 'true';
        const valorDisponivel = cardTransacao.dataset.transacaoValorDisponivel || cardTransacao.dataset.transacaoValor || 'R$ 0,00';
        const valorOriginal = cardTransacao.dataset.transacaoValor || 'R$ 0,00';
        
        // Usar valor disponível para transações parciais
        const valor = isParcial ? valorDisponivel : valorOriginal;
        const data = cardTransacao.dataset.transacaoData || '';
        const descricao = cardTransacao.dataset.transacaoDescricao || 'Sem descrição';
        const fitid = cardTransacao.dataset.transacaoFitid || transacaoId;

        return {
            valor: valor,
            valorOriginal: valorOriginal,
            valorDisponivel: valorDisponivel,
            isParcial: isParcial,
            data: data,
            descricao: descricao,
            fitid: fitid
        };
    }

    // Extrai dados do agendamento para o modal de conciliação massa
    extrairDadosAgendamento(agendamentoId) {
        // Buscar linha do agendamento na tabela
        const linhaAgendamento = document.querySelector(`tr[data-agendamento-id="${agendamentoId}"]`);
        if (!linhaAgendamento) {
            console.error(`Linha do agendamento ${agendamentoId} não encontrada`);
            // Retornar dados básicos mesmo sem encontrar a linha
            return {
                id: agendamentoId,
                pessoa_nome: 'Não informado',
                valor_formatado: 'R$ 0,00',
                data_vencimento: new Date().toLocaleDateString('pt-BR'),
                descricao: 'Agendamento via Buscar Existente',
                origem_codigo: agendamentoId,
                categorias: []
            };
        }

        // Extrair dados da linha (baseado na estrutura da tabela)
        const cells = linhaAgendamento.children;
        
        // Dados básicos com fallback
        let origemCodigo = 'Sistema';
        let dataVencimento = new Date().toLocaleDateString('pt-BR');
        let pessoaNome = 'Não informado';
        let descricao = 'Sem descrição';
        let valorFormatado = 'R$ 0,00';
        let categorias = [];

        try {
            // Estrutura: checkbox, origem, data vencimento, beneficiário, descrição, categorias, valor, ação
            if (cells[1]) { // Origem - pode conter badge com código
                const badgeOrigem = cells[1].querySelector('.badge');
                if (badgeOrigem) {
                    origemCodigo = badgeOrigem.textContent.trim();
                } else {
                    origemCodigo = cells[1].textContent.trim() || agendamentoId;
                }
            }

            if (cells[2]) { // Data vencimento
                dataVencimento = cells[2].textContent.trim() || dataVencimento;
            }

            if (cells[3]) { // Beneficiário/Pessoa
                pessoaNome = cells[3].textContent.trim() || pessoaNome;
            }

            if (cells[4]) { // Descrição
                const descElement = cells[4].querySelector('span[title]');
                if (descElement) {
                    descricao = descElement.getAttribute('title') || descElement.textContent.trim();
                } else {
                    descricao = cells[4].textContent.trim() || descricao;
                }
            }

            if (cells[5]) { // Categorias
                const badgesCategorias = cells[5].querySelectorAll('.badge');
                categorias = Array.from(badgesCategorias)
                    .map(badge => badge.textContent.trim())
                    .filter(cat => cat.length > 0 && cat !== '-');
            }

            if (cells[6]) { // Valor
                // Primeiro, pegar o valor formatado padrão
                valorFormatado = cells[6].textContent.trim() || valorFormatado;
                
                // Verificar se há tooltip ou span com valor restante
                const valorElement = cells[6];
                const tooltipElement = valorElement.querySelector('[title*="Restante"]') || 
                                    valorElement.querySelector('[title*="Pendente"]') ||
                                    valorElement.querySelector('[data-bs-title*="Restante"]') ||
                                    valorElement.querySelector('[data-bs-title*="Pendente"]');
                
                if (tooltipElement) {
                    // Se há tooltip, extrair valor restante
                    const tooltipText = tooltipElement.getAttribute('title') || 
                                       tooltipElement.getAttribute('data-bs-title') || '';
                    
                    // Buscar padrão "Restante: R$ X,XX" ou "Pendente: R$ X,XX"
                    const matchRestante = tooltipText.match(/(?:Restante|Pendente):\s*R?\$?\s*([\d.,]+)/i);
                    if (matchRestante) {
                        valorFormatado = `R$ ${matchRestante[1]}`;
                    }
                }
            }

        } catch (error) {
            // Erro ao extrair dados - usar valores padrão
        }

        return {
            id: agendamentoId,
            origem_codigo: origemCodigo,
            data_vencimento: dataVencimento,
            pessoa_nome: pessoaNome,
            descricao: descricao,
            valor_formatado: valorFormatado,
            categorias: categorias,
            
            // Compatibilidade com modal individual (propriedades alternativas)
            valor: valorFormatado,
            vencimento: dataVencimento,
            pessoa: pessoaNome,
            origem: origemCodigo
        };
    }

    // Conciliação individual direta (fallback quando sistema de sugestões não está disponível)
    async conciliacaoIndividualDireta(agendamentoId, transacaoId) {
        if (!confirm('Confirma a conciliação deste agendamento?')) {
            return;
        }

        try {
            const response = await fetch('/api/processar-conciliacao', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agendamento_id: agendamentoId,
                    transacao_id: transacaoId,
                    observacoes: 'Conciliação via buscar existente'
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                // Notificar sucesso
                this.mostrarToastSucesso(resultado.message);
                
                // Recarregar página após 1.5s para atualizar valores
                setTimeout(() => window.location.reload(), 1500);
                return;
            } else {
                this.mostrarToastErro(resultado.message || 'Erro ao processar conciliação');
            }
        } catch (error) {
            console.error('Erro na conciliação:', error);
            this.mostrarToastErro('Erro de conexão. Tente novamente.');
        }
    }

    // Mostra toast de sucesso
    mostrarToastSucesso(mensagem) {
        // Tentar usar o sistema de toast existente
        if (window.conciliacaoSugestoes && window.conciliacaoSugestoes.mostrarToast) {
            window.conciliacaoSugestoes.mostrarToast('sucesso', mensagem);
        } else if (typeof mostrarToast === 'function') {
            mostrarToast('success', mensagem);
        } else {
            // Criar toast próprio
            this.criarToast('success', mensagem);
        }
    }

    // Mostra toast de erro
    mostrarToastErro(mensagem) {
        // Tentar usar o sistema de toast existente
        if (window.conciliacaoSugestoes && window.conciliacaoSugestoes.mostrarToast) {
            window.conciliacaoSugestoes.mostrarToast('erro', mensagem);
        } else if (typeof mostrarToast === 'function') {
            mostrarToast('error', mensagem);
        } else {
            // Criar toast próprio
            this.criarToast('error', mensagem);
        }
    }

    // Aplica efeito visual na transação conciliada (similar às sugestões)
    aplicarEfeitoTransacaoConciliada(transacaoId) {
        // Encontrar o card da transação principal
        const transacaoCard = document.querySelector(`[data-transacao-id="${transacaoId}"], .conciliacao-ofx-id-${transacaoId}`);
        
        if (transacaoCard) {
            // Aplicar efeito de fade-out (igual às sugestões)
            transacaoCard.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            transacaoCard.style.opacity = '0.3';
            transacaoCard.style.transform = 'scale(0.95)';
            
            // Adicionar classe de conciliado
            transacaoCard.classList.add('transacao-conciliada');
            
            // Desabilitar interações
            const botoes = transacaoCard.querySelectorAll('button, a, input');
            botoes.forEach(elemento => {
                elemento.disabled = true;
                elemento.style.pointerEvents = 'none';
            });
            
            // Adicionar marca visual de "conciliado"
            const existingBadge = transacaoCard.querySelector('.badge-conciliado');
            if (!existingBadge) {
                const badge = document.createElement('div');
                badge.className = 'badge badge-success badge-conciliado position-absolute';
                badge.style.top = '10px';
                badge.style.right = '10px';
                badge.style.zIndex = '10';
                badge.innerHTML = '✓ Conciliado';
                
                // Adicionar posição relativa ao card se não tiver
                if (getComputedStyle(transacaoCard).position === 'static') {
                    transacaoCard.style.position = 'relative';
                }
                
                transacaoCard.appendChild(badge);
            }
            
            // Opcional: remover completamente após um tempo
            setTimeout(() => {
                if (transacaoCard && transacaoCard.parentNode) {
                    transacaoCard.style.transition = 'opacity 0.3s ease-out, height 0.3s ease-out, margin 0.3s ease-out';
                    transacaoCard.style.opacity = '0';
                    transacaoCard.style.height = '0';
                    transacaoCard.style.margin = '0';
                    transacaoCard.style.overflow = 'hidden';
                    
                    setTimeout(() => {
                        if (transacaoCard && transacaoCard.parentNode) {
                            transacaoCard.remove();
                        }
                    }, 300);
                }
            }, 2000); // 2 segundos para mostrar o estado "conciliado"
        }
    }

    // Cria um toast próprio se não houver sistema de toast disponível
    criarToast(tipo, mensagem) {
        // Criar container de toasts se não existir
        let container = document.getElementById('toast-container-buscar-existente');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container-buscar-existente';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Criar toast
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${tipo === 'success' ? 'success' : 'danger'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="icon icon-tabler icon-tabler-${tipo === 'success' ? 'check' : 'alert-circle'} me-2"></i>
                        ${mensagem}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', toastHtml);

        // Mostrar toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
        toast.show();

        // Remover após esconder
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Manipula a conciliação múltipla de agendamentos
    aoConciliarMultiplos(botao) {
        // Extrair ID da transação da classe do botão
        const classesBtn = Array.from(botao.classList);
        const classeTransacao = classesBtn.find(cls => cls.startsWith('conciliar-multiplos-'));
        
        if (!classeTransacao) {
            console.error('Classe de transação não encontrada no botão', botao);
            alert('Erro: ID da transação não encontrado');
            return;
        }
        
        const transacaoId = classeTransacao.replace('conciliar-multiplos-', '');
        const checkboxesMarcados = document.querySelectorAll(`input[name="agendamentos_selecionados_${transacaoId}[]"]:checked`);
        
        if (checkboxesMarcados.length === 0) {
            alert('Selecione pelo menos um agendamento para conciliar.');
            return;
        }

        const agendamentosIds = Array.from(checkboxesMarcados).map(cb => cb.value);
        
        // Executar conciliação em massa com os agendamentos selecionados
        
        // Executar conciliação múltipla
        this.executarConciliacaoMultipla(agendamentosIds, transacaoId);
    }

    // Executa a conciliação múltipla de agendamentos
    async executarConciliacaoMultipla(agendamentosIds, transacaoId) {
        const count = agendamentosIds.length;
        
        // Abrir modal de confirmação personalizado
        this.abrirModalConciliacaoMassa(agendamentosIds, transacaoId);
    }

    // Abre o modal de conciliação em massa
    abrirModalConciliacaoMassa(agendamentosIds, transacaoId) {
        try {
            // Obter dados da transação
            const dadosTransacao = this.extrairDadosTransacao(transacaoId);
            if (!dadosTransacao) {
                alert('Dados da transação não encontrados');
                return;
            }

            // Obter dados dos agendamentos selecionados
            const agendamentos = agendamentosIds.map(id => this.extrairDadosAgendamento(id)).filter(ag => ag);

            if (agendamentos.length === 0) {
                alert('Dados dos agendamentos não encontrados');
                return;
            }

            // Preencher dados no modal
            this.preencherModalConciliacaoMassa(dadosTransacao, agendamentos, transacaoId, agendamentosIds);

            // Configurar evento do botão de confirmação
            this.configurarEventoConfirmacaoMassa(agendamentosIds, transacaoId);

            // Mostrar o modal
            const modal = new bootstrap.Modal(document.getElementById('modal-confirmar-conciliacao-massa'));
            modal.show();

        } catch (error) {
            console.error('Erro ao abrir modal de conciliação massa:', error);
            alert('Erro ao abrir modal de confirmação');
        }
    }

    // Preenche os dados no modal de conciliação massa
    preencherModalConciliacaoMassa(transacao, agendamentos, transacaoId, agendamentosIds) {
        // Dados da transação
        document.getElementById('modal-massa-transacao-valor').textContent = transacao.valor || 'N/A';
        document.getElementById('modal-massa-transacao-data').textContent = transacao.data || 'N/A';
        document.getElementById('modal-massa-transacao-descricao').textContent = transacao.descricao || 'N/A';
        document.getElementById('modal-massa-transacao-fitid').textContent = transacao.fitid || 'N/A';

        // Calcular totais dos agendamentos
        const valorTotalAgendamentos = agendamentos.reduce((total, ag) => {
            const valor = this.converterValorParaNumero(ag.valor_formatado || '0');
            return total + valor;
        }, 0);

        const valorTransacao = this.converterValorParaNumero(transacao.valor || '0');
        // Diferença: agendamentos - transação (pode ser positiva ou negativa)
        const diferenca = valorTotalAgendamentos - valorTransacao;
        const diferencaAbsoluta = Math.abs(diferenca);
        const statusConciliacao = diferencaAbsoluta === 0 ? 'EXATO' : diferencaAbsoluta < 1 ? 'APROXIMADO' : 'DIFERENÇA';

        // Resumo dos agendamentos
        document.getElementById('modal-massa-quantidade-agendamentos').textContent = agendamentos.length;
        document.getElementById('modal-massa-valor-total-agendamentos').textContent = this.formatarMoeda(valorTotalAgendamentos);
        document.getElementById('modal-massa-diferenca').textContent = this.formatarMoeda(diferenca);

        // Status da conciliação
        const statusElement = document.getElementById('modal-massa-status');
        let statusClass = 'badge-outline text-muted';
        let statusText = 'Indefinido';

        switch (statusConciliacao) {
            case 'EXATO':
                statusClass = 'badge-outline text-green';
                statusText = 'Valores Exatos';
                break;
            case 'APROXIMADO':
                statusClass = 'badge-outline text-yellow';
                statusText = 'Aproximado (< R$ 1,00)';
                break;
            case 'DIFERENÇA':
                statusClass = 'badge-outline text-red';
                const sinal = diferenca >= 0 ? '+' : '';
                statusText = `Diferença: ${sinal}${this.formatarMoeda(Math.abs(diferenca))}`;
                break;
        }

        statusElement.innerHTML = `<span class="badge ${statusClass}">${statusText}</span>`;

        // Lista detalhada dos agendamentos
        const tbody = document.getElementById('modal-massa-lista-agendamentos');
        tbody.innerHTML = '';

        agendamentos.forEach(agendamento => {
            const tr = document.createElement('tr');

            // Categorias
            let categoriasHtml = '<span class="text-muted">-</span>';
            if (agendamento.categorias && agendamento.categorias.length > 0) {
                categoriasHtml = agendamento.categorias
                    .slice(0, 2) // Máximo 2 categorias para não ocupar muito espaço
                    .map(cat => `<span class="badge bg-light text-dark me-1">${cat}</span>`)
                    .join('');
                
                if (agendamento.categorias.length > 2) {
                    categoriasHtml += `<span class="text-muted">+${agendamento.categorias.length - 2}</span>`;
                }
            }

            // Preparar informações de valor para o modal - limpar informações extras
            let valorDisplay = agendamento.valor_formatado || 'R$ 0,00';
            
            // Remover informações extras como "Restante (X% pago)" e manter apenas o valor
            if (valorDisplay.includes('Restante')) {
                // Extrair apenas o valor monetário, removendo texto adicional
                const matchValor = valorDisplay.match(/R\$\s*[\d.,]+/);
                if (matchValor) {
                    valorDisplay = matchValor[0];
                }
            }
            
            tr.innerHTML = `
                <td>
                    <span class="badge bg-light text-light-fg">${agendamento.origem_codigo || agendamento.id}</span>
                </td>
                <td>${agendamento.data_vencimento || '-'}</td>
                <td>${agendamento.pessoa_nome || '-'}</td>
                <td>
                    <span title="${agendamento.descricao || '-'}">
                        ${(agendamento.descricao || '-').length > 30 ? 
                          (agendamento.descricao || '-').substring(0, 30) + '...' : 
                          (agendamento.descricao || '-')}
                    </span>
                </td>
                <td>${categoriasHtml}</td>
                <td class="text-end fw-bold">${valorDisplay}</td>
            `;

            tbody.appendChild(tr);
        });
    }

    // Configura o evento de confirmação do modal massa
    configurarEventoConfirmacaoMassa(agendamentosIds, transacaoId) {
        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao-massa');
        
        // Remover eventos anteriores
        const novoBotao = btnConfirmar.cloneNode(true);
        btnConfirmar.parentNode.replaceChild(novoBotao, btnConfirmar);

        // Adicionar novo evento
        novoBotao.addEventListener('click', async () => {
            // Mostrar loading
            const spinner = novoBotao.querySelector('.spinner-border');
            const btnText = novoBotao.querySelector('.btn-text');
            
            spinner.classList.remove('d-none');
            novoBotao.disabled = true;
            btnText.textContent = 'Processando...';

            try {
                // Processar conciliação (sem observações personalizadas)
                const resultado = await this.processarConciliacaoMultiplaDireta(
                    agendamentosIds, 
                    transacaoId, 
                    'Conciliação em massa via buscar existente'
                );
                
                if (resultado.success) {
                    // Fechar modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('modal-confirmar-conciliacao-massa'));
                    modal.hide();
                }
            } finally {
                // Restaurar botão
                spinner.classList.add('d-none');
                novoBotao.disabled = false;
                btnText.textContent = 'Confirmar Conciliação';
            }
        });
    }

    // Formatar valor monetário
    formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    }

    // Processa a conciliação múltipla diretamente (chamado após confirmação)
    async processarConciliacaoMultiplaDireta(agendamentosIds, transacaoId, observacoes) {
        const count = agendamentosIds.length;
        
        try {
            const response = await fetch('/api/processar-conciliacao-massa', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agendamentos_ids: agendamentosIds,
                    transacao_id: transacaoId,
                    observacoes: observacoes || 'Conciliação em massa via buscar existente'
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                this.mostrarToastSucesso(resultado.message);
                
                // Recarregar página após 1.5s para atualizar valores
                setTimeout(() => window.location.reload(), 1500);
                
                return { success: true, message: resultado.message };
            } else {
                this.mostrarToastErro(resultado.message || 'Erro ao processar conciliação em massa');
                return { success: false, message: resultado.message || 'Erro ao processar conciliação em massa' };
            }
        } catch (error) {
            console.error('Erro na conciliação múltipla:', error);
            this.mostrarToastErro('Erro de conexão. Tente novamente.');
            return { success: false, message: 'Erro de conexão. Tente novamente.' };
        }
    }

    // ============================================
    // MÉTODOS PARA CONCILIAÇÃO PARCIAL
    // ============================================

    abrirModalConciliacaoParcial(botao) {
        const agendamentoId = botao.dataset.agendamentoId;
        const transacaoId = botao.dataset.transacaoId;
        const valorTotal = parseInt(botao.dataset.agendamentoValor);
        const valorConciliado = parseInt(botao.dataset.agendamentoValorConciliado) || 0;

        // Buscar dados da transação
        const transacaoData = this.obterDadosTransacao(transacaoId);
        const agendamentoData = this.extrairDadosAgendamento(agendamentoId);

        if (!transacaoData || !agendamentoData) {
            this.mostrarToastErro('Erro ao carregar dados para conciliação parcial');
            return;
        }

        // Preencher modal
        this.preencherModalConciliacaoParcial({
            transacao: transacaoData,
            agendamento: agendamentoData,
            transacaoId,
            agendamentoId,
            valorTotal,
            valorConciliado
        });

        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('modalConciliacaoParcial'));
        modal.show();
    }

    preencherModalConciliacaoParcial(dados) {
        const { transacao, agendamento, transacaoId, agendamentoId, valorTotal, valorConciliado } = dados;
        const valorPendente = valorTotal - valorConciliado;

        // Dados da transação
        document.getElementById('parcial-transacao-valor').textContent = this.formatarMoeda(Math.abs(transacao.valor));
        document.getElementById('parcial-transacao-data').textContent = new Date(transacao.data_transacao).toLocaleDateString('pt-BR');
        document.getElementById('parcial-transacao-descricao').textContent = transacao.descricao_limpa || transacao.memo || 'Sem descrição';

        // Dados do agendamento
        document.getElementById('parcial-agendamento-valor-total').textContent = this.formatarMoeda(valorTotal / 100);
        document.getElementById('parcial-agendamento-valor-conciliado').textContent = this.formatarMoeda(valorConciliado / 100);
        document.getElementById('parcial-agendamento-valor-pendente').textContent = this.formatarMoeda(valorPendente / 100);

        // Configurar input com valor máximo e validações
        const inputValor = document.getElementById('valor-parcial-input');
        const valorMaximo = (valorPendente / 100);
        inputValor.max = valorMaximo.toFixed(2);
        inputValor.value = '';
        inputValor.placeholder = `Máx: R$ ${valorMaximo.toFixed(2)}`;
        
        // Adicionar validação em tempo real
        inputValor.addEventListener('input', function() {
            const valorDigitado = parseFloat(this.value) || 0;
            const valorMax = parseFloat(this.max);
            
            if (valorDigitado > valorMax) {
                this.setCustomValidity(`Valor não pode ser maior que R$ ${valorMax.toFixed(2)}`);
                this.classList.add('is-invalid');
            } else if (valorDigitado <= 0) {
                this.setCustomValidity('Valor deve ser maior que R$ 0,00');
                this.classList.add('is-invalid');
            } else {
                this.setCustomValidity('');
                this.classList.remove('is-invalid');
            }
        });
        
        inputValor.focus();

        // Limpar observações
        document.getElementById('observacoes-parcial').value = '';

        // Configurar botão de confirmação
        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao-parcial');
        btnConfirmar.onclick = () => this.processarConciliacaoParcial(transacaoId, agendamentoId);
    }

    obterDadosTransacao(transacaoId) {
        // Buscar dados da transação na DOM
        const containerTransacao = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId}`)?.closest('.col-12');
        if (!containerTransacao) return null;

        // Buscar valor da transação
        let valor = 0;
        const valorElement = containerTransacao.querySelector('[data-valor-transacao]');
        if (valorElement) {
            valor = parseFloat(valorElement.dataset.valorTransacao);
        } else {
            // Tentar extrair do badge de valor
            const badgeValor = containerTransacao.querySelector('.badge:contains("R$"), .valor-transacao');
            if (badgeValor) {
                const match = badgeValor.textContent.match(/R\$\s*([\d.-]+,\d{2})/);
                if (match) {
                    valor = parseFloat(match[1].replace('.', '').replace(',', '.'));
                }
            }
        }

        // Buscar data da transação
        let dataTransacao = new Date().toISOString();
        const dataElement = containerTransacao.querySelector('[data-data-transacao]');
        if (dataElement) {
            dataTransacao = dataElement.dataset.dataTransacao;
        }

        // Buscar descrição
        let descricao = 'Transação OFX';
        const descricaoElement = containerTransacao.querySelector('.descricao-transacao, [data-descricao]');
        if (descricaoElement) {
            descricao = descricaoElement.textContent.trim() || descricaoElement.dataset.descricao || descricao;
        }

        return {
            id: transacaoId,
            valor: valor,
            data_transacao: dataTransacao,
            descricao_limpa: descricao,
            memo: descricao
        };
    }

    async processarConciliacaoParcial(transacaoId, agendamentoId) {
        const inputValor = document.getElementById('valor-parcial-input');
        const inputObservacoes = document.getElementById('observacoes-parcial');
        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao-parcial');

        // Validações
        const valorParcial = parseFloat(inputValor.value);
        if (!valorParcial || valorParcial <= 0) {
            this.mostrarToastErro('Digite um valor válido para a conciliação parcial');
            inputValor.focus();
            return;
        }

        const valorParcialCentavos = Math.round(valorParcial * 100);
        const observacoes = inputObservacoes.value.trim() || 'Conciliação parcial';

        try {
            // Desabilitar botão
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Processando...';

            const response = await fetch('/api/processar-conciliacao-parcial', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transacao_id: transacaoId,
                    agendamento_id: agendamentoId,
                    valor_parcial: valorParcialCentavos,
                    observacoes: observacoes
                })
            });

            const resultado = await response.json();

            if (resultado.success) {
                // Fechar modal
                bootstrap.Modal.getInstance(document.getElementById('modalConciliacaoParcial')).hide();

                // Mostrar sucesso
                this.mostrarToastSucesso(resultado.message);
                
                // Recarregar página após 1.5s para atualizar valores
                setTimeout(() => window.location.reload(), 1500);
                return;

            } else {
                this.mostrarToastErro(resultado.message || 'Erro ao processar conciliação parcial');
            }

        } catch (error) {
            console.error('Erro na conciliação parcial:', error);
            this.mostrarToastErro('Erro de conexão. Tente novamente.');
        } finally {
            // Reabilitar botão
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-check me-1"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 12l5 5l10 -10"/></svg>Confirmar Conciliação Parcial';
        }
    }

    atualizarLinhaAgendamento(agendamentoId, dados) {
        const linhaAgendamento = document.querySelector(`[data-agendamento-id="${agendamentoId}"]`)?.closest('tr');
        if (!linhaAgendamento) return;

        // Atualizar dados dos botões
        const btnParcial = linhaAgendamento.querySelector('.btn-conciliar-parcial');
        const btnNormal = linhaAgendamento.querySelector(`[data-agendamento-id="${agendamentoId}"]`);
        
        if (btnParcial) {
            // Atualizar valor conciliado nos datasets
            const valorConciliadoAtual = parseInt(btnParcial.dataset.agendamentoValorConciliado || 0);
            const novoValorConciliado = valorConciliadoAtual + dados.valor_parcial_conciliado;
            
            btnParcial.dataset.agendamentoValorConciliado = novoValorConciliado;
            btnNormal.dataset.agendamentoValorConciliado = novoValorConciliado;
        }

        // Atualizar exibição do valor na coluna
        const colunaValor = linhaAgendamento.querySelector('td:nth-last-child(2)'); // Penúltima coluna (valor)
        if (colunaValor) {
            const valorTotal = dados.valor_total || (parseInt(btnParcial?.dataset.agendamentoValor || 0) / 100);
            const valorConciliado = (parseInt(btnParcial?.dataset.agendamentoValorConciliado || 0) / 100);
            const valorPendente = valorTotal - valorConciliado;
            const percentual = ((valorConciliado / valorTotal) * 100).toFixed(1);

            colunaValor.innerHTML = `
                <div class="fw-bold">${this.formatarMoeda(valorTotal)}</div>
                <div class="text-xs text-warning">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-coin">
                        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                        <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"/>
                        <path d="M14.8 9a2 2 0 0 0 -1.8 -1h-2a2 2 0 1 0 0 4h2a2 2 0 1 1 0 4h-2a2 2 0 0 1 -1.8 -1"/>
                        <path d="M12 7v10"/>
                    </svg>
                    Conciliado: ${percentual}% (${this.formatarMoeda(valorConciliado)})
                    <br>
                    Pendente: ${this.formatarMoeda(valorPendente)}
                </div>
            `;
        }
    }

    marcarTransacaoComoConciliada(transacaoId) {
        const containerTransacao = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId}`)?.closest('.col-12');
        if (containerTransacao) {
            // Aplicar efeito visual de conciliada
            containerTransacao.style.opacity = '0.6';
            containerTransacao.style.pointerEvents = 'none';
            
            // Adicionar badge de conciliado na header
            const cardHeader = containerTransacao.querySelector('.card-header h3');
            if (cardHeader && !cardHeader.querySelector('.badge-conciliado')) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-success ms-2 badge-conciliado';
                badge.textContent = 'Totalmente Conciliada';
                cardHeader.appendChild(badge);
            }

            // Desabilitar todos os botões de conciliação
            const botoesAcao = containerTransacao.querySelectorAll('.conciliacao-btn');
            botoesAcao.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('disabled');
            });
        }
    }

    atualizarInformacoesTransacao(transacaoId, dados) {
        const containerTransacao = document.querySelector(`.conciliacao-ofx-buscar-existente-${transacaoId}`)?.closest('.col-12');
        if (!containerTransacao) return;

        // Buscar o valor da transação no container (pode estar em data-attribute ou texto)
        const valorTransacaoElement = containerTransacao.querySelector('[data-valor-transacao]');
        let valorTransacao = 0;
        
        if (valorTransacaoElement) {
            valorTransacao = parseFloat(valorTransacaoElement.dataset.valorTransacao);
        } else {
            // Tentar extrair do texto se não houver data-attribute
            const valorTexto = containerTransacao.querySelector('.valor-transacao, .badge:contains("R$")');
            if (valorTexto) {
                const match = valorTexto.textContent.match(/R\$\s*([\d.]+,\d{2})/);
                if (match) {
                    valorTransacao = parseFloat(match[1].replace('.', '').replace(',', '.'));
                }
            }
        }

        if (valorTransacao > 0) {
            const valorUtilizado = (dados.valor_utilizado_total || 0) / 100;
            const valorDisponivel = valorTransacao - valorUtilizado;
            const percentualUtilizado = ((valorUtilizado / valorTransacao) * 100).toFixed(1);

            // Adicionar informação de uso parcial na header
            const cardHeader = containerTransacao.querySelector('.card-header');
            if (cardHeader) {
                let badgeUso = cardHeader.querySelector('.badge-uso-parcial');
                if (!badgeUso) {
                    badgeUso = document.createElement('span');
                    badgeUso.className = 'badge bg-warning text-dark ms-2 badge-uso-parcial';
                    cardHeader.appendChild(badgeUso);
                }
                badgeUso.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-coin me-1">
                        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                        <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"/>
                        <path d="M14.8 9a2 2 0 0 0 -1.8 -1h-2a2 2 0 1 0 0 4h2a2 2 0 1 1 0 4h-2a2 2 0 0 1 -1.8 -1"/>
                        <path d="M12 7v10"/>
                    </svg>
                    ${percentualUtilizado}% utilizada | Restante: ${this.formatarMoeda(valorDisponivel)}
                `;
            }
        }
    }
}

// Inicializar quando DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    window.conciliacaoOfxBuscarExistente = new ConciliacaoOfxBuscarExistente();
});

// Exportar para uso em outros módulos se necessário
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConciliacaoOfxBuscarExistente;
}