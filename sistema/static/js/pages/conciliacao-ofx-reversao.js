/**
 * Gerenciador de Reversão de Conciliação OFX
 * 
 * Este módulo é responsável por gerenciar a reversão de conciliações bancárias
 * de transações OFX, fornecendo uma interface clara e segura para o usuário.
 * 
 * Funcionalidades:
 * - Exibir detalhes da conciliação a ser revertida
 * - Buscar informações via API
 * - Validar confirmação do usuário
 * - Processar reversão
 * - Exibir feedback de sucesso/erro
 * 
 * @author Sistema de Gestão
 * @version 1.0.0
 */

class ConciliacaoReversao {
    constructor() {
        this.transacaoParaReverter = null;
        this.modalReversao = null;
        this.init();
    }

    /**
     * Inicializa o gerenciador de reversão
     */
    init() {
        console.log('[ReversaoOFX] Inicializando gerenciador de reversão...');
        this.configurarEventos();
        this.inicializarModal();
    }

    /**
     * Configura todos os eventos necessários
     */
    configurarEventos() {
        // Evento para checkbox de confirmação
        const checkboxConfirmacao = document.getElementById('confirmarReversao');
        if (checkboxConfirmacao) {
            checkboxConfirmacao.addEventListener('change', (e) => {
                const btnConfirmar = document.getElementById('btnConfirmarReversao');
                if (btnConfirmar) {
                    btnConfirmar.disabled = !e.target.checked;
                }
            });
        }

        // Evento para botão de confirmação
        const btnConfirmar = document.getElementById('btnConfirmarReversao');
        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', () => {
                this.confirmarReversao();
            });
        }

        // Evento quando modal é fechado - limpar dados
        const modal = document.getElementById('modalReverterConciliacao');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                this.limparDadosModal();
            });
        }
    }

    /**
     * Inicializa referências do modal
     */
    inicializarModal() {
        const modalElement = document.getElementById('modalReverterConciliacao');
        if (modalElement) {
            this.modalReversao = new bootstrap.Modal(modalElement);
        }
    }

    /**
     * Abre modal de reversão para uma transação específica
     * @param {number} transacaoId - ID da transação
     * @param {string} fitid - FITID da transação
     * @param {string} valorFormatado - Valor formatado da transação
     * @param {string} dataTransacao - Data da transação (opcional)
     */
    abrirModalReversao(transacaoId, fitid, valorFormatado, dataTransacao = null) {
        // Armazenar dados da transação
        this.transacaoParaReverter = {
            id: transacaoId,
            fitid: fitid,
            valorFormatado: valorFormatado,
            dataTransacao: dataTransacao
        };

        // Preencher informações básicas da transação
        this.preencherInformacoesTransacao();

        // Resetar estado do modal
        this.resetarModal();

        // Mostrar modal
        if (this.modalReversao) {
            this.modalReversao.show();
        }

        // Carregar detalhes da conciliação
        this.carregarDetalhesConciliacao();
    }

    /**
     * Preenche as informações básicas da transação no modal
     */
    preencherInformacoesTransacao() {
        if (!this.transacaoParaReverter) return;

        const elementos = {
            'reverterDataTransacao': this.transacaoParaReverter.dataTransacao || 'N/A',
            'reverterValorTransacao': this.transacaoParaReverter.valorFormatado || 'N/A',
            'reverterDescricaoTransacao': this.transacaoParaReverter.fitid || 'N/A',
            'reverterFitidTransacao': this.transacaoParaReverter.fitid || 'N/A'
        };

        Object.entries(elementos).forEach(([id, valor]) => {
            const elemento = document.getElementById(id);
            if (elemento) {
                elemento.textContent = valor;
            }
        });
    }

    /**
     * Reset do modal para estado inicial
     */
    resetarModal() {
        // Resetar checkbox
        const checkbox = document.getElementById('confirmarReversao');
        if (checkbox) {
            checkbox.checked = false;
        }

        // Desabilitar botão
        const btnConfirmar = document.getElementById('btnConfirmarReversao');
        if (btnConfirmar) {
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = `
                <i class="fas fa-undo me-2"></i>Confirmar Reversão
            `;
        }

        // Mostrar loading no conteúdo
        this.mostrarCarregando();
    }

    /**
     * Mostra estado de carregando
     */
    mostrarCarregando() {
        // Esconder conteúdo
        const conteudo = document.getElementById('reverterConteudo');
        const erro = document.getElementById('reverterErro');
        const carregando = document.getElementById('reverterCarregando');

        if (conteudo) conteudo.style.display = 'none';
        if (erro) erro.style.display = 'none';
        if (carregando) carregando.style.display = 'block';
    }

    /**
     * Mostra conteúdo principal
     */
    mostrarConteudo() {
        const conteudo = document.getElementById('reverterConteudo');
        const erro = document.getElementById('reverterErro');
        const carregando = document.getElementById('reverterCarregando');

        if (conteudo) conteudo.style.display = 'block';
        if (erro) erro.style.display = 'none';
        if (carregando) carregando.style.display = 'none';
    }

    /**
     * Mostra erro
     */
    mostrarErro(mensagem) {
        const conteudo = document.getElementById('reverterConteudo');
        const erro = document.getElementById('reverterErro');
        const carregando = document.getElementById('reverterCarregando');
        const erroMensagem = document.getElementById('reverterErroMensagem');

        if (conteudo) conteudo.style.display = 'none';
        if (carregando) carregando.style.display = 'none';
        if (erro) erro.style.display = 'block';
        if (erroMensagem) erroMensagem.textContent = mensagem;
    }

    /**
     * Carrega detalhes da conciliação via API
     */
    async carregarDetalhesConciliacao() {
        if (!this.transacaoParaReverter) return;

        try {
            console.log('[ReversaoOFX] Buscando detalhes da conciliação...');

            const response = await fetch(`/api/detalhes-conciliacao/${this.transacaoParaReverter.id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`Erro na resposta: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.exibirDetalhesConciliacao(data.detalhes);
            } else {
                throw new Error(data.error || 'Erro ao buscar detalhes');
            }

        } catch (error) {
            console.error('[ReversaoOFX] Erro ao carregar detalhes:', error);
            this.exibirErroCarregamento(error.message);
        }
    }

    /**
     * Exibe os detalhes da conciliação no modal
     * @param {Object} detalhes - Detalhes da conciliação
     */
    exibirDetalhesConciliacao(detalhes) {
        // Preencher informações da conciliação
        const elemTipoConciliacao = document.getElementById('reverterTipoConciliacao');
        const elemDataConciliacao = document.getElementById('reverterDataConciliacao');
        const elemObservacoes = document.getElementById('reverterObservacoes');

        if (elemTipoConciliacao) {
            elemTipoConciliacao.textContent = detalhes.tipo_conciliacao || 'Não especificado';
        }

        if (elemDataConciliacao) {
            elemDataConciliacao.textContent = detalhes.data_conciliacao || 'N/A';
        }

        // Exibir agendamentos
        this.preencherAgendamentos(detalhes.agendamentos);

        // Exibir movimentações
        this.preencherMovimentacoes(detalhes.movimentacoes);

        // Mostrar conteúdo
        this.mostrarConteudo();
    }

    /**
     * Preenche a lista de agendamentos
     * @param {Array} agendamentos - Lista de agendamentos
     */
    preencherAgendamentos(agendamentos) {
        const container = document.getElementById('reverterAgendamentosContainer');
        const lista = document.getElementById('reverterAgendamentosList');

        if (!agendamentos || agendamentos.length === 0) {
            if (container) container.style.display = 'none';
            return;
        }

        if (container) container.style.display = 'block';
        console.log(agendamentos)
        if (lista) {
            lista.innerHTML = agendamentos.map(agendamento => `
                <tr>
                    <td class="text-center"><span class="badge badge-outline text-blue">${agendamento.tipo}</span></td>
                    <td class="text-center">${agendamento.codigo || 'N/A'}</td>
                    <td class="text-center"><strong class="text-success">${agendamento.valor}</strong></td>
                    <td class="text-center"><small class="text-muted">${agendamento.observacoes || 'N/A'}</small></td>
                </tr>
            `).join('');
        }
    }

    /**
     * Preenche a lista de movimentações
     * @param {Array} movimentacoes - Lista de movimentações
     */
    preencherMovimentacoes(movimentacoes) {
        const container = document.getElementById('reverterMovimentacoesContainer');
        const lista = document.getElementById('reverterMovimentacoesList');

        if (!movimentacoes || movimentacoes.length === 0) {
            if (container) container.style.display = 'none';
            return;
        }

        if (container) container.style.display = 'block';
        
        if (lista) {
            lista.innerHTML = movimentacoes.map(mov => `
                <tr>
                    <td class="text-center"><small>${mov.data}</small></td>
                    <td class="text-center"><strong class="text-primary">${mov.valor}</strong></td>
                    <td class="text-center"><small class="text-muted">${mov.conta || 'N/A'}</small></td>
                </tr>
            `).join('');
        }
    }

    /**
     * Exibe erro no carregamento dos detalhes
     * @param {string} mensagem - Mensagem de erro
     */
    exibirErroCarregamento(mensagem) {
        this.mostrarErro(mensagem || 'Erro ao carregar detalhes da conciliação');
    }

    /**
     * Confirma e processa a reversão da conciliação
     */
    async confirmarReversao() {
        if (!this.transacaoParaReverter) {
            console.error('[ReversaoOFX] Nenhuma transação selecionada para reversão');
            return;
        }

        const checkbox = document.getElementById('confirmarReversao');
        if (!checkbox || !checkbox.checked) {
            alert('Por favor, confirme que você entende as consequências da reversão.');
            return;
        }

        const btnConfirmar = document.getElementById('btnConfirmarReversao');
        if (btnConfirmar) {
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Processando...
            `;
        }

        try {
            console.log('[ReversaoOFX] Processando reversão da transação:', this.transacaoParaReverter.id);

            const response = await fetch('/api/reverter-conciliacao', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transacao_id: this.transacaoParaReverter.id
                })
            });

            if (!response.ok) {
                throw new Error(`Erro na resposta: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.exibirSucessoReversao(data.message);
            } else {
                throw new Error(data.error || 'Erro ao processar reversão');
            }

        } catch (error) {
            console.error('[ReversaoOFX] Erro ao processar reversão:', error);
            this.exibirErroReversao(error.message);
        }
    }

    /**
     * Exibe sucesso da reversão
     * @param {string} mensagem - Mensagem de sucesso
     */
    exibirSucessoReversao(mensagem) {
        console.log('[ReversaoOFX] Reversão processada com sucesso');

        // Fechar modal atual
        if (this.modalReversao) {
            this.modalReversao.hide();
        }

        // Mostrar modal de sucesso
        const modalSucesso = new bootstrap.Modal(document.getElementById('modal-reversao-sucesso'));
        modalSucesso.show();

        // Recarregar página após 2 segundos
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }

    /**
     * Exibe erro na reversão
     * @param {string} mensagem - Mensagem de erro
     */
    exibirErroReversao(mensagem) {
        console.error('[ReversaoOFX] Erro na reversão:', mensagem);

        // Reabilitar botão
        const btnConfirmar = document.getElementById('btnConfirmarReversao');
        if (btnConfirmar) {
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon me-1">
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                  <path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4"/>
                  <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"/>
                </svg>
                <span class="btn-text">Confirmar Reversão</span>
            `;
        }

        // Atualizar mensagem no modal de erro e exibir
        const mensagemErro = document.getElementById('mensagem-erro-reversao');
        if (mensagemErro) {
            mensagemErro.textContent = mensagem;
        }

        // Mostrar modal de erro
        const modalErro = new bootstrap.Modal(document.getElementById('modal-reversao-erro'));
        modalErro.show();
    }

    /**
     * Mostra toast de notificação
     * @param {string} tipo - Tipo do toast (success, error, warning, info)
     * @param {string} mensagem - Mensagem a ser exibida
     */
    mostrarToast(tipo, mensagem) {
        // Usar função global se disponível
        if (window.mostrarToast) {
            window.mostrarToast(tipo, mensagem);
            return;
        }

        // Fallback simples
        console.log(`[ReversaoOFX] Toast ${tipo}:`, mensagem);
        alert(`${tipo.toUpperCase()}: ${mensagem}`);
    }

    /**
     * Limpa dados do modal quando fechado
     */
    limparDadosModal() {
        this.transacaoParaReverter = null;

        // Limpar elementos do modal
        const elementos = ['reverterDataTransacao', 'reverterValorTransacao', 'reverterDescricaoTransacao', 'reverterFitidTransacao'];
        elementos.forEach(id => {
            const elemento = document.getElementById(id);
            if (elemento) {
                elemento.textContent = '-';
            }
        });

        // Resetar checkbox
        const checkbox = document.getElementById('confirmarReversao');
        if (checkbox) {
            checkbox.checked = false;
        }

        // Esconder containers
        const containers = ['reverterAgendamentosContainer', 'reverterMovimentacoesContainer', 'reverterObservacoesContainer'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.style.display = 'none';
            }
        });
    }
}

// Inicializar quando DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Criar instância global do gerenciador
    window.conciliacaoReversao = new ConciliacaoReversao();
    
    // Função global para compatibilidade com template
    window.abrirModalReversao = function(transacaoId, fitid, valorFormatado, dataTransacao) {
        if (window.conciliacaoReversao) {
            window.conciliacaoReversao.abrirModalReversao(transacaoId, fitid, valorFormatado, dataTransacao);
        } else {
            console.error('[ReversaoOFX] Gerenciador não inicializado');
        }
    };

    console.log('[ReversaoOFX] Sistema de reversão inicializado com sucesso');
});