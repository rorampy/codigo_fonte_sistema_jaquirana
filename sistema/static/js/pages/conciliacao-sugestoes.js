
class ConciliacaoSugestoes {
    constructor() {
        this.dadosConciliacao = null;
        this.inicializar();
    }

    inicializar() {
        this.configurarEventos();
        this.inicializarComponentes();
        this.configurarEventoConciliacao();
    }

    configurarEventoConciliacao() {
        document.addEventListener('conciliacao-realizada', (event) => {
            const { agendamentoId } = event.detail;
            if (agendamentoId) {
                this.removerAgendamentoDeTodasSugestoes(agendamentoId);
            }
        });
    }

    configurarEventos() {
        
        document.addEventListener('click', (event) => {
            if (event.target.closest('.btn-conciliar-sugestao')) {
                event.preventDefault();
                this.abrirModalConciliacao(event.target.closest('.btn-conciliar-sugestao'));
            }
        });

        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao');
        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', () => {
                this.confirmarConciliacao();
            });
        }
    }

    inicializarComponentes() {
        this.modal = new bootstrap.Modal(document.getElementById('modal-confirmar-conciliacao'));
    }

    abrirModalConciliacao(botao) {
        const agendamentoId = botao.dataset.agendamentoId;
        const transacaoId = botao.dataset.transacaoId;

        if (!agendamentoId || !transacaoId) {
            this.mostrarToast('erro', 'Dados da conciliação não encontrados.');
            return;
        }

        const dadosTransacao = this.extrairDadosTransacao(transacaoId);
        const dadosAgendamento = this.extrairDadosAgendamento(botao);

        if (!dadosTransacao || !dadosAgendamento) {
            this.mostrarToast('erro', 'Erro ao carregar dados para conciliação.');
            return;
        }

        this.dadosConciliacao = {
            transacao_id: transacaoId,
            agendamento_id: agendamentoId,
            transacao: dadosTransacao,
            agendamento: dadosAgendamento
        };

        this.preencherModal();
        
        this.modal.show();
    }

    extrairDadosTransacao(transacaoId) {
        
        const cardTransacao = document.querySelector(`.conciliacao-ofx-id-${transacaoId} .card[data-transacao-id]`);
        if (!cardTransacao) {
            console.error(`Card da transação ${transacaoId} não encontrado`);
            return null;
        }

        const isParcial = cardTransacao.dataset.conciliacaoParcial === 'true';
        const valor = isParcial 
            ? (cardTransacao.dataset.transacaoValorDisponivel || cardTransacao.dataset.transacaoValor || '-')
            : (cardTransacao.dataset.transacaoValor || '-');

        return {
            valor: valor,
            valorOriginal: cardTransacao.dataset.transacaoValor || '-',
            valorDisponivel: cardTransacao.dataset.transacaoValorDisponivel || cardTransacao.dataset.transacaoValor || '-',
            isParcial: isParcial,
            data: cardTransacao.dataset.transacaoData || '-', 
            descricao: cardTransacao.dataset.transacaoDescricao || '-',
            fitid: cardTransacao.dataset.transacaoFitid || '-'
        };
    }

    extrairDadosAgendamento(botao) {
        const card = botao.closest('.sugestao-card');
        if (!card) return null;

        const valor = card.querySelector('.valor-sugestao strong')?.textContent || '-';
        const vencimento = card.querySelector('.data-sugestao strong')?.textContent || '-';
        const pessoa = card.querySelector('.beneficiario-sugestao strong')?.textContent || '-';
        const origem = card.querySelector('.badge')?.textContent || '-';
        
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

    preencherModal() {
        const { transacao, agendamento } = this.dadosConciliacao;

        document.getElementById('modal-transacao-valor').textContent = transacao.valor;
        document.getElementById('modal-transacao-data').textContent = transacao.data;
        document.getElementById('modal-transacao-descricao').textContent = transacao.descricao;
        document.getElementById('modal-transacao-fitid').textContent = transacao.fitid;

        document.getElementById('modal-agendamento-valor').textContent = agendamento.valor;
        document.getElementById('modal-agendamento-vencimento').textContent = agendamento.vencimento;
        document.getElementById('modal-agendamento-pessoa').textContent = agendamento.pessoa;
        document.getElementById('modal-agendamento-origem').textContent = agendamento.origem;

        this.preencherCategorias(agendamento.categorias);

    }

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

    converterValorParaNumero(valor) {
        return parseFloat(
            valor.replace('R$', '')
                 .replace(/\./g, '')
                 .replace(',', '.')
                 .trim()
        ) || 0;
    }

    async confirmarConciliacao() {
        if (!this.dadosConciliacao) {
            this.mostrarToast('erro', 'Dados da conciliação perdidos.');
            return;
        }

        const btnConfirmar = document.getElementById('btn-confirmar-conciliacao');
        const spinner = btnConfirmar.querySelector('.spinner-border');
        const texto = btnConfirmar.querySelector('.btn-text');

        try {
            
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

            this.esconderToast('loading');

            if (data.success) {
                
                this.mostrarToast('sucesso', data.message);
                this.modal.hide();
                
                setTimeout(() => window.location.reload(), 1500);
            } else {
                
                this.mostrarToast('erro', data.message || 'Erro ao processar conciliação.');
            }

        } catch (error) {
            console.error('Erro na conciliação:', error);
            this.esconderToast('loading');
            this.mostrarToast('erro', 'Erro de comunicação com o servidor.');
        } finally {
            
            btnConfirmar.disabled = false;
            spinner.classList.add('d-none');
            texto.textContent = 'Confirmar Conciliação';
        }
    }

    removerTransacaoCompletaComEfeito(transacaoId) {
        
        const linhaTransacao = document.querySelector(`.conciliacao-ofx-id-${transacaoId}`);
        if (!linhaTransacao) {
            console.warn(`[Conciliação] Linha da transação ${transacaoId} não encontrada`);
            return;
        }

        linhaTransacao.style.transition = 'all 0.5s ease-out';
        linhaTransacao.style.transform = 'scale(1.02)';
        linhaTransacao.style.backgroundColor = '#d4edda';
        linhaTransacao.style.borderRadius = '8px';
        linhaTransacao.style.padding = '10px';
        linhaTransacao.style.boxShadow = '0 4px 15px rgba(40, 167, 69, 0.4)';

        const todosCards = linhaTransacao.querySelectorAll('.card');
        todosCards.forEach(card => {
            card.style.transition = 'all 0.5s ease-out';
            card.style.borderColor = '#28a745';
            card.style.backgroundColor = '#f8f9fa';
        });

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
            
            linhaTransacao.style.transition = 'all 0.6s ease-in';
            linhaTransacao.style.opacity = '0';
            linhaTransacao.style.transform = 'scale(0.95) translateY(-30px)';
            
            setTimeout(() => {
                
                const alturaAtual = linhaTransacao.offsetHeight;
                
                linhaTransacao.style.transition = 'all 0.5s ease-in-out';
                linhaTransacao.style.height = alturaAtual + 'px';
                linhaTransacao.style.overflow = 'hidden';
                
                linhaTransacao.offsetHeight;
                
                linhaTransacao.style.height = '0px';
                linhaTransacao.style.padding = '0';
                linhaTransacao.style.margin = '0';
                
                setTimeout(() => {
                    linhaTransacao.remove();
                    
                    this.verificarPaginaVazia();
                }, 500);
            }, 600);
        }, 600);
    }

    verificarPaginaVazia() {
        const transacoesRestantes = document.querySelectorAll('.row.row-cards[class*="conciliacao-ofx-id-"]');
        
        if (transacoesRestantes.length === 0) {
            
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
                
                const mensagensFlash = container.querySelector('.alert');
                if (mensagensFlash) {
                    mensagensFlash.after(mensagemVazia);
                } else {
                    container.appendChild(mensagemVazia);
                }
            }
        }
    }

    removerAgendamentoDeTodasSugestoes(agendamentoId) {
        
        const botoesConciliacao = document.querySelectorAll(`.btn-conciliar-sugestao[data-agendamento-id="${agendamentoId}"]`);
        
        botoesConciliacao.forEach((botao, index) => {
            
            const cardSugestao = botao.closest('.sugestao-card') || botao.closest('.card') || botao.closest('.col-12');
            
            if (cardSugestao) {
                
                cardSugestao.style.transition = 'opacity 0.3s ease-out';
                cardSugestao.style.opacity = '0';
                
                setTimeout(() => {
                    cardSugestao.remove();
                }, 300);
            }
        });
        
        if (botoesConciliacao.length > 0) {
            setTimeout(() => {
                this.verificarTabsVazias();
            }, 400);
        }
    }

    verificarTabsVazias() {
        
        const tabsSugestao = document.querySelectorAll('[id*="tabs-sugestao-"]');
        
        tabsSugestao.forEach(tab => {
            const sugestoesRestantes = tab.querySelectorAll('.sugestao-card, .card[data-agendamento-id]');
            
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

    mostrarToast(tipo, mensagem) {
        const toastId = `toast-conciliacao-${tipo}`;
        const toastElement = document.getElementById(toastId);
        
        if (!toastElement) return;

        if (tipo !== 'loading') {
            const detalhes = toastElement.querySelector(`#toast-conciliacao-${tipo === 'sucesso' ? 'detalhes' : 'erro-detalhes'}`);
            if (detalhes) {
                detalhes.textContent = mensagem;
            }
        }

        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }

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

document.addEventListener('DOMContentLoaded', () => {
    window.conciliacaoSugestoes = new ConciliacaoSugestoes();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConciliacaoSugestoes;
}