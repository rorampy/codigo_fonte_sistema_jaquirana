Kit de ferramentas pessoal. Algumas ferramentas dependem de Módulos de terceiros...

# Changelog

## Versão 1.1.9 (23/07/2024)

### Adicionado

- Add função 'remover_dias_em_data' na classe DataHora;

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.1.8 (03/07/2024)

### Adicionado

- Add função 'verificar_fim_de_semana' na classe DataHora;

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.1.7 (14/06/2024)

### Adicionado

- Add função 'adicionar_dias_em_data' na classe DataHora;

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.1.6 (27/05/2024)

### Adicionado

- Add função 'converter_objeto_datetime_em_html_iso_8601' na classe DataHora;

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.1.5 (13/02/2024)

### Adicionado

- N/A;

### Corrigido/Alterado

- Alter função 'gerar_pdf_from_html' na classe ManipulacaoArquivos para habilitar acesso a arquivos locais pelo pdfkit;

<hr>

## Versão 1.1.4 (02/02/2024)

### Adicionado

- N/A;

### Corrigido/Alterado

- Alter função 'campo_obrigatorio' na classe ValidaForms para reconhecer 'R$ 0,00' como vazio;

<hr>

## Versão 1.1.3 (24/01/2024)

### Adicionado

- N/A;

### Corrigido/Alterado

- Alter função 'converter_string_brl_para_float' na classe ValoresMonetarios, melhoria;

<hr>

## Versão 1.1.2 (23/01/2024)

### Adicionado

- Add função 'remove_pontuacao_cip_py' na classe ValidaDocs;
- Add função 'insere_pontuacao_cip_py' na classe ValidaDocs;
- Add função 'remove_pontuacao_ruc_py' na classe ValidaDocs;
- Add função 'insere_pontuacao_ruc_py' na classe ValidaDocs;

### Corrigido/Alterado

- Alterado o formato de telefones PY (inserido parênteses no DDD); 

<hr>

## Versão 1.1.1 (23/01/2024)

### Adicionado

- Add função 'insere_pontuacao_telefone_fixo_py' na classe Tels;
- Add função 'remove_pontuacao_telefone_fixo_py' na classe Tels;
- Add função 'insere_pontuacao_telefone_celular_py' na classe Tels;
- Add função 'remove_pontuacao_telefone_celular_py' na classe Tels;

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.1.0 (04/01/2024)

### Adicionado

- Add função de extração de Data de um obtejo DateTime na classe DataHora;

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.0.9 (19/12/2023)

### Adicionado

- Add função de converter string BRL para float na classe 'ValoresMonetarios';

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.0.8 (13/12/2023)

### Adicionado

- N/A;

### Corrigido/Alterado

- Alteração na função de conversão de input BRL na classe 'ValidaForms';

<hr>

## Versão 1.0.7 (05/12/2023)

### Adicionado

- Add função de remover pontuação de CEP na classe 'ValidaForms';

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.0.6 (02/12/2023)

### Adicionado

- N/A;

### Corrigido/Alterado

- Alteração na função de validação de CNPJ na classe 'ValidaForms';

<hr>

## Versão 1.0.5 (01/12/2023)

### Adicionado

- Add função de validação de CNPJ na classe 'ValidaForms';

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.0.4 (18/11/2023)

### Adicionado

- N/A;

### Corrigido/Alterado

- Alteração na função de validação do Google ReCAPTCHA;

<hr>

## Versão 1.0.3 (31/10/2023)

### Adicionado

- Add função de validação de ReCAPCHA do Google na classe 'ValidaForms';

### Corrigido/Alterado

- N/A;

<hr>

## Versão 1.0.2 (13/10/2023)

### Adicionado

- Add validação de float 0.0 na função 'campo_brigatorio' da classe 'ValidaForms';

### Corrigido/Alterado

- Alteração do nome da função 'validar_e_converter_valor_input_brl' na classe 'ValidaForms';

<hr>

## Versão 1.0.1 (06/10/2023)

### Adicionado

- Add funções de inserir/remover pontuações no Telefone Fixo BR na classe 'Tels';

### Corrigido

- Alterações no arquivo '__init__.py';

<hr>

## Versão 1.0.0 (06/10/2023)

### Adicionado

- Add funções de inserir/remover pontuação de CNPJ na classe 'ValidaDocs';

### Corrigido

- Alterações no arquivo '__init__.py';

<hr>

## Versão 0.0.1 (10/08/2023)

### Adicionado

- Mudança de padrão na validação, agora retorna um dicionário com chave 'validado' ou com o erro;
- Importação de classes no arquivo __init__.py, agora basta importar o módulo para utilizar todas as classes;

### Corrigido

- Nenhuma correção;
