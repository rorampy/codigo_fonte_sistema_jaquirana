/**
 * Gerenciamento de anexos com Dropzone para categorização de fatura
 */

document.addEventListener('DOMContentLoaded', function() {
  const dropzoneElement = document.getElementById('dropzone-anexos');
  const form = document.querySelector('form[enctype="multipart/form-data"]');
  
  if (!dropzoneElement || !form) {
    return;
  }

  // Configurar Dropzone
  const myDropzone = new Dropzone("#dropzone-anexos", {
    url: "#",
    autoProcessQueue: false,
    uploadMultiple: false,
    paramName: "anexos",
    maxFilesize: 10,
    acceptedFiles: ".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx",
    addRemoveLinks: true,
    dictDefaultMessage: "",
    dictRemoveFile: "Remover",
    dictCancelUpload: "Cancelar",
    dictMaxFilesExceeded: "Arquivo muito grande"
  });

  // Interceptar submit do formulário
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    e.stopPropagation();

    // Criar FormData com todos os campos do formulário
    const formData = new FormData(form);
    
    // Remover anexos que possam estar vazios
    formData.delete('anexos');
    
    // Adicionar arquivos do Dropzone
    const files = myDropzone.files;
    if (files && files.length > 0) {
      files.forEach(function(file) {
        formData.append('anexos', file);
      });
    }

    // Enviar formulário
    fetch(form.action || window.location.href, {
      method: 'POST',
      body: formData
    })
    .then(function(response) {
      if (response.redirected) {
        window.location.href = response.url;
        return;
      }
      return response.text();
    })
    .then(function(html) {
      if (html) {
        document.open();
        document.write(html);
        document.close();
      }
    })
    .catch(function(error) {
      console.error('Erro:', error);
      alert('Erro ao enviar formulário. Tente novamente.');
    });
  });
});
