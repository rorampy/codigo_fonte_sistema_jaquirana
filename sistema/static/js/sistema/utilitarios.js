// Fecha os alertas automaticamente
function configurarFechamentoAutomaticoAlertas() {
    function closeAlert(alert) {
        alert.classList.remove('show');
        setTimeout(function() {
            alert.remove();
        }, 150); // Tempo para permitir a transição do fade
    }
    
    // Seleciona todos os alertas
    const alerts = document.querySelectorAll('.meu-alerta');
    
    // Configura cada alerta para fechar após 10 segundos
    alerts.forEach(function(alert) {
            setTimeout(function() {
            closeAlert(alert);
        }, 10000); // 10000 milissegundos = 10 segundos
    });
}

// Ajax para preenchimento do input de Cliente baseado no select de cliente
function atualizarCliente() {
  // Obtém o valor selecionado no campo de seleção
  var clienteId = document.getElementById('clienteId').value;

  // Verifica se o valor não está vazio
  if (clienteId !== '') {
      // Faz uma requisição para o servidor p/ obter os dados da fazenda
      var url = '/clientes/obter-dados-cliente/' + clienteId;

      // Realiza uma requisição AJAX (pode ser usado o fetch ou jQuery.ajax)
      fetch(url)
      .then(response => response.json())
      .then(data => {
          // Preenche o campo de entrada com os dados obtidos
          document.getElementsByName('rucCliente')[0].value = data.ruc_cliente;
          document.getElementsByName('contribuinte')[0].value = data.contribuinte;
          document.getElementsByName('tipoOperacao')[0].value = data.tipo_operacao;
          document.getElementsByName('telefoneCliente')[0].value = data.telefone_cliente;
      })
      .catch(error => console.error('Erro ao obter dados do cliente:', error));
  } else {
      // Se o valor estiver vazio, limpa o campo de entrada
      document.getElementsByName('rucCliente')[0].value = '';
      document.getElementsByName('contribuinte')[0].value = '';
      document.getElementsByName('tipoOperacao')[0].value = '';
      document.getElementsByName('telefoneCliente')[0].value = '';
  }
}

// Máscara para campos BRL
function aplicarMascaraMoeda() {
    document.querySelectorAll('.campo-moeda-brl').forEach(campo => {
        // Lógica de formatação integrada
        function formatarParaMoeda(valor) {
            valor = valor.replace(/\D/g, "");  // Remove tudo o que não é dígito
            valor = (valor / 100).toFixed(2);  // Divide por 100 e fixa duas casas decimais
            valor = valor.replace(".", ",");   // Substitui ponto por vírgula
            valor = valor.replace(/(\d)(\d{3})(\d{3}),/g, "$1.$2.$3,"); // Adiciona ponto como separador de milhares
            valor = valor.replace(/(\d)(\d{3}),/g, "$1.$2,"); // Adiciona ponto como separador de milhares
            return "R$ " + valor;  // Adiciona o símbolo de Real
        }

        campo.value = formatarParaMoeda(campo.value);  // Aplica a máscara para valores existentes
        campo.addEventListener('input', function() {
            this.value = formatarParaMoeda(this.value);  // Aplica a máscara durante a digitação
        });
    });
}

// Máscara para campos PYG
function formatarParaMoedaPYG(valor) {
    valor = valor.replace(/\D/g, "");  // Remove tudo o que não é dígito
    valor = valor.replace(/\B(?=(\d{3})+(?!\d))/g, ".");  // Adiciona ponto como separador de milhares
    return "₲ " + valor;  // Adiciona o símbolo de Guarani
  }

function aplicarMascaraMoedaPYG() {
    document.querySelectorAll('.campo-moeda-pyg').forEach(campo => {
      // Verifica se o campo não está vazio antes de aplicar a máscara
      if (campo.value !== "") {
        campo.value = formatarParaMoedaPYG(campo.value);  // Aplica a máscara para valores existentes
      }

      // Adiciona evento para aplicar a máscara durante a digitação
      campo.addEventListener('input', function() {
        this.value = formatarParaMoedaPYG(this.value);
      });

      // Adiciona evento para remover a máscara se o campo estiver vazio novamente
      campo.addEventListener('blur', function() {
        if (this.value === "₲ ") {
          this.value = "";
        }
      });
    });
}

// Máscara para campos USD
function formatarParaMoedaUSD(valor) {
    valor = valor.replace(/\D/g, "");  // Remove tudo o que não é dígito
    valor = (valor / 100).toFixed(2);  // Divide por 100 e fixa duas casas decimais
    valor = valor.replace(/\B(?=(\d{3})+(?!\d))/g, ","); // Adiciona vírgula como separador de milhares
    return "$ " + valor;  // Adiciona o símbolo de Dólar
}

function aplicarMascaraMoedaUSD() {
    document.querySelectorAll('.campo-moeda-usd').forEach(campo => {
      // Verifica se o campo não está vazio antes de aplicar a máscara
      if (campo.value !== "") {
        campo.value = formatarParaMoedaUSD(campo.value);  // Aplica a máscara para valores existentes
      }
      
      campo.addEventListener('input', function() {
        this.value = formatarParaMoedaUSD(this.value);  // Aplica a máscara durante a digitação
      });

      // Adiciona evento para remover a máscara se o campo estiver vazio novamente
      campo.addEventListener('blur', function() {
        if (this.value === "$ ") {
          this.value = "";
        }
      });
    });
}

// Máscara para campos Somente números
function aplicarComportamentoCampoSomenteNumeros() {
    // Seleciona todos os elementos com a classe 'campo-numerico'
    document.querySelectorAll('.campo-numerico').forEach(campo => {
        // Adiciona um ouvinte de eventos de 'keypress' a cada campo
        campo.addEventListener('keypress', function(e) {
        if (!e.key.match(/[0-9]/)) {
            e.preventDefault(); // Impede a entrada de caracteres não numéricos
        }
        });
    });
}


// Máscara para campos Números float com substituição de vírgula por ponto e máximo de 2 casas decimais
function aplicarComportamentoCampoFloat() {
  document.querySelectorAll('.campo-float').forEach(campo => {
      // Substitui vírgula por ponto e limita a 2 casas decimais
      campo.addEventListener('input', function() {
          // Substitui vírgula por ponto
          let valor = this.value.replace(',', '.');

          // Regex para extrair parte inteira e até duas casas decimais
          const match = valor.match(/^(\d+)(\.(\d{0,2})?)?/);
          if (match) {
              this.value = match[1];
              if (match[2]) {
                  this.value += match[2];
              }
          } else {
              this.value = '';
          }
      });

      // Permite apenas números, ponto ou vírgula
      campo.addEventListener('keypress', function(e) {
          const regex = /[0-9]|[.,]/;
          if (!regex.test(e.key)) {
              e.preventDefault();
          }
      });
  });
}


// Obtem a data de hoje e carrega no campo
function preencherDataAtualemCampo() {
    var hoje = new Date();

    // Formata a data para o formato YYYY-MM-DD
    var dia = String(hoje.getDate()).padStart(2, '0');
    var mes = String(hoje.getMonth() + 1).padStart(2, '0'); // Janeiro é 0!
    var ano = hoje.getFullYear();
    var dataFormatada = `${ano}-${mes}-${dia}`;

    // Preenche todos os campos com a classe 'data-hoje' com a data formatada
    document.querySelectorAll('.data-hoje').forEach(campo => {
        campo.value = dataFormatada;
    });
}


// Obtém a data e hora atual no fuso horário UTC-3 e carrega no campo
function preencherDataHoraAtualEmCampo() {
  var agora = new Date();

  // Ajusta para o fuso horário diminuindo 1 hora do horário do S.O
  agora.setHours(agora.getHours() - 1);

  // Formata a data e hora para o formato YYYY-MM-DD HH:MM
  var dia = String(agora.getDate()).padStart(2, '0');
  var mes = String(agora.getMonth() + 1).padStart(2, '0'); // Janeiro é 0!
  var ano = agora.getFullYear();
  var horas = String(agora.getHours()).padStart(2, '0');
  var minutos = String(agora.getMinutes()).padStart(2, '0');
  var dataHoraFormatada = `${ano}-${mes}-${dia} ${horas}:${minutos}`;

  // Preenche todos os campos com a classe 'data-hora-atual' com a data e hora formatada
  document.querySelectorAll('.data-hora-atual').forEach(campo => {
      campo.value = dataHoraFormatada;
  });
}


// Máscara para substituição de vírgula por ponto em um campo
function campoSemVirgulaComPonto() {
    // Seleciona todos os elementos com a classe 'campo-sem-virgula'
    document.querySelectorAll('.campo-sem-virgula').forEach(campo => {
        // Adiciona um ouvinte de eventos de 'input' a cada campo
        campo.addEventListener('input', function() {
        // Substitui vírgula por ponto
        this.value = this.value.replace(',', '.');
        });
    });
}


// Máscara para campo porcentagem com máx. 100%
function validarCampoPorcentagemMaximo100(input) {
    // Primeiro substitui todas as vírgulas por pontos
    input.value = input.value.replace(/,/g, '.');

    // Permite números, ponto decimal (já substituiu vírgulas por pontos) e remove qualquer outro caractere
    input.value = input.value.replace(/[^0-9.]/g, '');
  
    // Converte o valor para um número inteiro
    var valor = parseFloat(input.value, 10);
  
    // Verifica se o valor é maior que 100
    if (valor > 100) {
      // Se for maior que 100, define o valor como 100
      input.value = '100';
    }
  }

// Máscara para campos de RUC PF e PJ
function aplicarMascaraRUCEmCampos() {
    // Seleciona todos os campos com o seletor fornecido
    var rucInputs = document.querySelectorAll('.ruc-input');
  
    // Função para aplicar a máscara
    function aplicarMascaraRUC(event) {
      var input = event.target;
      var value = input.value.replace(/\D/g, ''); // Remove tudo que não for número
      var length = value.length;
  
      // Limita a entrada a no máximo 8 dígitos
      if (length > 8) {
        value = value.substring(0, 8);
        length = 8;
      }
  
      // Aplica a máscara de acordo com o número de dígitos
      if (length === 7) {
        input.value = value.replace(/(\d{6})(\d)/, '$1-$2'); // Aplica o hífen após o sexto dígito
      } else if (length === 8) {
        input.value = value.replace(/(\d{7})(\d)/, '$1-$2'); // Aplica o hífen após o sétimo dígito
      } else {
        input.value = value; // Para menos de 7 dígitos, sem máscara
      }
    }
  
    // Itera sobre cada campo e adiciona o evento de input para aplicar a máscara
    rucInputs.forEach(function (rucInput) {
      rucInput.addEventListener('input', aplicarMascaraRUC);
    });
}

// Inicializador de funções
function inicializar() {
    configurarFechamentoAutomaticoAlertas();
    aplicarMascaraMoeda();
    aplicarMascaraMoedaPYG();
    aplicarMascaraMoedaUSD();
    aplicarComportamentoCampoSomenteNumeros();
    aplicarComportamentoCampoFloat();
    preencherDataAtualemCampo();
    preencherDataHoraAtualEmCampo();
    campoSemVirgulaComPonto();
    aplicarMascaraRUCEmCampos();
}

window.addEventListener('load', inicializar);