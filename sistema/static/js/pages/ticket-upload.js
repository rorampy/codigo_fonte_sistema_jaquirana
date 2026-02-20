
(() => {
  'use strict';

  let arquivoSelecionado = null;
  let imagemBase64 = null;
  let estaProcessando = false;

  const elementos = {
    
    areaUploadInicial: null,
    areaFormulario: null,
    rodapeFormulario: null,

    modalUpload: null,
    dropZone: null,
    dropZoneConteudo: null,
    dropZonePreview: null,
    inputUploadModal: null,
    imagemPreview: null,
    nomeArquivo: null,
    btnProcessarUpload: null,

    modalVisualizarImagem: null,
    imagemVisualizacao: null,

    modalConfirmacao: null,
    btnConfirmarCadastro: null,

    btnAlterarImagem: null,
    btnConfirmar: null,

    campos: {},

    formTicket: null,
    arquivoTicket: null,

    loaderFullscreen: null
  };

  const inicializar = () => {
    cachearElementos();
    criarLoaderFullscreen();
    vincularEventos();
  };

  const cachearElementos = () => {
    
    elementos.areaUploadInicial = document.getElementById('areaUploadInicial');
    elementos.areaFormulario = document.getElementById('areaFormulario');
    elementos.rodapeFormulario = document.getElementById('rodapeFormulario');

    elementos.modalUpload = document.getElementById('modalUpload');
    elementos.dropZone = document.getElementById('dropZone');
    elementos.dropZoneConteudo = document.getElementById('dropZoneConteudo');
    elementos.dropZonePreview = document.getElementById('dropZonePreview');
    elementos.inputUploadModal = document.getElementById('inputUploadModal');
    elementos.imagemPreview = document.getElementById('imagemPreview');
    elementos.nomeArquivo = document.getElementById('nomeArquivo');
    elementos.btnProcessarUpload = document.getElementById('btnProcessarUpload');

    elementos.imagemTicketDireta = document.getElementById('imagemTicketDireta');

    elementos.imagemMiniatura = document.getElementById('imagemMiniatura');

    elementos.modalConfirmacao = document.getElementById('modalConfirmacao');
    elementos.btnConfirmarCadastro = document.getElementById('btnConfirmarCadastro');
    elementos.confirmaImagemTicket = document.getElementById('confirma-imagem-ticket');

    elementos.btnAlterarImagem = document.getElementById('btnAlterarImagem');
    elementos.btnConfirmar = document.getElementById('btnConfirmar');

    elementos.campos = {
      numeroNf: document.getElementById('numeroNf'),
      pesoLiquido: document.getElementById('pesoLiquido'),
      dataEntrega: document.getElementById('dataEntregaTicket')
    };

    elementos.formTicket = document.getElementById('formTicket');
    elementos.arquivoTicket = document.getElementById('arquivoTicket');
  };

  const criarLoaderFullscreen = () => {
    const loader = document.createElement('div');
    loader.id = 'ticket-loader';
    loader.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.85);
      z-index: 10000;
      display: none;
      justify-content: center;
      align-items: center;
    `;
    loader.innerHTML = `
      <div class="text-center">
        <div class="spinner-border text-light" style="width: 3rem; height: 3rem;"></div>
        <div class="text-white mt-3 fs-4">Processando Ticket...</div>
        <div class="text-white-50 mt-1">Extraindo dados automaticamente</div>
      </div>
    `;
    document.body.appendChild(loader);
    elementos.loaderFullscreen = loader;
  };

  const vincularEventos = () => {
    
    if (elementos.dropZone) {
      elementos.dropZone.addEventListener('click', () => {
        elementos.inputUploadModal.click();
      });

      elementos.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elementos.dropZone.style.borderColor = 'var(--tblr-success)';
        elementos.dropZone.style.background = 'var(--tblr-success-lt)';
      });

      elementos.dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elementos.dropZone.style.borderColor = 'var(--tblr-primary)';
        elementos.dropZone.style.background = 'var(--tblr-bg-surface-tertiary)';
      });

      elementos.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elementos.dropZone.style.borderColor = 'var(--tblr-primary)';
        elementos.dropZone.style.background = 'var(--tblr-bg-surface-tertiary)';

        const arquivo = e.dataTransfer.files[0];
        if (arquivo) {
          processarArquivoSelecionado(arquivo);
        }
      });
    }

    if (elementos.inputUploadModal) {
      elementos.inputUploadModal.addEventListener('change', (e) => {
        const arquivo = e.target.files[0];
        if (arquivo) {
          processarArquivoSelecionado(arquivo);
        }
      });
    }

    if (elementos.btnProcessarUpload) {
      elementos.btnProcessarUpload.addEventListener('click', processarUpload);
    }

    if (elementos.btnAlterarImagem) {
      elementos.btnAlterarImagem.addEventListener('click', abrirModalAlterarImagem);
    }

    if (elementos.btnConfirmar) {
      elementos.btnConfirmar.addEventListener('click', abrirModalConfirmacao);
    }

    if (elementos.btnConfirmarCadastro) {
      elementos.btnConfirmarCadastro.addEventListener('click', confirmarCadastro);
    }

    if (elementos.modalUpload) {
      elementos.modalUpload.addEventListener('hidden.bs.modal', () => {
        
        if (!arquivoSelecionado) {
          resetarModalUpload();
        }
      });
    }
  };

  const processarArquivoSelecionado = (arquivo) => {
    
    const tiposPermitidos = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!tiposPermitidos.includes(arquivo.type)) {
      exibirToast('Arquivo deve estar em formato JPG, JPEG ou PNG.', 'error');
      return;
    }

    if (arquivo.size > 10 * 1024 * 1024) {
      exibirToast('Arquivo deve ter no máximo 10MB.', 'error');
      return;
    }

    arquivoSelecionado = arquivo;

    const reader = new FileReader();
    reader.onload = (e) => {
      imagemBase64 = e.target.result;
      elementos.imagemPreview.src = imagemBase64;
      elementos.nomeArquivo.textContent = arquivo.name;

      elementos.dropZoneConteudo.classList.add('d-none');
      elementos.dropZonePreview.classList.remove('d-none');

      elementos.btnProcessarUpload.disabled = false;
    };
    reader.readAsDataURL(arquivo);
  };

  const processarUpload = async () => {
    if (!arquivoSelecionado || estaProcessando) return;

    estaProcessando = true;

    const modalUploadInstance = bootstrap.Modal.getInstance(elementos.modalUpload);
    if (modalUploadInstance) {
      modalUploadInstance.hide();
    }

    exibirLoader();

    try {
      
      const formData = new FormData();
      formData.append('arquivo', arquivoSelecionado);

      const resposta = await fetch('/api/processar-ticket', {
        method: 'POST',
        body: formData
      });

      esconderLoader();

      if (!resposta.ok) {
        const erro = await resposta.json().catch(() => ({}));
        exibirToast(erro.mensagem || 'Erro ao processar ticket.', 'error');
        estaProcessando = false;
        return;
      }

      const dados = await resposta.json();

      if (dados.dados) {
        if (dados.dados.numero_nf && elementos.campos.numeroNf) {
          elementos.campos.numeroNf.value = dados.dados.numero_nf;
        }
        if (dados.dados.peso_liquido && elementos.campos.pesoLiquido) {
          elementos.campos.pesoLiquido.value = parseFloat(dados.dados.peso_liquido).toFixed(2);
        }
        if (dados.dados.data_entrega && elementos.campos.dataEntrega) {
          elementos.campos.dataEntrega.value = dados.dados.data_entrega;
        }
      }

      transferirArquivoParaInput();

      exibirFormulario();

      exibirToast('Imagem processada! Verifique os dados extraídos.', 'success');

    } catch (erro) {
      esconderLoader();
      console.error('Erro:', erro);
      exibirToast('Erro ao processar ticket. Verifique sua conexão.', 'error');
    }

    estaProcessando = false;
  };

  const transferirArquivoParaInput = () => {
    if (!arquivoSelecionado || !elementos.arquivoTicket) return;

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(arquivoSelecionado);
    elementos.arquivoTicket.files = dataTransfer.files;
    
    atualizarImagemDireta();
  };

  const atualizarImagemDireta = () => {
    const imagemSrc = imagemBase64 || window.imagemBase64;
    if (imagemSrc && elementos.imagemTicketDireta) {
      elementos.imagemTicketDireta.src = imagemSrc;
    }
  };

  const exibirFormulario = () => {
    elementos.areaUploadInicial.style.display = 'none';
    elementos.areaFormulario.style.display = 'block';
    elementos.rodapeFormulario.style.display = 'block';
  };

  const abrirModalAlterarImagem = () => {
    resetarModalUpload();
    const modal = new bootstrap.Modal(elementos.modalUpload);
    modal.show();
  };

  const resetarModalUpload = () => {
    elementos.dropZoneConteudo.classList.remove('d-none');
    elementos.dropZonePreview.classList.add('d-none');
    elementos.imagemPreview.src = '';
    elementos.nomeArquivo.textContent = 'Imagem selecionada';
    elementos.inputUploadModal.value = '';
    elementos.btnProcessarUpload.disabled = true;
    arquivoSelecionado = null;
    imagemBase64 = null;
  };

  const abrirModalConfirmacao = () => {
    
    const fornecedor = document.getElementById('fornecedorIdentificacao');
    const numeroNf = elementos.campos.numeroNf;
    const pesoLiquido = elementos.campos.pesoLiquido;
    const dataEntrega = elementos.campos.dataEntrega;
    const placaVeiculo = document.querySelector('input[name="placaVeiculo"]');
    const motorista = document.querySelector('input[name="motoristaTicket"]');

    let camposInvalidos = [];

    if (!fornecedor?.value) camposInvalidos.push('Fornecedor');
    if (!numeroNf?.value) camposInvalidos.push('Número NF');
    if (!pesoLiquido?.value) camposInvalidos.push('Peso Líquido');
    if (!dataEntrega?.value) camposInvalidos.push('Data Entrega');
    if (!placaVeiculo?.value) camposInvalidos.push('Placa');
    if (!motorista?.value) camposInvalidos.push('Motorista');

    if (camposInvalidos.length > 0) {
      exibirToast(`Preencha os campos obrigatórios: ${camposInvalidos.join(', ')}`, 'warning');
      return;
    }

    const infoInputs = document.querySelectorAll('.card.border-primary input[disabled]');
    let cliente = '-', produto = '-', bitola = '-', nfVenda = '-';
    let transportadora = '-', documento = '-', telefone = '-';

    if (infoInputs.length >= 9) {
      cliente = infoInputs[0]?.value || '-';
      produto = infoInputs[1]?.value || '-';
      bitola = infoInputs[2]?.value || '-';
      nfVenda = infoInputs[3]?.value || '-';
      transportadora = infoInputs[4]?.value || '-';
      documento = infoInputs[5]?.value || '-';
      telefone = infoInputs[6]?.value || '-';
    }

    const confirmaCliente = document.getElementById('confirma-cliente');
    const confirmaProduto = document.getElementById('confirma-produto');
    const confirmaBitola = document.getElementById('confirma-bitola');
    const confirmaNfVenda = document.getElementById('confirma-nf-venda');
    const confirmaTransportadora = document.getElementById('confirma-transportadora');
    const confirmaDocumento = document.getElementById('confirma-documento');
    const confirmaTelefone = document.getElementById('confirma-telefone');

    if (confirmaCliente) confirmaCliente.value = cliente;
    if (confirmaProduto) confirmaProduto.value = produto;
    if (confirmaBitola) confirmaBitola.value = bitola;
    if (confirmaNfVenda) confirmaNfVenda.value = nfVenda;
    if (confirmaTransportadora) confirmaTransportadora.value = transportadora;
    if (confirmaDocumento) confirmaDocumento.value = documento;
    if (confirmaTelefone) confirmaTelefone.value = telefone;

    document.getElementById('confirma-nf').value = numeroNf.value;
    document.getElementById('confirma-peso').value = pesoLiquido.value;
    document.getElementById('confirma-data').value = formatarData(dataEntrega.value);
    document.getElementById('confirma-fornecedor').value =
      fornecedor.options[fornecedor.selectedIndex]?.text || '-';
    document.getElementById('confirma-placa').value = placaVeiculo.value;
    document.getElementById('confirma-motorista').value = motorista.value;

    const imagemSrc = imagemBase64 || window.imagemBase64;
    if (imagemSrc && elementos.confirmaImagemTicket) {
      elementos.confirmaImagemTicket.src = imagemSrc;
    }

    const modal = new bootstrap.Modal(elementos.modalConfirmacao);
    modal.show();
  };

  const confirmarCadastro = () => {
    
    const modalInstance = bootstrap.Modal.getInstance(elementos.modalConfirmacao);
    if (modalInstance) {
      modalInstance.hide();
    }

    elementos.formTicket.submit();
  };

  const formatarData = (dataISO) => {
    if (!dataISO) return '-';
    const [ano, mes, dia] = dataISO.split('-');
    return `${dia}/${mes}/${ano}`;
  };

  const exibirLoader = () => {
    if (elementos.loaderFullscreen) {
      elementos.loaderFullscreen.style.display = 'flex';
    }
  };

  const esconderLoader = () => {
    if (elementos.loaderFullscreen) {
      elementos.loaderFullscreen.style.display = 'none';
    }
  };

  const exibirToast = (mensagem, tipo = 'info') => {
    
    const toastAnterior = document.getElementById('toast-ticket');
    if (toastAnterior) {
      toastAnterior.remove();
    }

    const cores = {
      success: 'bg-success',
      error: 'bg-danger',
      warning: 'bg-warning',
      info: 'bg-info'
    };

    const icones = {
      success: '<path d="M5 12l5 5l10 -10"/>',
      error: '<path d="M18 6l-12 12"/><path d="M6 6l12 12"/>',
      warning: '<path d="M12 9v4"/><path d="M12 17h.01"/>',
      info: '<path d="M12 9h.01"/><path d="M11 12h1v4h1"/>'
    };

    const toastHtml = `
      <div id="toast-ticket" class="toast align-items-center text-white ${cores[tipo]} border-0" 
           role="alert" aria-live="assertive" aria-atomic="true" 
           style="position: fixed; top: 20px; right: 20px; z-index: 11000;">
        <div class="d-flex">
          <div class="toast-body d-flex align-items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="icon me-2" width="24" height="24" 
                 viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" 
                 stroke-linecap="round" stroke-linejoin="round">
              ${icones[tipo]}
            </svg>
            ${mensagem}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', toastHtml);
    const toast = new bootstrap.Toast(document.getElementById('toast-ticket'), {
      autohide: true,
      delay: 4000
    });
    toast.show();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
  } else {
    inicializar();
  }

})();
