// Sistema de Conciliação de Sugestões OFX
class ConciliacaoSugestoes {
    constructor() {
        this.dadosConciliacao = null;
        this.inicializar();
    }

    // Inicializa eventos e componentes
    inicializar() {
        this.configurarEventos();
        this.inicializarComponentes();
        this.configurarEventoConciliacao();
    }

    // Escuta eventos de conciliação para remover agendamento de outras sugestões
    configurarEventoConciliacao() {
        document.addEventListener('conciliacao-realizada', (event) => {
            const { agendamentoId } = event.detail;
            if (agendamentoId) {
                this.removerAgendamentoDeTodasSugestoes(agendamentoId);
            }
        });
    }

    // Configura eventos de clique nos botões de conciliar
    configurarEventos() {
        // Evento para botões de conciliação de sugestões
        document.addEventListener('click', (event) => {
            if (event.target.closest('.btn-conciliar-sugestao')) {
                event.preventDefault();
                this.abrirModalConciliacao(event.target.closest('.btn-conciliar-sugestao'));
            }
        });

        // Evento para confirmar conciliação no modal
        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao');
        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', () => {
                this.confirmarConciliacao();
            });
        }
    }

    // Inicializa componentes Bootstrap
    inicializarComponentes() {
        this.modal = new bootstrap.Modal(document.getElementById('modal-confirmar-conciliacao'));
    }

    // Abre o modal de confirmação de conciliação
    abrirModalConciliacao(botao) {
        const agendamentoId = botao.dataset.agendamentoId;
        const transacaoId = botao.dataset.transacaoId;

        if (!agendamentoId || !transacaoId) {
            this.mostrarToast('erro', 'Dados da conciliação não encontrados.');
            return;
        }

        // Buscar dados dos elementos na página
        const dadosTransacao = this.extrairDadosTransacao(transacaoId);
        const dadosAgendamento = this.extrairDadosAgendamento(botao);

        if (!dadosTransacao || !dadosAgendamento) {
            this.mostrarToast('erro', 'Erro ao carregar dados para conciliação.');
            return;
        }

        // Armazenar dados para uso posterior
        this.dadosConciliacao = {
            transacao_id: transacaoId,
            agendamento_id: agendamentoId,
            transacao: dadosTransacao,
            agendamento: dadosAgendamento
        };

        // Preencher modal com os dados
        this.preencherModal();
        
        // Mostrar modal
        this.modal.show();
    }

    // Extrai dados da transação OFX da página
    extrairDadosTransacao(transacaoId) {
        // Busca o card da transação pela estrutura da página
        const cardTransacao = document.querySelector(`.conciliacao-ofx-id-${transacaoId} .card[data-transacao-id]`);
        if (!cardTransacao) {
            console.error(`Card da transação ${transacaoId} não encontrado`);
            return null;
        }

        return {
            valor: cardTransacao.dataset.transacaoValor || '-',
            data: cardTransacao.dataset.transacaoData || '-', 
            descricao: cardTransacao.dataset.transacaoDescricao || '-',
            fitid: cardTransacao.dataset.transacaoFitid || '-'
        };
    }

    // Extrai dados do agendamento do card de sugestão
    extrairDadosAgendamento(botao) {
        const card = botao.closest('.sugestao-card');
        if (!card) return null;

        const valor = card.querySelector('.valor-sugestao strong')?.textContent || '-';
        const vencimento = card.querySelector('.data-sugestao strong')?.textContent || '-';
        const pessoa = card.querySelector('.beneficiario-sugestao strong')?.textContent || '-';
        const origem = card.querySelector('.badge')?.textContent || '-';
        
        // Extrair categorias
        const categorias = [];
        const badgesCategorias = card.querySelectorAll('.categorias-sugestao .badge');
        badgesCategorias.forEach(badge => {
            if (!badge.classList.contains('bg-secondary-subtle')) {
                categorias.push(badge.textContent.trim());
            }
        });

        return {
            valor,
            vencimento,
            pessoa,
            origem,
            categorias
        };
    }

    // Preenche o modal com os dados da conciliação
    preencherModal() {
        const { transacao, agendamento } = this.dadosConciliacao;

        // Preenche dados da transação
        document.getElementById('modal-transacao-valor').textContent = transacao.valor;
        document.getElementById('modal-transacao-data').textContent = transacao.data;
        document.getElementById('modal-transacao-descricao').textContent = transacao.descricao;
        document.getElementById('modal-transacao-fitid').textContent = transacao.fitid;

        // Preenche dados do agendamento
        document.getElementById('modal-agendamento-valor').textContent = agendamento.valor;
        document.getElementById('modal-agendamento-vencimento').textContent = agendamento.vencimento;
        document.getElementById('modal-agendamento-pessoa').textContent = agendamento.pessoa;
        document.getElementById('modal-agendamento-origem').textContent = agendamento.origem;

        // Preencher categorias
        this.preencherCategorias(agendamento.categorias);

    }

    // Preenche as categorias no modal
    preencherCategorias(categorias) {
        const container = document.getElementById('modal-agendamento-categorias');
        container.innerHTML = '';

        if (categorias.length === 0) {
            container.innerHTML = '<span class="badge bg-secondary-subtle text-secondary">Sem categoria definida</span>';
            return;
        }

        categorias.forEach(categoria => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-light text-dark border';
            badge.textContent = categoria;
            container.appendChild(badge);
        });
    }


    // Converte valor formatado para número
    converterValorParaNumero(valor) {
        return parseFloat(
            valor.replace('R$', '')
                 .replace(/\./g, '')
                 .replace(',', '.')
                 .trim()
        ) || 0;
    }

    // Confirma e processa a conciliação
    async confirmarConciliacao() {
        if (!this.dadosConciliacao) {
            this.mostrarToast('erro', 'Dados da conciliação perdidos.');
            return;
        }

        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao');
        const spinner = btnConfirmar.querySelector('.spinner-border');
        const texto = btnConfirmar.querySelector('.btn-text');

        try {
            // Mostrar loading
            this.mostrarToast('loading', 'Processando conciliação...');
            btnConfirmar.disabled = true;
            spinner.classList.remove('d-none');
            texto.textContent = 'Processando...';

            const response = await fetch('/api/processar-conciliacao', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transacao_id: this.dadosConciliacao.transacao_id,
                    agendamento_id: this.dadosConciliacao.agendamento_id
                })
            });

            const data = await response.json();

            // Esconder loading
            this.esconderToast('loading');

            if (data.success) {
                // Disparar evento para que outras partes do sistema sejam notificadas
                document.dispatchEvent(new CustomEvent('conciliacao-realizada', {
                    detail: {
                        transacaoId: this.dadosConciliacao.transacao_id,
                        agendamentoId: this.dadosConciliacao.agendamento_id
                    }
                }));

                // Sucesso - remover transação inteira da tela
                this.removerTransacaoCompletaComEfeito(this.dadosConciliacao.transacao_id);
                this.removerAgendamentoDeTodasSugestoes(this.dadosConciliacao.agendamento_id);
                this.mostrarToast('sucesso', data.message);
                this.modal.hide();
            } else {
                // Erro - mostrar mensagem
                this.mostrarToast('erro', data.message || 'Erro ao processar conciliação.');
            }

        } catch (error) {
            console.error('Erro na conciliação:', error);
            this.esconderToast('loading');
            this.mostrarToast('erro', 'Erro de comunicação com o servidor.');
        } finally {
            // Restaurar botão
            btnConfirmar.disabled = false;
            spinner.classList.add('d-none');
            texto.textContent = 'Confirmar Conciliação';
        }
    }

    // Remove a transação completa da tela quando uma conciliação é realizada
    removerTransacaoCompletaComEfeito(transacaoId) {
        console.log(`[Conciliação] Removendo transação completa ${transacaoId} da tela`);
        
        // Buscar a linha completa da transação usando o ID
        const linhaTransacao = document.querySelector(`.conciliacao-ofx-id-${transacaoId}`);
        if (!linhaTransacao) {
            console.warn(`[Conciliação] Linha da transação ${transacaoId} não encontrada`);
            return;
        }

        // Efeito visual de sucesso antes de remover
        linhaTransacao.style.transition = 'all 0.5s ease-out';
        linhaTransacao.style.transform = 'scale(1.02)';
        linhaTransacao.style.backgroundColor = '#d4edda';
        linhaTransacao.style.borderRadius = '8px';
        linhaTransacao.style.padding = '10px';
        linhaTransacao.style.boxShadow = '0 4px 15px rgba(40, 167, 69, 0.4)';

        // Estilizar todos os cards internos
        const todosCards = linhaTransacao.querySelectorAll('.card');
        todosCards.forEach(card => {
            card.style.transition = 'all 0.5s ease-out';
            card.style.borderColor = '#28a745';
            card.style.backgroundColor = '#f8f9fa';
        });

        // Adicionar ícone de sucesso
        const iconeSucesso = document.createElement('div');
        iconeSucesso.innerHTML = `
            <div style="position: absolute; top: 10px; right: 15px; z-index: 1000;">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="3">
                    <path d="M9 12l2 2 4-4"/>
                    <circle cx="12" cy="12" r="10"/>
                </svg>
            </div>
        `;
        linhaTransacao.appendChild(iconeSucesso);

        setTimeout(() => {
            // Fade out da transação
            linhaTransacao.style.transition = 'all 0.6s ease-in';
            linhaTransacao.style.opacity = '0';
            linhaTransacao.style.transform = 'scale(0.95) translateY(-30px)';
            
            setTimeout(() => {
                // Colapso final da altura
                const alturaAtual = linhaTransacao.offsetHeight;
                
                linhaTransacao.style.transition = 'all 0.5s ease-in-out';
                linhaTransacao.style.height = alturaAtual + 'px';
                linhaTransacao.style.overflow = 'hidden';
                
                // Forçar reflow
                linhaTransacao.offsetHeight;
                
                // Colapsar completamente
                linhaTransacao.style.height = '0px';
                linhaTransacao.style.padding = '0';
                linhaTransacao.style.margin = '0';
                
                setTimeout(() => {
                    linhaTransacao.remove();
                    console.log(`[Conciliação] Transação ${transacaoId} removida da interface`);
                    
                    // Verifica se página ficou vazia
                    this.verificarPaginaVazia();
                }, 500);
            }, 600);
        }, 600);
    }

    // Verifica se a página ficou sem transações e mostra mensagem
    verificarPaginaVazia() {
        const transacoesRestantes = document.querySelectorAll('.row.row-cards[class*="conciliacao-ofx-id-"]');
        
        if (transacoesRestantes.length === 0) {
            // Cria mensagem de página vazia
            const container = document.querySelector('.container-xl');
            if (container) {
                const mensagemVazia = document.createElement('div');
                mensagemVazia.className = 'text-center py-5';
                mensagemVazia.innerHTML = `
                    <div class="empty">
                        <div class="empty-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-success">
                                <path d="M9 12l2 2 4-4"/>
                                <circle cx="12" cy="12" r="10"/>
                            </svg>
                        </div>
                        <h3 class="empty-title">Todas as transações foram conciliadas!</h3>
                        <p class="empty-subtitle text-muted">
                            Não há mais transações OFX pendentes de conciliação nesta página.
                        </p>
                        <div class="empty-action">
                            <a href="${window.location.pathname}" class="btn btn-primary">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-1">
                                    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                                    <path d="M21 3v5h-5"/>
                                    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                                    <path d="M8 16H3v5"/>
                                </svg>
                                Recarregar Página
                            </a>
                        </div>
                    </div>
                `;
                
                // Insere após mensagens flash se existirem
                const mensagensFlash = container.querySelector('.alert');
                if (mensagensFlash) {
                    mensagensFlash.after(mensagemVazia);
                } else {
                    container.appendChild(mensagemVazia);
                }
            }
        }
    }

    // Remove agendamento de todas as outras sugestões da página
    removerAgendamentoDeTodasSugestoes(agendamentoId) {
        console.log(`[Conciliação] Removendo agendamento ${agendamentoId} de todas as sugestões`);
        
        // Busca todos os botões de conciliação com este agendamento ID
        const botoesConciliacao = document.querySelectorAll(`.btn-conciliar-sugestao[data-agendamento-id="${agendamentoId}"]`);
        
        // Para cada botão encontrado, remove o card pai
        botoesConciliacao.forEach((botao, index) => {
            console.log(`[Conciliação] Removendo sugestão ${index + 1} do agendamento ${agendamentoId}`);
            
            // Encontra o card pai da sugestão
            const cardSugestao = botao.closest('.sugestao-card') || botao.closest('.card') || botao.closest('.col-12');
            
            if (cardSugestao) {
                // Fade out simples
                cardSugestao.style.transition = 'opacity 0.3s ease-out';
                cardSugestao.style.opacity = '0';
                
                // Remove após a animação
                setTimeout(() => {
                    cardSugestao.remove();
                    console.log(`[Conciliação] Card do agendamento ${agendamentoId} removido`);
                }, 300);
            }
        });
        
        // Se removeu alguma sugestão, verifica se alguma aba ficou vazia
        if (botoesConciliacao.length > 0) {
            setTimeout(() => {
                this.verificarTabsVazias();
            }, 400);
        }
    }

    // Verifica se alguma tab de sugestões ficou vazia e mostra mensagem
    verificarTabsVazias() {
        // Buscar todas as tabs de sugestão
        const tabsSugestao = document.querySelectorAll('[id*="tabs-sugestao-"]');
        
        tabsSugestao.forEach(tab => {
            const sugestoesRestantes = tab.querySelectorAll('.sugestao-card, .card[data-agendamento-id]');
            
            // Se não tem mais sugestões, mostrar mensagem
            if (sugestoesRestantes.length === 0) {
                tab.innerHTML = `
                    <div class="text-center py-4">
                        <div class="text-muted">
                            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="mb-2">
                                <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
                                <path d="M9 12l2 2l4 -4"/>
                                <path d="M21 12a9 9 0 1 0 -18 0a9 9 0 0 0 18 0z"/>
                            </svg>
                            <h5>Todas as sugestões foram conciliadas</h5>
                            <p class="small mb-0">Não há mais agendamentos disponíveis para esta transação.</p>
                        </div>
                    </div>
                `;
            }
        });
    }

    // Mostra toast de notificação
    mostrarToast(tipo, mensagem) {
        const toastId = `toast-conciliacao-${tipo}`;
        const toastElement = document.getElementById(toastId);
        
        if (!toastElement) return;

        // Atualizar mensagem se necessário
        if (tipo !== 'loading') {
            const detalhes = toastElement.querySelector(`#toast-conciliacao-${tipo === 'sucesso' ? 'detalhes' : 'erro-detalhes'}`);
            if (detalhes) {
                detalhes.textContent = mensagem;
            }
        }

        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }

    // Esconde toast específico
    esconderToast(tipo) {
        const toastId = `toast-conciliacao-${tipo}`;
        const toastElement = document.getElementById(toastId);
        
        if (toastElement) {
            const toast = bootstrap.Toast.getInstance(toastElement);
            if (toast) {
                toast.hide();
            }
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.conciliacaoSugestoes = new ConciliacaoSugestoes();
});

// Exportar para uso em módulos se necessário
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConciliacaoSugestoes;
}