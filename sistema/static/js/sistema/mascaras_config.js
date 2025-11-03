$(document).ready(function () {
  // Máscaras fixas
  $('.cpfMask').mask('000.000.000-00');
  $('.cepMask').mask('00000-000');
  $('.cnpjMask').mask('00.000.000/0000-00');
  $('.celular').mask('(00) 00000-0000');
  $('.telefone').mask('(00) 0000-0000');
  $('.codBarras').mask('00000.00000 00000.000000 00000.000000 0 00000000000000');
  $('.codAgencia').mask('00000000000');
  $('.codConta').mask('00000000000000000000000000');
  $('.codDigito').mask('00000000');
  $('.mesAno').mask('00/0000');
});


document.addEventListener('DOMContentLoaded', function () {
  const inputs = document.querySelectorAll('.cpfCnpj');
  const cleaveInstances = new Map();

  function aplicarMascara(input) {
    const valor = input.value;
    const numeros = valor.replace(/\D/g, '');

    if (cleaveInstances.has(input)) {
      cleaveInstances.get(input).destroy();
    }

    let cleaveInstance;
    if (numeros.length <= 11) {
      cleaveInstance = new Cleave(input, {
        delimiters: ['.', '.', '-'],
        blocks: [3, 3, 3, 2],
        numericOnly: true
      });
    } else {
      cleaveInstance = new Cleave(input, {
        delimiters: ['.', '.', '/', '-'],
        blocks: [2, 3, 3, 4, 2],
        numericOnly: true
      });
    }

    cleaveInstances.set(input, cleaveInstance);
  }

  inputs.forEach(input => {
    aplicarMascara(input);
    
    input.addEventListener('input', () => aplicarMascara(input));
  });
});

$(document).ready(function() {
  $('#tabela-informacao').DataTable({
    ordering: true,
    paging: false,
    searching: false,
    info: false,
    order:[[0, 'desc']],
    language: {
      emptyTable: "  "
    }
  });
});

$(document).ready(function () {
  const tabela = $('#tabela-informacao-ro').DataTable({
    ordering: true,
    paging: false,       
    info: false,        
    searching: true,   
    language: {
      emptyTable: "Nenhum registro encontrado",
      search: "",
      searchPlaceholder: "Filtrar registros...",
      zeroRecords: "Nenhum resultado encontrado",
    },
    dom: 't'
  });

  $('#tabela-search').on('keyup', function () {
    tabela.search(this.value).draw();
  });
});