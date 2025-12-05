/**
 * Módulo para processamento de upload e extração de dados de tickets
 * @module ticket-upload
 */

class TicketUploadManager {
  constructor() {
    this.arquivoInput = document.querySelector('input[name="arquivoTicket"]');
    this.btnCadastrar = document.querySelector('button[type="submit"]');
    this.textoOriginalBtn = this.btnCadastrar?.innerHTML;
    this.init();
  }

  init() {
    if (this.arquivoInput) {
      this.arquivoInput.addEventListener('change', (e) => this.handleFileChange(e));
    }
    this.criarModais();
  }

  criarModais() {
    const modaisHTML = `
      <!-- Loader OCR -->
      <div id="loader-ocr" class="modal modal-blur fade" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" style="display: none;">
        <div class="modal-dialog modal-sm modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-body text-center py-5">
              <div class="mb-3">
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                  <span class="visually-hidden">Processando...</span>
                </div>
              </div>
              <h3 class="mb-2">Processando Ticket</h3>
              <p class="text-secondary mb-0">Extraindo dados automaticamente...</p>
              <small class="text-muted">Isso pode levar alguns segundos</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Sucesso -->
      <div class="modal modal-blur fade" id="modal-ticket-sucesso" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            <div class="modal-status bg-success"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="icon mb-2 text-green icon-lg">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M9 12l2 2l4 -4" />
              </svg>
              <h3>Dados Extraídos com Sucesso!</h3>
              <div class="text-secondary" id="mensagem-sucesso-conteudo"></div>
            </div>
            <div class="modal-footer">
              <div class="w-100">
                <button class="btn btn-success w-100" data-bs-dismiss="modal">
                  Continuar
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Aviso (Extração Parcial) -->
      <div class="modal modal-blur fade" id="modal-ticket-aviso" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered" role="document">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            <div class="modal-status bg-warning"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="icon mb-2 text-yellow icon-lg">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M12 8l0 4" />
                <path d="M12 16l.01 0" />
              </svg>
              <h3>Extração Parcial</h3>
              <div class="text-secondary" id="mensagem-aviso-conteudo"></div>
            </div>
            <div class="modal-footer">
              <div class="w-100">
                <button class="btn w-100" data-bs-dismiss="modal">
                  Entendido - Preencher Manualmente
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Erro (Qualidade Insuficiente) -->
      <div class="modal modal-blur fade" id="modal-ticket-erro-qualidade" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered" role="document">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            <div class="modal-status bg-danger"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="icon mb-2 text-red icon-lg">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M10 10l4 4m0 -4l-4 4" />
              </svg>
              <h3>Qualidade de Imagem Inadequada</h3>
              <div class="text-secondary text-start" id="mensagem-erro-qualidade-conteudo"></div>
            </div>
            <div class="modal-footer">
              <div class="w-100">
                <div class="row">
                  <div class="col">
                    <button class="btn w-100" data-bs-dismiss="modal">
                      Preencher Manualmente
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Erro Genérico -->
      <div class="modal modal-blur fade" id="modal-ticket-erro" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            <div class="modal-status bg-danger"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="icon mb-2 text-red icon-lg">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M10 10l4 4m0 -4l-4 4" />
              </svg>
              <h3>Erro ao Processar Ticket</h3>
              <div class="text-secondary" id="mensagem-erro-conteudo"></div>
            </div>
            <div class="modal-footer">
              <div class="w-100">
                <button class="btn btn-danger w-100" data-bs-dismiss="modal">
                  Entendido
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modaisHTML);
  }

  handleFileChange(e) {
    const arquivo = e.target.files[0];
    if (!arquivo) return;

    if (!this.validarTipoArquivo(arquivo)) {
      this.mostrarErro('Arquivo deve estar em formato JPG, JPEG ou PNG.');
      e.target.value = '';
      return;
    }

    // Limpar campos antes de processar novo arquivo
    this.limparCampos();
    
    this.processarTicket(arquivo);
  }

  validarTipoArquivo(arquivo) {
    const tiposPermitidos = ['image/jpeg', 'image/png', 'image/jpg'];
    return tiposPermitidos.includes(arquivo.type);
  }

  limparCampos() {
    const campoNumeroNf = document.querySelector('input[name="numeroNf"]');
    const campoPesoLiquido = document.querySelector('input[name="pesoLiquido"]');
    const campoDataEntrega = document.querySelector('input[name="dataEntregaTicket"]');
    const campoPlaca = document.querySelector('input[name="placaVeiculo"]');
    
    if (campoNumeroNf) campoNumeroNf.value = '';
    if (campoPesoLiquido) campoPesoLiquido.value = '';
    if (campoDataEntrega) campoDataEntrega.value = '';
    if (campoPlaca) campoPlaca.value = '';
  }

  mostrarCarregamento() {
    // Desabilitar botão de cadastrar
    if (this.btnCadastrar) {
      this.btnCadastrar.disabled = true;
      this.btnCadastrar.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processando ticket...';
    }
    
    // Mostrar modal de loader
    const loaderModal = new bootstrap.Modal(document.getElementById('loader-ocr'));
    this.loaderModal = loaderModal;
    loaderModal.show();
  }

  esconderCarregamento() {
    // Reabilitar botão de cadastrar
    if (this.btnCadastrar) {
      this.btnCadastrar.disabled = false;
      this.btnCadastrar.innerHTML = this.textoOriginalBtn;
    }
    
    // Esconder modal de loader
    if (this.loaderModal) {
      this.loaderModal.hide();
      this.loaderModal = null;
    }
  }

  async processarTicket(arquivo) {
    this.mostrarCarregamento();

    const formData = new FormData();
    formData.append('arquivo', arquivo);

    try {
      const response = await fetch('/api/processar-ticket', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.sucesso) {
        this.preencherCampos(data.dados);
        this.mostrarSucesso(data);
      } else {
        this.tratarErro(data);
      }
    } catch (error) {
      console.error('Erro:', error);
      this.mostrarErro('Erro ao processar ticket. Verifique sua conexão e tente novamente.');
    } finally {
      this.esconderCarregamento();
    }
  }

  preencherCampos(dados) {
    if (dados.numero_nf) {
      document.querySelector('input[name="numeroNf"]').value = dados.numero_nf;
    }
    if (dados.peso_liquido) {
      document.querySelector('input[name="pesoLiquido"]').value = parseFloat(dados.peso_liquido).toFixed(2);
    }
    if (dados.data_entrega) {
      document.querySelector('input[name="dataEntregaTicket"]').value = dados.data_entrega;
    }
    if (dados.placa) {
      document.querySelector('input[name="placaVeiculo"]').value = dados.placa;
    }
  }

  mostrarSucesso(data) {
    let mensagem = 'Os seguintes dados foram extraídos automaticamente:<br><br>';
    
    const camposExtraidos = [];
    if (data.dados.numero_nf) camposExtraidos.push('Número NF');
    if (data.dados.peso_liquido) camposExtraidos.push('Peso Líquido');
    if (data.dados.data_entrega) camposExtraidos.push('Data de Entrega');
    if (data.dados.placa) camposExtraidos.push('Placa');
    
    // Layout em grid com ícones de check
    mensagem += '<div class="row g-2">';
    camposExtraidos.forEach(campo => {
      mensagem += `
        <div class="col-6">
          <div class="d-flex align-items-center text-success">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
              class="me-2" style="min-width: 20px;">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9 12l2 2 4-4"/>
            </svg>
            <span class="fw-medium">${campo}</span>
          </div>
        </div>
      `;
    });
    mensagem += '</div>';

    if (data.campos_faltantes && data.campos_faltantes.length > 0) {
      mensagem += '<br><div class="alert alert-warning mb-0 mt-3" role="alert">';
      mensagem += '<strong>⚠️ Atenção:</strong><br>Não foi possível extrair: ' + data.campos_faltantes.join(', ');
      mensagem += '<br><small>Preencha manualmente os campos faltantes.</small>';
      mensagem += '</div>';
    }

    document.getElementById('mensagem-sucesso-conteudo').innerHTML = mensagem;
    const modal = new bootstrap.Modal(document.getElementById('modal-ticket-sucesso'));
    modal.show();
  }

  tratarErro(data) {
    if (data.erro === 'QUALIDADE_IMAGEM_INSUFICIENTE') {
      this.mostrarErroQualidade(data);
    } else if (data.erro === 'EXTRACAO_INCOMPLETA') {
      this.preencherCampos(data.dados);
      this.mostrarAviso(data);
    } else {
      this.mostrarErro(data.mensagem || 'Erro desconhecido ao processar ticket.');
    }
  }

  mostrarErroQualidade(data) {
    let mensagem = `<p><strong>${data.mensagem}</strong></p>`;
    mensagem += '<hr>';
    mensagem += '<p class="mb-2"><strong>Dicas para melhorar a qualidade:</strong></p>';
    mensagem += '<ul class="text-start">';
    mensagem += '<li>Tire a foto mais próxima do documento</li>';
    mensagem += '<li>Certifique-se de ter boa iluminação</li>';
    mensagem += '<li>Evite sombras sobre o documento</li>';
    mensagem += '<li>Mantenha a câmera estável (evite tremor)</li>';
    mensagem += '<li>Limpe a lente da câmera</li>';
    mensagem += '</ul>';

    document.getElementById('mensagem-erro-qualidade-conteudo').innerHTML = mensagem;
    const modal = new bootstrap.Modal(document.getElementById('modal-ticket-erro-qualidade'));
    modal.show();
  }

  mostrarAviso(data) {
    let mensagem = `<div class="alert alert-warning mb-3" role="alert">${data.mensagem}</div>`;
    
    if (data.dados) {
      mensagem += '<p class="mb-2 fw-bold">Dados extraídos com sucesso:</p>';
      
      const dadosExtraidos = [];
      if (data.dados.numero_nf) dadosExtraidos.push('Número NF');
      if (data.dados.peso_liquido) dadosExtraidos.push('Peso Líquido');
      if (data.dados.data_entrega) dadosExtraidos.push('Data de Entrega');
      if (data.dados.placa) dadosExtraidos.push('Placa');
      
      mensagem += '<div class="row g-2 mb-3">';
      dadosExtraidos.forEach(campo => {
        mensagem += `
          <div class="col-6">
            <div class="d-flex align-items-center text-success">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
                class="me-2" style="min-width: 20px;">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
              <span class="fw-medium">${campo}</span>
            </div>
          </div>
        `;
      });
      mensagem += '</div>';
    }
    
    mensagem += '<div class="alert alert-info mb-0" role="alert">';
    mensagem += '<strong>Próximos passos:</strong><br>';
    mensagem += 'Preencha manualmente os campos que não foram extraídos.';
    mensagem += '</div>';

    document.getElementById('mensagem-aviso-conteudo').innerHTML = mensagem;
    const modal = new bootstrap.Modal(document.getElementById('modal-ticket-aviso'));
    modal.show();
  }

  mostrarErro(mensagem) {
    document.getElementById('mensagem-erro-conteudo').innerHTML = mensagem;
    const modal = new bootstrap.Modal(document.getElementById('modal-ticket-erro'));
    modal.show();
  }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  new TicketUploadManager();
});
