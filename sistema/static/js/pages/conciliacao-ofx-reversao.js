
class ConciliacaoReversao {
    constructor() {
        this.transacaoParaReverter = null;
        this.modalReversao = null;
        this.init();
    }

    init() {
        this.configurarEventos();
        this.inicializarModal();
    }

    configurarEventos() {
        
        const checkboxConfirmacao = document.getElementById('confirmarReversao');
        if (checkboxConfirmacao) {
            checkboxConfirmacao.addEventListener('change', (e) => {
                const btnConfirmar = document.getElementById('btnConfirmarReversao');
                if (btnConfirmar) {
                    btnConfirmar.disabled = !e.target.checked;
                }
            });
        }

        const btnConfirmar = document.getElementById('btnConfirmarReversao');
        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', () => {
                this.confirmarReversao();
            });
        }

        const modal = document.getElementById('modalReverterConciliacao');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                this.limparDadosModal();
            });
        }
    }

    inicializarModal() {
        const modalElement = document.getElementById('modalReverterConciliacao');
        if (modalElement) {
            this.modalReversao = new bootstrap.Modal(modalElement);
        }
    }

    abrirModalReversao(transacaoId, fitid, valorFormatado, dataTransacao = null) {
        
        this.transacaoParaReverter = {
            id: transacaoId,
            fitid: fitid,
            valorFormatado: valorFormatado,
            dataTransacao: dataTransacao
        };

        this.preencherInformacoesTransacao();

        this.resetarModal();

        if (this.modalReversao) {
            this.modalReversao.show();
        }

        this.carregarDetalhesConciliacao();
    }

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

    resetarModal() {
        
        const checkbox = document.getElementById('confirmarReversao');
        if (checkbox) {
            checkbox.checked = false;
        }

        const btnConfirmar = document.getElementById('btnConfirmarReversao');
        if (btnConfirmar) {
            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = `
                <i class="fas fa-undo me-2"></i>Confirmar Reversão
            `;
        }

        this.mostrarCarregando();
    }

    mostrarCarregando() {
        
        const conteudo = document.getElementById('reverterConteudo');
        const erro = document.getElementById('reverterErro');
        const carregando = document.getElementById('reverterCarregando');

        if (conteudo) conteudo.style.display = 'none';
        if (erro) erro.style.display = 'none';
        if (carregando) carregando.style.display = 'block';
    }

    mostrarConteudo() {
        const conteudo = document.getElementById('reverterConteudo');
        const erro = document.getElementById('reverterErro');
        const carregando = document.getElementById('reverterCarregando');

        if (conteudo) conteudo.style.display = 'block';
        if (erro) erro.style.display = 'none';
        if (carregando) carregando.style.display = 'none';
    }

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

    async carregarDetalhesConciliacao() {
        if (!this.transacaoParaReverter) return;

        try {

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

    exibirDetalhesConciliacao(detalhes) {
        
        const elemTipoConciliacao = document.getElementById('reverterTipoConciliacao');
        const elemDataConciliacao = document.getElementById('reverterDataConciliacao');
        const elemObservacoes = document.getElementById('reverterObservacoes');

        if (elemTipoConciliacao) {
            elemTipoConciliacao.textContent = detalhes.tipo_conciliacao || 'Não especificado';
        }

        if (elemDataConciliacao) {
            elemDataConciliacao.textContent = detalhes.data_conciliacao || 'N/A';
        }

        this.preencherAgendamentos(detalhes.agendamentos);

        this.preencherMovimentacoes(detalhes.movimentacoes);

        this.mostrarConteudo();
    }

    preencherAgendamentos(agendamentos) {
        const container = document.getElementById('reverterAgendamentosContainer');
        const lista = document.getElementById('reverterAgendamentosList');

        if (!agendamentos || agendamentos.length === 0) {
            if (container) container.style.display = 'none';
            return;
        }

        if (container) container.style.display = 'block';
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

    exibirErroCarregamento(mensagem) {
        this.mostrarErro(mensagem || 'Erro ao carregar detalhes da conciliação');
    }

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

    exibirSucessoReversao(mensagem) {

        if (this.modalReversao) {
            this.modalReversao.hide();
        }

        const modalSucesso = new bootstrap.Modal(document.getElementById('modal-reversao-sucesso'));
        modalSucesso.show();

        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }

    exibirErroReversao(mensagem) {
        console.error('[ReversaoOFX] Erro na reversão:', mensagem);

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

        const mensagemErro = document.getElementById('mensagem-erro-reversao');
        if (mensagemErro) {
            mensagemErro.textContent = mensagem;
        }

        const modalErro = new bootstrap.Modal(document.getElementById('modal-reversao-erro'));
        modalErro.show();
    }

    mostrarToast(tipo, mensagem) {
        
        if (window.mostrarToast) {
            window.mostrarToast(tipo, mensagem);
            return;
        }

        alert(`${tipo.toUpperCase()}: ${mensagem}`);
    }

    limparDadosModal() {
        this.transacaoParaReverter = null;

        const elementos = ['reverterDataTransacao', 'reverterValorTransacao', 'reverterDescricaoTransacao', 'reverterFitidTransacao'];
        elementos.forEach(id => {
            const elemento = document.getElementById(id);
            if (elemento) {
                elemento.textContent = '-';
            }
        });

        const checkbox = document.getElementById('confirmarReversao');
        if (checkbox) {
            checkbox.checked = false;
        }

        const containers = ['reverterAgendamentosContainer', 'reverterMovimentacoesContainer', 'reverterObservacoesContainer'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.style.display = 'none';
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    
    window.conciliacaoReversao = new ConciliacaoReversao();
    
    window.abrirModalReversao = function(transacaoId, fitid, valorFormatado, dataTransacao) {
        if (window.conciliacaoReversao) {
            window.conciliacaoReversao.abrirModalReversao(transacaoId, fitid, valorFormatado, dataTransacao);
        } else {
            console.error('[ReversaoOFX] Gerenciador não inicializado');
        }
    };

});