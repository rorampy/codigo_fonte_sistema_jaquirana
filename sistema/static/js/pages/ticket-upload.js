/**
 * Upload e extração de dados de tickets
 * Usa spinner inline ao invés de modal para loading
 */

(() => {
  'use strict';

  // Elementos do DOM
  const elementos = {
    inputArquivo: null,
    botaoEnviar: null,
    textoBotaoOriginal: '',
    containerSpinner: null,
    campos: {}
  };

  // Controle de estado
  let estaProcessando = false;

  // Inicialização
  const inicializar = () => {
    cachearElementos();
    criarContainerSpinner();
    criarModais();
    vincularEventos();
  };

  // Faz cache dos elementos do DOM
  const cachearElementos = () => {
    elementos.inputArquivo = document.querySelector('input[name="arquivoTicket"]');
    elementos.botaoEnviar = document.querySelector('button[type="submit"]');
    elementos.textoBotaoOriginal = elementos.botaoEnviar?.innerHTML || '';
    elementos.campos = {
      numeroNf: document.querySelector('input[name="numeroNf"]'),
      pesoLiquido: document.querySelector('input[name="pesoLiquido"]'),
      dataEntrega: document.querySelector('input[name="dataEntregaTicket"]'),
      placa: document.querySelector('input[name="placaVeiculo"]')
    };
  };

  // Cria o loader fullscreen (overlay escuro com spinner)
  const criarContainerSpinner = () => {
    const loader = document.createElement('div');
    loader.id = 'ticket-loader';
    loader.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.8);
      z-index: 10000;
      display: none;
      justify-content: center;
      align-items: center;
    `;
    loader.innerHTML = `
      <div class="text-center">
        <div class="spinner-border text-light" style="width: 3rem; height: 3rem;"></div>
        <div class="text-white mt-3">Processando Ticket...</div>
        <div class="text-white-50 small mt-1">Extraindo dados automaticamente</div>
      </div>
    `;
    document.body.appendChild(loader);
    elementos.containerSpinner = loader;
  };

  // Cria os modais de resultado (sucesso, aviso, erro)
  const criarModais = () => {
    const html = `
      <!-- Modal Sucesso -->
      <div class="modal modal-blur fade" id="modal-sucesso" tabindex="-1">
        <div class="modal-dialog modal-sm modal-dialog-centered">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            <div class="modal-status bg-success"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" class="text-success mb-2">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M9 12l2 2l4 -4" />
              </svg>
              <h3>Dados Extraídos com Sucesso!</h3>
              <div id="sucesso-conteudo" class="text-secondary"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-success w-100" data-bs-dismiss="modal">Continuar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Aviso -->
      <div class="modal modal-blur fade" id="modal-aviso" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            <div class="modal-status bg-warning"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" class="text-warning mb-2">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M12 8l0 4" /><path d="M12 16l.01 0" />
              </svg>
              <h3>Extração Parcial</h3>
              <div id="aviso-conteudo" class="text-secondary"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn w-100" data-bs-dismiss="modal">Entendido - Preencher Manualmente</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Erro Qualidade -->
      <div class="modal modal-blur fade" id="modal-erro-qualidade" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            <div class="modal-status bg-danger"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" class="text-danger mb-2">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M10 10l4 4m0 -4l-4 4" />
              </svg>
              <h3>Qualidade de Imagem Inadequada</h3>
              <div id="erro-qualidade-conteudo" class="text-secondary text-start"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn w-100" data-bs-dismiss="modal">Preencher Manualmente</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Erro Genérico -->
      <div class="modal modal-blur fade" id="modal-erro" tabindex="-1">
        <div class="modal-dialog modal-sm modal-dialog-centered">
          <div class="modal-content">
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            <div class="modal-status bg-danger"></div>
            <div class="modal-body text-center py-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" class="text-danger mb-2">
                <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
                <path d="M10 10l4 4m0 -4l-4 4" />
              </svg>
              <h3>Erro ao Processar Ticket</h3>
              <div id="erro-conteudo" class="text-secondary"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-danger w-100" data-bs-dismiss="modal">Entendido</button>
            </div>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
  };

  // Vincula eventos aos elementos
  const vincularEventos = () => {
    if (!elementos.inputArquivo) return;
    elementos.inputArquivo.addEventListener('change', aoSelecionarArquivo);
  };

  // Executado quando usuário seleciona um arquivo
  const aoSelecionarArquivo = async (evento) => {
    const arquivo = evento.target.files[0];
    if (!arquivo || estaProcessando) return;

    const tiposPermitidos = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!tiposPermitidos.includes(arquivo.type)) {
      exibirErro('Arquivo deve estar em formato JPG, JPEG ou PNG.');
      evento.target.value = '';
      return;
    }

    await processarTicket(arquivo);
  };

  // Processa o ticket enviando para a API
  const processarTicket = async (arquivo) => {
    estaProcessando = true;
    exibirSpinner();
    limparCampos();

    const dadosFormulario = new FormData();
    dadosFormulario.append('arquivo', arquivo);

    try {
      const resposta = await fetch('/api/processar-ticket', {
        method: 'POST',
        body: dadosFormulario
      });

      esconderSpinner();

      if (!resposta.ok) {
        const mensagemErro = await obterMensagemErroHttp(resposta);
        exibirErro(mensagemErro);
        return;
      }

      const dados = await resposta.json();

      if (dados.sucesso) {
        preencherCampos(dados.dados);
        exibirSucesso(dados);
      } else {
        tratarErroApi(dados);
      }

    } catch (erro) {
      esconderSpinner();
      console.error('Erro:', erro);
      exibirErro('Erro ao processar ticket. Verifique sua conexão.');
    } finally {
      estaProcessando = false;
    }
  };

  // Exibe o loader fullscreen
  const exibirSpinner = () => {
    if (elementos.containerSpinner) {
      elementos.containerSpinner.style.display = 'flex';
    }
    if (elementos.botaoEnviar) {
      elementos.botaoEnviar.disabled = true;
    }
  };

  // Esconde o loader fullscreen
  const esconderSpinner = () => {
    if (elementos.containerSpinner) {
      elementos.containerSpinner.style.display = 'none';
    }
    if (elementos.botaoEnviar) {
      elementos.botaoEnviar.disabled = false;
    }
  };

  // Limpa todos os campos do formulário
  const limparCampos = () => {
    Object.values(elementos.campos).forEach(campo => {
      if (campo) campo.value = '';
    });
  };

  // Preenche os campos com os dados extraídos
  const preencherCampos = (dados) => {
    if (dados.numero_nf && elementos.campos.numeroNf) {
      elementos.campos.numeroNf.value = dados.numero_nf;
    }
    if (dados.peso_liquido && elementos.campos.pesoLiquido) {
      elementos.campos.pesoLiquido.value = parseFloat(dados.peso_liquido).toFixed(2);
    }
    if (dados.data_entrega && elementos.campos.dataEntrega) {
      elementos.campos.dataEntrega.value = dados.data_entrega;
    }
    if (dados.placa && elementos.campos.placa) {
      elementos.campos.placa.value = dados.placa;
    }
  };

  // Obtém mensagem de erro baseada no código HTTP
  const obterMensagemErroHttp = async (resposta) => {
    try {
      const dados = await resposta.json();
      return dados.mensagem || 'Erro ao processar ticket.';
    } catch {
      const mensagens = {
        502: 'Servidor temporariamente indisponível.',
        507: 'Servidor sem memória. Tente imagem menor.',
        413: 'Arquivo muito grande (máximo 10MB).'
      };
      return mensagens[resposta.status] || `Erro no servidor (${resposta.status}).`;
    }
  };

  // Trata erros retornados pela API
  const tratarErroApi = (dados) => {
    if (dados.erro === 'QUALIDADE_IMAGEM_INSUFICIENTE') {
      exibirErroQualidade(dados);
    } else if (dados.erro === 'EXTRACAO_INCOMPLETA') {
      preencherCampos(dados.dados);
      exibirAviso(dados);
    } else {
      exibirErro(dados.mensagem || 'Erro desconhecido.');
    }
  };

  // Gera HTML com lista dos campos extraídos
  const construirHtmlCamposExtraidos = (listaCampos) => {
    let html = '<div class="row g-2">';
    listaCampos.forEach(campo => {
      html += `
        <div class="col-6">
          <div class="d-flex align-items-center text-success">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" 
              fill="none" stroke="currentColor" stroke-width="2" class="me-2">
              <circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/>
            </svg>
            <span class="fw-medium">${campo}</span>
          </div>
        </div>`;
    });
    html += '</div>';
    return html;
  };

  // Exibe modal de sucesso
  const exibirSucesso = (dados) => {
    const camposExtraidos = [];
    if (dados.dados.numero_nf) camposExtraidos.push('Número NF');
    if (dados.dados.peso_liquido) camposExtraidos.push('Peso Líquido');
    if (dados.dados.data_entrega) camposExtraidos.push('Data de Entrega');
    if (dados.dados.placa) camposExtraidos.push('Placa');

    let html = 'Os seguintes dados foram extraídos automaticamente:<br><br>';
    html += construirHtmlCamposExtraidos(camposExtraidos);

    if (dados.campos_faltantes?.length > 0) {
      html += `<br><div class="alert alert-warning mb-0 mt-3">
        <strong>⚠️ Atenção:</strong><br>
        Não foi possível extrair: ${dados.campos_faltantes.join(', ')}<br>
        <small>Preencha manualmente os campos faltantes.</small>
      </div>`;
    }

    document.getElementById('sucesso-conteudo').innerHTML = html;
    new bootstrap.Modal(document.getElementById('modal-sucesso')).show();
  };

  // Exibe modal de aviso (extração parcial)
  const exibirAviso = (dados) => {
    let html = `<div class="alert alert-warning mb-3">${dados.mensagem}</div>`;
    
    const camposExtraidos = [];
    if (dados.dados?.numero_nf) camposExtraidos.push('Número NF');
    if (dados.dados?.peso_liquido) camposExtraidos.push('Peso Líquido');
    if (dados.dados?.data_entrega) camposExtraidos.push('Data de Entrega');
    if (dados.dados?.placa) camposExtraidos.push('Placa');

    if (camposExtraidos.length > 0) {
      html += '<p class="mb-2 fw-bold">Dados extraídos com sucesso:</p>';
      html += construirHtmlCamposExtraidos(camposExtraidos);
    }

    html += `<div class="alert alert-info mb-0 mt-3">
      <strong>Próximos passos:</strong><br>
      Preencha manualmente os campos que não foram extraídos.
    </div>`;

    document.getElementById('aviso-conteudo').innerHTML = html;
    new bootstrap.Modal(document.getElementById('modal-aviso')).show();
  };

  // Exibe modal de erro de qualidade de imagem
  const exibirErroQualidade = (dados) => {
    const html = `
      <p><strong>${dados.mensagem}</strong></p>
      <hr>
      <p class="mb-2"><strong>Dicas para melhorar:</strong></p>
      <ul class="text-start">
        <li>Foto mais próxima do documento</li>
        <li>Boa iluminação</li>
        <li>Evite sombras</li>
        <li>Mantenha câmera estável</li>
        <li>Limpe a lente</li>
      </ul>`;

    document.getElementById('erro-qualidade-conteudo').innerHTML = html;
    new bootstrap.Modal(document.getElementById('modal-erro-qualidade')).show();
  };

  // Exibe modal de erro genérico
  const exibirErro = (mensagem) => {
    document.getElementById('erro-conteudo').innerHTML = mensagem;
    new bootstrap.Modal(document.getElementById('modal-erro')).show();
  };

  // Inicia quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
  } else {
    inicializar();
  }

})();
