
/**
 * Formata um valor numérico para o padrão monetário brasileiro (BRL).
 * Recebe valor em centavos, retorna string formatada (ex: R$ 1.234,56 ou R$ -1.234,56).
 * Usada para exibir valores em todos os cards e relatórios.
 */
function formatarParaMoedaBRL(valor) {
  // Detecta se o valor é negativo
  const isNegativo = valor < 0;

  // Trabalha com valor absoluto
  valor = Math.abs(valor);

  valor = String(valor); // Garante que é string
  valor = valor.replace(/\D/g, "");  // Remove tudo o que não é dígito
  valor = (valor / 100).toFixed(2);  // Divide por 100 e fixa duas casas decimais
  valor = valor.replace(".", ",");   // Substitui ponto por vírgula
  valor = valor.replace(/(\d)(\d{3})(\d{3}),/g, "$1.$2.$3,"); // Adiciona ponto como separador de milhares
  valor = valor.replace(/(\d)(\d{3}),/g, "$1.$2,"); // Adiciona ponto como separador de milhares

  // Adiciona o sinal negativo se necessário
  if (isNegativo) {
    return "R$ -" + valor;
  }

  return "R$ " + valor;  // Adiciona o símbolo de Real
}

/**
 * Formata valor em reais (float) para BRL, convertendo para centavos antes.
 * Usada para exibir valores calculados (ex: receita, impostos, etc).
 */
function formatarMoedaReal(valor) {
  if (valor === null || valor === undefined || isNaN(valor)) {
    valor = 0;
  }

  // Detecta se o valor é negativo
  const isNegativo = valor < 0;

  // Trabalha com valor absoluto para a conversão
  const valorAbsoluto = Math.abs(valor);
  const valorEmCentavos = Math.round(valorAbsoluto * 100);

  // Formata o valor
  let valorFormatado = formatarParaMoedaBRL(valorEmCentavos);

  // Se o valor original era negativo, adiciona o sinal
  if (isNegativo) {
    valorFormatado = valorFormatado.replace("R$ ", "R$ -");
  }

  return valorFormatado;
}

// Função para atualizar a tabela de resumo financeiro usando dados já calculados
function atualizarResumoFinanceiro() {
  // Cálculos dos impostos
  const icmsVenda = analiseData.receitaBruta * 0.12;
  const pisVenda = analiseData.receitaBruta * 0.0165;
  const cofinsVenda = analiseData.receitaBruta * 0.076;
  const totalImpostosDebito = icmsVenda + pisVenda + cofinsVenda;
  
  // Impostos de crédito (das operações de compra) - convertendo de centavos para reais
  const totalImpostosCredito = ((compraMercadoriaData.icms || 0) + (compraMercadoriaData.pis || 0) + (compraMercadoriaData.cofins || 0)
      + (freteData.icms || 0) + (freteData.pis || 0) + (freteData.cofins || 0)
      + (extracaoData.icms || 0) + (extracaoData.pis || 0) + (extracaoData.cofins || 0)
      + (comissaoData.icms || 0) + (comissaoData.pis || 0) + (comissaoData.cofins || 0)) / 100;
  
  // Margem por tonelada
  const quantidade = parseFloat(document.querySelector('.campo-float').value) || 0;
  const margemTon = quantidade > 0 ? (analiseData.lucroLiquido / 100) / quantidade : 0;

  // Atualiza os campos
  if (document.getElementById('resumo-receita-bruta')) {
    document.getElementById('resumo-receita-bruta').textContent = formatarMoedaReal(analiseData.receitaBruta);
  }
  if (document.getElementById('resumo-impostos-debito')) {
    document.getElementById('resumo-impostos-debito').textContent = formatarMoedaReal(totalImpostosDebito);
  }
  if (document.getElementById('resumo-impostos-credito')) {
    document.getElementById('resumo-impostos-credito').textContent = formatarMoedaReal(totalImpostosCredito);
  }
  if (document.getElementById('resumo-receita-liquida')) {
    document.getElementById('resumo-receita-liquida').textContent = formatarMoedaReal(analiseData.receitaLiquida);
  }
  if (document.getElementById('resumo-cmv')) {
    document.getElementById('resumo-cmv').textContent = formatarMoedaReal(analiseData.custosTotal / 100);
  }
  if (document.getElementById('resumo-lucro-bruto')) {
    document.getElementById('resumo-lucro-bruto').textContent = formatarMoedaReal(analiseData.lucroBruto / 100);
  }
  if (document.getElementById('resumo-lucro-liquido')) {
    document.getElementById('resumo-lucro-liquido').textContent = formatarMoedaReal(analiseData.lucroLiquido / 100);
  }
  if (document.getElementById('resumo-margem-ton')) {
    document.getElementById('resumo-margem-ton').textContent = formatarMoedaReal(margemTon);
  }
  if (document.getElementById('resumo-margem-liquida')) {
    document.getElementById('resumo-margem-liquida').textContent = analiseData.margemLiquida.toFixed(2) + '%';
  }

  // Remove campos antigos que não existem mais
  if (document.getElementById('resumo-icms-venda')) {
    document.getElementById('resumo-icms-venda').textContent = "- " + formatarMoedaReal(analiseData.receitaBruta * 0.12);
  }
  if (document.getElementById('resumo-pis-venda')) {
    document.getElementById('resumo-pis-venda').textContent = "- " + formatarMoedaReal(analiseData.receitaBruta * 0.0165);
  }
  if (document.getElementById('resumo-cofins-venda')) {
    document.getElementById('resumo-cofins-venda').textContent = "- " + formatarMoedaReal(analiseData.receitaBruta * 0.076);
  }
  // Exibe o total de despesas correto (custos + acréscimos + impostos)
  if (document.getElementById('resumo-total-despesas')) {
    // Recalcula o total de despesas
    // Custos ja com impostos
    let custos = (compraMercadoriaData.total || 0) + (freteData.total || 0) + (extracaoData.total || 0) + (comissaoData.total || 0);
    let acrescimos = (compraMercadoriaData.acrescimos || 0) + (freteData.acrescimos || 0) + (extracaoData.acrescimos || 0) + (comissaoData.acrescimos || 0);
    // let impostos = (compraMercadoriaData.icms || 0) + (compraMercadoriaData.pis || 0) + (compraMercadoriaData.cofins || 0)
    //     + (freteData.icms || 0) + (freteData.pis || 0) + (freteData.cofins || 0)
    //     + (extracaoData.icms || 0) + (extracaoData.pis || 0) + (extracaoData.cofins || 0)
    //     + (comissaoData.icms || 0) + (comissaoData.pis || 0) + (comissaoData.cofins || 0);
    let totalDespesasCorreto = custos + acrescimos;
    document.getElementById('resumo-total-despesas').textContent = formatarParaMoedaBRL(totalDespesasCorreto);
  }
}

// Função para atualizar a tabela de impostos por operação usando dados já calculados
function atualizarResumoImpostos() {
  const icmsVendaReais = parseFloat(((analiseData.receitaBruta * 0.12)).toFixed(2));
  const pisVendaReais = parseFloat(((analiseData.receitaBruta * 0.0165)).toFixed(2));
  const cofinsVendaReais = parseFloat(((analiseData.receitaBruta * 0.076)).toFixed(2));

  if (document.getElementById('operacao-venda-icms')) {
    document.getElementById('operacao-venda-icms').textContent = "- " + formatarMoedaReal(icmsVendaReais);
  }
  if (document.getElementById('operacao-venda-pis')) {
    document.getElementById('operacao-venda-pis').textContent = "- " + formatarMoedaReal(pisVendaReais);
  }
  if (document.getElementById('operacao-venda-cofins')) {
    document.getElementById('operacao-venda-cofins').textContent = "- " + formatarMoedaReal(cofinsVendaReais);
  }
  if (document.getElementById('operacao-venda-total')) {
    const totalVendaReais = parseFloat((icmsVendaReais + pisVendaReais + cofinsVendaReais).toFixed(2));
    document.getElementById('operacao-venda-total').textContent = "- " + formatarMoedaReal(totalVendaReais);
  }

  const icmsCompraReais = parseFloat(((compraMercadoriaData.icms || 0) / 100).toFixed(2));
  const pisCompraReais = parseFloat(((compraMercadoriaData.pis || 0) / 100).toFixed(2));
  const cofinsCompraReais = parseFloat(((compraMercadoriaData.cofins || 0) / 100).toFixed(2));

  if (document.getElementById('operacao-compra-icms')) {
    document.getElementById('operacao-compra-icms').textContent = formatarMoedaReal(icmsCompraReais);
  }
  if (document.getElementById('operacao-compra-pis')) {
    document.getElementById('operacao-compra-pis').textContent = formatarMoedaReal(pisCompraReais);
  }
  if (document.getElementById('operacao-compra-cofins')) {
    document.getElementById('operacao-compra-cofins').textContent = formatarMoedaReal(cofinsCompraReais);
  }
  if (document.getElementById('operacao-compra-total')) {
    const totalCompraReais = parseFloat((icmsCompraReais + pisCompraReais + cofinsCompraReais).toFixed(2));
    document.getElementById('operacao-compra-total').textContent = formatarMoedaReal(totalCompraReais);
  }

  // === FRETE (VALORES NEGATIVOS - CRÉDITOS) ===
  const icmsFreteReais = parseFloat(((freteData.icms || 0) / 100).toFixed(2));
  const pisFreteReais = parseFloat(((freteData.pis || 0) / 100).toFixed(2));
  const cofinsFreteReais = parseFloat(((freteData.cofins || 0) / 100).toFixed(2));

  if (document.getElementById('operacao-frete-icms')) {
    document.getElementById('operacao-frete-icms').textContent = formatarMoedaReal(icmsFreteReais);
  }
  if (document.getElementById('operacao-frete-pis')) {
    document.getElementById('operacao-frete-pis').textContent = formatarMoedaReal(pisFreteReais);
  }
  if (document.getElementById('operacao-frete-cofins')) {
    document.getElementById('operacao-frete-cofins').textContent = formatarMoedaReal(cofinsFreteReais);
  }
  if (document.getElementById('operacao-frete-total')) {
    const totalFreteReais = parseFloat((icmsFreteReais + pisFreteReais + cofinsFreteReais).toFixed(2));
    document.getElementById('operacao-frete-total').textContent = formatarMoedaReal(totalFreteReais);
  }

  // === EXTRAÇÃO (VALORES NEGATIVOS - CRÉDITOS) ===
  const icmsExtracaoReais = parseFloat(((extracaoData.icms || 0) / 100).toFixed(2));
  const pisExtracaoReais = parseFloat(((extracaoData.pis || 0) / 100).toFixed(2));
  const cofinsExtracaoReais = parseFloat(((extracaoData.cofins || 0) / 100).toFixed(2));

  if (document.getElementById('operacao-extracao-icms')) {
    document.getElementById('operacao-extracao-icms').textContent = formatarMoedaReal(icmsExtracaoReais);
  }
  if (document.getElementById('operacao-extracao-pis')) {
    document.getElementById('operacao-extracao-pis').textContent = formatarMoedaReal(pisExtracaoReais);
  }
  if (document.getElementById('operacao-extracao-cofins')) {
    document.getElementById('operacao-extracao-cofins').textContent = formatarMoedaReal(cofinsExtracaoReais);
  }
  if (document.getElementById('operacao-extracao-total')) {
    const totalExtracaoReais = parseFloat((icmsExtracaoReais + pisExtracaoReais + cofinsExtracaoReais).toFixed(2));
    document.getElementById('operacao-extracao-total').textContent = formatarMoedaReal(totalExtracaoReais);
  }

  // === COMISSÃO (VALORES NEGATIVOS - CRÉDITOS) ===
  const icmsComissaoReais = parseFloat(((comissaoData.icms || 0) / 100).toFixed(2));
  const pisComissaoReais = parseFloat(((comissaoData.pis || 0) / 100).toFixed(2));
  const cofinsComissaoReais = parseFloat(((comissaoData.cofins || 0) / 100).toFixed(2));

  if (document.getElementById('operacao-comissao-icms')) {
    document.getElementById('operacao-comissao-icms').textContent = formatarMoedaReal(icmsComissaoReais);
  }
  if (document.getElementById('operacao-comissao-pis')) {
    document.getElementById('operacao-comissao-pis').textContent = formatarMoedaReal(pisComissaoReais);
  }
  if (document.getElementById('operacao-comissao-cofins')) {
    document.getElementById('operacao-comissao-cofins').textContent = formatarMoedaReal(cofinsComissaoReais);
  }
  if (document.getElementById('operacao-comissao-total')) {
    const totalComissaoReais = parseFloat((icmsComissaoReais + pisComissaoReais + cofinsComissaoReais).toFixed(2));
    document.getElementById('operacao-comissao-total').textContent = formatarMoedaReal(totalComissaoReais);
  }

  // Totais Gerais
  const totalGeralIcms = parseFloat((icmsVendaReais - icmsCompraReais - icmsFreteReais - icmsExtracaoReais - icmsComissaoReais).toFixed(2));
  const totalGeralPis = parseFloat((pisVendaReais - pisCompraReais - pisFreteReais - pisExtracaoReais - pisComissaoReais).toFixed(2));
  const totalGeralCofins = parseFloat((cofinsVendaReais - cofinsCompraReais - cofinsFreteReais - cofinsExtracaoReais - cofinsComissaoReais).toFixed(2));
  const totalGeralTotal = parseFloat((totalGeralIcms + totalGeralPis + totalGeralCofins).toFixed(2));

  if (document.getElementById('total-geral-icms')) {
    document.getElementById('total-geral-icms').textContent = formatarMoedaReal(totalGeralIcms);
  }
  if (document.getElementById('total-geral-pis')) {
    document.getElementById('total-geral-pis').textContent = formatarMoedaReal(totalGeralPis);
  }
  if (document.getElementById('total-geral-cofins')) {
    document.getElementById('total-geral-cofins').textContent = formatarMoedaReal(totalGeralCofins);
  }
  if (document.getElementById('total-geral-total')) {
    document.getElementById('total-geral-total').textContent = formatarMoedaReal(totalGeralTotal);
  }
}

// Função para atualizar a tabela de acréscimos fiscais
function atualizarTabelaAcrescimos() {
  // === COMPRA DE MERCADORIA (apenas ajuste fiscal 5%) ===
  let descCompra = "-";
  let valorCompraAjusteFiscalReais = 0;

  // Calcula apenas o ajuste fiscal de 5% da compra (sem Funrural/Senar)
  if (compraMercadoriaData.tipoEmissao === 'nao' && compraMercadoriaData.documentacaoFiscal === 'sim') {
    descCompra = "5% ajuste";
    let quantidade = inputQuantidadeProduto ? parseFloat(inputQuantidadeProduto.value.replace(',', '.')) || 1 : 1;
    let valorCompraCentavos = inputValorTonCompra ? inputValorTonCompra.value.replace(/\D/g, "") : "0";
    let valorBaseReais = (parseFloat(valorCompraCentavos) / 100) * quantidade;
    valorCompraAjusteFiscalReais = parseFloat((valorBaseReais * 0.05).toFixed(2));
  }

  if (document.getElementById('desc-acrescimo-compra')) {
    document.getElementById('desc-acrescimo-compra').textContent = descCompra;
  }
  if (document.getElementById('acrescimo-compra-total')) {
    document.getElementById('acrescimo-compra-total').textContent = formatarMoedaReal(valorCompraAjusteFiscalReais);
  }

  // === FRETE ===
  let descFrete = "-";
  let valorFreteReais = 0;

  if (freteData.acrescimos > 0) {
    descFrete = "5% ajuste";
    valorFreteReais = parseFloat((freteData.acrescimos / 100).toFixed(2));
  }

  if (document.getElementById('desc-acrescimo-frete')) {
    document.getElementById('desc-acrescimo-frete').textContent = descFrete;
  }
  if (document.getElementById('acrescimo-frete-total')) {
    document.getElementById('acrescimo-frete-total').textContent = formatarMoedaReal(valorFreteReais);
  }

  // === EXTRAÇÃO ===
  let descExtracao = "-";
  let valorExtracaoReais = 0;

  if (extracaoData.acrescimos > 0) {
    descExtracao = "5% ajuste";
    valorExtracaoReais = parseFloat((extracaoData.acrescimos / 100).toFixed(2));
  }

  if (document.getElementById('desc-acrescimo-extracao')) {
    document.getElementById('desc-acrescimo-extracao').textContent = descExtracao;
  }
  if (document.getElementById('acrescimo-extracao-total')) {
    document.getElementById('acrescimo-extracao-total').textContent = formatarMoedaReal(valorExtracaoReais);
  }

  // === COMISSÃO ===
  let descComissao = "-";
  let valorComissaoReais = 0;

  if (comissaoData.acrescimos > 0) {
    descComissao = "5% ajuste";
    valorComissaoReais = parseFloat((comissaoData.acrescimos / 100).toFixed(2));
  }

  if (document.getElementById('desc-acrescimo-comissao')) {
    document.getElementById('desc-acrescimo-comissao').textContent = descComissao;
  }
  if (document.getElementById('acrescimo-comissao-total')) {
    document.getElementById('acrescimo-comissao-total').textContent = formatarMoedaReal(valorComissaoReais);
  }

  // === TOTAL AJUSTES FISCAIS (apenas 5%) ===
  const totalAjustesFiscaisReais = parseFloat((valorCompraAjusteFiscalReais + valorFreteReais + valorExtracaoReais + valorComissaoReais).toFixed(2));

  if (document.getElementById('total-acrescimos-geral')) {
    document.getElementById('total-acrescimos-geral').textContent = formatarMoedaReal(totalAjustesFiscaisReais);
  }

  // === NOVA TABELA: CONTRIBUIÇÕES SOCIAIS RURAIS ===
  let descFunruralCompra = "-";
  let valorFunruralCompraReais = 0;

  // Calcula Funrural/Senar da compra de mercadoria (apenas quando descontado = 'nao')
  if (compraMercadoriaData.funruralDescontado === 'nao') {
    let quantidade = inputQuantidadeProduto ? parseFloat(inputQuantidadeProduto.value.replace(',', '.')) || 1 : 1;
    let valorCompraCentavos = inputValorTonCompra ? inputValorTonCompra.value.replace(/\D/g, "") : "0";
    let valorBaseReais = (parseFloat(valorCompraCentavos) / 100) * quantidade;

    if (compraMercadoriaData.funruralSenar === 'funrural') {
      descFunruralCompra = "1,5% Funrural";
      valorFunruralCompraReais = parseFloat((valorBaseReais * 0.015).toFixed(2));
    } else if (compraMercadoriaData.funruralSenar === 'senar') {
      descFunruralCompra = "0,2% Senar";
      valorFunruralCompraReais = parseFloat((valorBaseReais * 0.002).toFixed(2));
    }
  }

  if (document.getElementById('desc-funrural-compra')) {
    document.getElementById('desc-funrural-compra').textContent = descFunruralCompra;
  }
  if (document.getElementById('funrural-compra-total')) {
    document.getElementById('funrural-compra-total').textContent = formatarMoedaReal(valorFunruralCompraReais);
  }

  // === TOTAL CONTRIBUIÇÕES SOCIAIS ===
  if (document.getElementById('total-funrural-geral')) {
    document.getElementById('total-funrural-geral').textContent = formatarMoedaReal(valorFunruralCompraReais);
  }
}


/**
 * Objeto global para armazenar os principais resultados da análise de precificação.
 * Todos os valores são em reais (float).
 */
const analiseData = {
  receitaBruta: 0,        // Valor total da venda
  receitaLiquida: 0,      // Receita após impostos
  impostosVenda: 0,       // Soma dos impostos sobre venda
  custosTotal: 0,         // CMV (custo mercadoria vendida)
  lucroBruto: 0,          // Receita líquida - CMV
  impostosSobreLucro: 0,  // IRPJ, CSLL, etc
  lucroLiquido: 0,        // Lucro após impostos
  margemLiquida: 0        // Margem percentual
};

// Elementos DOM para exibição dos resultados principais
const metricTotalDespesas = document.getElementById('metric-total-despesas');
const metricCmv = document.getElementById('metric-cmv');
const metricIcmsVenda = document.getElementById('metric-icms-venda');
const metricPisVenda = document.getElementById('metric-pis-venda');
const metricCofinsVenda = document.getElementById('metric-cofins-venda');
const totalReceitaBrutaHeader = document.getElementById('total-receita-bruta');
const metricReceitaBruta = document.getElementById('metric-receita-bruta');
const metricReceitaLiquida = document.getElementById('metric-receita-liquida');
const metricImpostosTotal = document.getElementById('metric-impostos-total');
const metricLucroBruto = document.getElementById('metric-lucro-bruto');
const metricLucroLiquido = document.getElementById('metric-lucro-liquido');
const metricMargemLiquida = document.getElementById('metric-margem-liquida');

/**
 * Calcula a receita bruta da venda (valor unitário x quantidade).
 * Atualiza os campos visuais e chama o cálculo da receita líquida.
 */
function calcularReceitaBruta() {
  let valorUnitario = inputValorUnitario ? inputValorUnitario.value.replace(/\D/g, "") : "0";
  let quantidade = inputQuantidade ? inputQuantidade.value.replace(',', '.') : "0";
  valorUnitario = parseFloat(valorUnitario) / 100 || 0;
  quantidade = parseFloat(quantidade) || 0;
  analiseData.receitaBruta = valorUnitario * quantidade;
  if (totalReceitaBrutaHeader) {
    totalReceitaBrutaHeader.innerHTML = '<span class="mbr-card-total-label">Receita Bruta</span> ' + formatarMoedaReal(analiseData.receitaBruta);
  }
  if (metricReceitaBruta) {
    metricReceitaBruta.textContent = formatarMoedaReal(analiseData.receitaBruta);
  }
  // calcularReceitaLiquida(); // Removido - será chamado após processar operações
}

/**
 * Calcula a receita líquida (receita bruta - débitos + créditos).
 * Usa os valores de débitos já calculados para evitar interferência.
 * Configurado para regime de LUCRO REAL.
 */
function calcularReceitaLiquida(totalImpostosDebito, totalImpostosCredito) {
  // Recebe os valores já calculados como parâmetros
  
  // Receita Líquida = Receita Bruta - Débitos + Créditos
  analiseData.impostosVenda = totalImpostosDebito;
  analiseData.receitaLiquida = analiseData.receitaBruta - totalImpostosDebito + totalImpostosCredito;
  
  // Atualiza apenas os campos visuais dos impostos individuais (usando os débitos calculados)
  const icmsVenda = analiseData.receitaBruta * 0.12;
  const pisVenda = analiseData.receitaBruta * 0.0165;
  const cofinsVenda = analiseData.receitaBruta * 0.076;
  
  if (metricIcmsVenda) metricIcmsVenda.textContent = "- " + formatarMoedaReal(icmsVenda);
  if (metricPisVenda) metricPisVenda.textContent = "- " + formatarMoedaReal(pisVenda);
  if (metricCofinsVenda) metricCofinsVenda.textContent = "- " + formatarMoedaReal(cofinsVenda);
  if (metricReceitaLiquida) {
    metricReceitaLiquida.textContent = formatarMoedaReal(analiseData.receitaLiquida);
  }
  if (metricImpostosTotal) {
    metricImpostosTotal.textContent = formatarMoedaReal(analiseData.impostosVenda);
  }
  atualizarResumoFinanceiro();
}

/**
 * Calcula CMV (custo mercadoria vendida) e lucro bruto.
 * Soma despesas base, impostos e acréscimos de todas as etapas.
 * Atualiza campos visuais e chama cálculo do lucro líquido.
 */
function calcularLucroBruto() {
  // 1. CUSTOS BASE (sem impostos, sem acréscimos)
  let custosBase = 0;
  let valorTonCompra = inputValorTonCompra ? inputValorTonCompra.value.replace(/\D/g, "") : "0";
  let quantidade = inputQuantidadeProduto ? inputQuantidadeProduto.value.replace(',', '.') : "0";
  valorTonCompra = parseFloat(valorTonCompra) / 100 || 0;
  quantidade = parseFloat(quantidade) || 0;
  
  custosBase += valorTonCompra * quantidade;           // Compra de mercadoria
  
  const madeiraPostaSim = radioMadeiraPostaSim && radioMadeiraPostaSim.checked;
  if (!madeiraPostaSim) {
    let valorFrete = inputValorFrete ? inputValorFrete.value.replace(/\D/g, "") : "0";
    valorFrete = parseFloat(valorFrete) / 100 || 0;
    custosBase += valorFrete * quantidade;             // Frete (se não for madeira posta)
  }
  
  let valorExtracao = inputValorExtracao ? inputValorExtracao.value.replace(/\D/g, "") : "0";
  valorExtracao = parseFloat(valorExtracao) / 100 || 0;
  custosBase += valorExtracao * quantidade;           // Extração
  
  let valorComissao = inputValorComissao ? inputValorComissao.value.replace(/\D/g, "") : "0";
  valorComissao = parseFloat(valorComissao) / 100 || 0;
  custosBase += valorComissao * quantidade;           // Comissão

  // 2. ACRÉSCIMOS (ajustes fiscais + contribuições sociais)
  let totalAcrescimos = 0;
  
  // Ajuste fiscal 5% da compra (quando não emite nota E tem documentação fiscal)
  if (compraMercadoriaData.tipoEmissao === 'nao' && compraMercadoriaData.documentacaoFiscal === 'sim') {
    totalAcrescimos += (valorTonCompra * quantidade) * 0.05;
  }
  
  // Funrural/Senar da compra (apenas quando descontado = 'nao')
  if (compraMercadoriaData.funruralDescontado === 'nao') {
    if (compraMercadoriaData.funruralSenar === 'funrural') {
      totalAcrescimos += (valorTonCompra * quantidade) * 0.015; // 1,5% FUNRURAL
    } else if (compraMercadoriaData.funruralSenar === 'senar') {
      totalAcrescimos += (valorTonCompra * quantidade) * 0.002; // 0,2% SENAR
    }
  }
  
  // Ajuste fiscal 5% do frete (quando não emite nota E tem documentação fiscal)
  if (!madeiraPostaSim && freteData.tipoEmissao === 'nao' && freteData.documentacaoFiscal === 'sim') {
    let valorFreteBase = inputValorFrete ? inputValorFrete.value.replace(/\D/g, "") : "0";
    valorFreteBase = parseFloat(valorFreteBase) / 100 || 0;
    totalAcrescimos += (valorFreteBase * quantidade) * 0.05;
  }
  
  // Ajuste fiscal 5% da extração (quando não emite nota E tem documentação fiscal)
  if (extracaoData.tipoEmissao === 'nao' && extracaoData.documentacaoFiscal === 'sim') {
    totalAcrescimos += (valorExtracao * quantidade) * 0.05;
  }
  
  // Ajuste fiscal 5% da comissão (quando não emite nota E tem documentação fiscal)
  if (comissaoData.tipoEmissao === 'nao' && comissaoData.documentacaoFiscal === 'sim') {
    totalAcrescimos += (valorComissao * quantidade) * 0.05;
  }

  // 3. IMPOSTOS DÉBITO (sobre venda)
  const icmsVenda = analiseData.receitaBruta * 0.12;
  const pisVenda = analiseData.receitaBruta * 0.0165;
  const cofinsVenda = analiseData.receitaBruta * 0.076;
  const totalImpostosDebito = icmsVenda + pisVenda + cofinsVenda;

  // 4. IMPOSTOS CRÉDITO (das operações de compra) - convertendo de centavos para reais
  const totalImpostosCredito = ((compraMercadoriaData.icms || 0) + (compraMercadoriaData.pis || 0) + (compraMercadoriaData.cofins || 0)
      + (freteData.icms || 0) + (freteData.pis || 0) + (freteData.cofins || 0)
      + (extracaoData.icms || 0) + (extracaoData.pis || 0) + (extracaoData.cofins || 0)
      + (comissaoData.icms || 0) + (comissaoData.pis || 0) + (comissaoData.cofins || 0)) / 100;

  // 5. DIFERENÇA DE IMPOSTOS (Débito - Crédito)
  const diferencaImpostos = totalImpostosDebito - totalImpostosCredito;

  // 6. CMV FINAL = Custos Base + Acréscimos
  const cmvFinal = custosBase + totalAcrescimos;

  // Calcular receita líquida ANTES de usar nos cálculos
  calcularReceitaLiquida(totalImpostosDebito, totalImpostosCredito);

  // Convertendo para centavos para manter compatibilidade com o resto do sistema
  const cmvFinalCentavos = parseInt((cmvFinal * 100).toFixed(0));
  
  if (metricTotalDespesas) {
    metricTotalDespesas.textContent = formatarParaMoedaBRL(cmvFinalCentavos);
  }
  analiseData.custosTotal = cmvFinalCentavos;

  // Lucro bruto: receita líquida - CMV
  const receitaLiquidaCentavos = parseInt((analiseData.receitaLiquida * 100).toFixed(0));
  analiseData.lucroBruto = receitaLiquidaCentavos - cmvFinalCentavos;

  if (metricCmv) {
    metricCmv.textContent = formatarParaMoedaBRL(cmvFinalCentavos);
  }
  if (metricLucroBruto) {
    metricLucroBruto.textContent = formatarParaMoedaBRL(analiseData.lucroBruto);
  }
  calcularLucroLiquido();
  atualizarResumoFinanceiro();
}

/**
 * Calcula lucro líquido usando a nova fórmula:
 * Lucro Líquido = Lucro Real - (Lucro Real × 0,09) - [(Lucro Real - Lucro Real × 0,09) × 0,15]
 * Onde Lucro Real = Lucro Bruto
 */
function calcularLucroLiquido() {
  const lucroBruto = analiseData.lucroBruto || 0;
  
  // Converter para reais para o cálculo
  const lucroReal = lucroBruto / 100;
  
  // Aplicar a nova fórmula
  // CSLL: 9% sobre o lucro real
  const csll = lucroReal * 0.09;
  
  // Base para IRPJ: Lucro Real - CSLL
  const baseIrpj = lucroReal - csll;
  
  // IRPJ: 15% sobre a base (lucro real - CSLL)
  const irpj = baseIrpj * 0.15;
  
  // Lucro Líquido = Lucro Real - CSLL - IRPJ
  const lucroLiquidoReais = lucroReal - csll - irpj;
  
  // Converter de volta para centavos
  analiseData.impostosSobreLucro = Math.round((csll + irpj) * 100);
  analiseData.lucroLiquido = Math.round(lucroLiquidoReais * 100);

  // Converter receita bruta para centavos para cálculo correto da margem
  const receitaBrutaCentavos = parseInt((analiseData.receitaBruta * 100).toFixed(0));
  analiseData.margemLiquida = receitaBrutaCentavos > 0 ?
    (analiseData.lucroLiquido / receitaBrutaCentavos) * 100 : 0;

  if (metricLucroLiquido) {
    metricLucroLiquido.textContent = formatarParaMoedaBRL(analiseData.lucroLiquido);
  }
  if (metricMargemLiquida) {
    metricMargemLiquida.textContent = analiseData.margemLiquida.toFixed(2) + '%';
  }
  
  atualizarResumoFinanceiro();
}

// ----------------------
// CONTROLE DE SERVIÇOS OPCIONAIS
// ----------------------

// Elementos dos switches
const switchExtracao = document.getElementById('switch-extracao');
const switchComissao = document.getElementById('switch-comissao');

// Função para controlar visibilidade do card de extração
function controlarExtracao() {
  const cardExtracao = document.getElementById('card-extracao');
  const isAtivo = switchExtracao && switchExtracao.checked;

  if (cardExtracao) {
    if (isAtivo) {
      cardExtracao.classList.remove('oculto');
      cardExtracao.style.display = '';
    } else {
      cardExtracao.classList.add('oculto');
      setTimeout(() => {
        cardExtracao.style.display = 'none';
      }, 400);

      // Zera os dados quando desativado
      extracaoData.total = 0;
      extracaoData.icms = 0;
      extracaoData.pis = 0;
      extracaoData.cofins = 0;
      extracaoData.acrescimos = 0;
    }
  }

  atualizarCardsServicos();
  calcularLucroBruto();
  atualizarResumoImpostos();
  atualizarTabelaAcrescimos();
}

// Função para controlar visibilidade do card de comissão
function controlarComissao() {
  const cardComissao = document.getElementById('card-comissao');
  const isAtivo = switchComissao && switchComissao.checked;

  if (cardComissao) {
    if (isAtivo) {
      cardComissao.classList.remove('oculto');
      cardComissao.style.display = '';
    } else {
      cardComissao.classList.add('oculto');
      setTimeout(() => {
        cardComissao.style.display = 'none';
      }, 400);

      // Zera os dados quando desativado
      comissaoData.total = 0;
      comissaoData.icms = 0;
      comissaoData.pis = 0;
      comissaoData.cofins = 0;
      comissaoData.acrescimos = 0;
    }
  }

  atualizarCardsServicos();
  calcularLucroBruto();
  atualizarResumoImpostos();
  atualizarTabelaAcrescimos();
}

// Event listeners para os switches
if (switchExtracao) {
  switchExtracao.addEventListener('change', controlarExtracao);
}

if (switchComissao) {
  switchComissao.addEventListener('change', controlarComissao);
}


// ----------------------
// ETAPA: DADOS DO PRODUTO
// ----------------------
// Elementos da área de dados do produto
const inputValorUnitario = document.querySelector('.mbr-section .campo-moeda-brl');
const inputQuantidade = document.querySelector('.mbr-section .campo-float');
const totalProduto = document.querySelector('.mbr-card .mbr-total-value');
const radioMadeiraPostaSim = document.getElementById('madeira-posta-sim');
const radioMadeiraPostaNao = document.getElementById('madeira-posta-nao');
const cardFrete = document.getElementById('card-frete');
const cardExtracao = document.getElementById('card-extracao');
const cardComissao = document.getElementById('card-comissao');

// Calcula e atualiza o total do produto
function calcularTotalProduto() {
  let valorUnitario = inputValorUnitario.value.replace(/\D/g, "");
  let quantidade = inputQuantidade.value.replace(',', '.');
  valorUnitario = parseFloat(valorUnitario) || 0;
  quantidade = parseFloat(quantidade) || 0;
  let total = valorUnitario * quantidade;
  totalProduto.textContent = formatarParaMoedaBRL(total);
  calcularReceitaBruta();
}

function atualizarCardsServicos() {
  if (radioMadeiraPostaSim && radioMadeiraPostaSim.checked) {
    // Esconde o card do frete
    if (cardFrete) cardFrete.style.display = 'none';

    // FORÇA o reset dos dados do frete IMEDIATAMENTE
    freteData.total = 0;
    freteData.icms = 0;
    freteData.pis = 0;
    freteData.cofins = 0;
    freteData.acrescimos = 0;
    freteData.tipoEmissao = '';
    freteData.tipoPrestador = '';
    freteData.tipoNota = '';
    freteData.origem = '';
    freteData.destino = '';

    // Limpa todos os campos visuais do frete
    if (inputValorFrete) inputValorFrete.value = '';
    if (radioEmiteNotaFreteSim) radioEmiteNotaFreteSim.checked = false;
    if (radioEmiteNotaFreteNao) radioEmiteNotaFreteNao.checked = false;
    if (selectOrigemFrete) selectOrigemFrete.selectedIndex = 0;
    if (selectDestinoFrete) selectDestinoFrete.selectedIndex = 0;
    if (selectPrestadorFrete) selectPrestadorFrete.selectedIndex = 0;
    if (selectTipoNotaFrete) selectTipoNotaFrete.selectedIndex = 0;

    // Limpa campos visuais de impostos
    if (valorIcmsFrete) valorIcmsFrete.value = '';
    if (valorPisFrete) valorPisFrete.value = '';
    if (valorCofinsFrete) valorCofinsFrete.value = '';
    if (valorSemNotaFrete) valorSemNotaFrete.value = '';

    // Esconde áreas de impostos do frete
    if (areaImpostosFrete) areaImpostosFrete.style.display = 'none';
    if (areaAcrescimosFrete) areaAcrescimosFrete.style.display = 'none';
    if (areaSemImpostosFrete) areaSemImpostosFrete.style.display = 'block';

    // Ajusta colunas dos outros serviços
    if (cardExtracao) {
      cardExtracao.classList.remove('col-lg-4');
      cardExtracao.classList.add('col-lg-6');
    }
    if (cardComissao) {
      cardComissao.classList.remove('col-lg-4');
      cardComissao.classList.add('col-lg-6');
    }

    // FORÇA atualização imediata das tabelas
    atualizarResumoImpostos();
    atualizarTabelaAcrescimos();
    calcularLucroBruto();

  } else {
    // Mostra o card do frete
    if (cardFrete) cardFrete.style.display = '';

    // Ajusta colunas de volta ao normal
    if (cardExtracao) {
      cardExtracao.classList.remove('col-lg-6');
      cardExtracao.classList.add('col-lg-4');
    }
    if (cardComissao) {
      cardComissao.classList.remove('col-lg-6');
      cardComissao.classList.add('col-lg-4');
    }

    // Recalcula com os valores atuais
    calcularFrete();
    atualizarResumoImpostos();
    calcularLucroBruto();
  }
}

// Campos obrigatórios: impede ação se não preencher
function validarCamposProduto() {
  if (!inputValorUnitario.value || !inputQuantidade.value) {
    return false;
  }
  return true;
}

// Eventos dinâmicos
if (inputValorUnitario) inputValorUnitario.addEventListener('input', calcularTotalProduto);
if (inputQuantidade) inputQuantidade.addEventListener('input', calcularTotalProduto);
if (radioMadeiraPostaSim) radioMadeiraPostaSim.addEventListener('change', atualizarCardsServicos);
if (radioMadeiraPostaNao) radioMadeiraPostaNao.addEventListener('change', atualizarCardsServicos);

// Inicializa valores ao carregar
window.addEventListener('DOMContentLoaded', function () {
  calcularTotalProduto();
  atualizarCardsServicos();
});

// ----------------------
// ETAPA: COMPRA DE MERCADORIA
// ----------------------
// Objeto para armazenar os valores calculados da etapa de compra
const compraMercadoriaData = {
  total: 0, // valor total da compra
  icms: 0,
  pis: 0,
  cofins: 0,
  acrescimos: 0, // acréscimos de funrural/senar ou sem nota
  tipoEmissao: '', // 'sim' ou 'nao'
  funruralDescontado: '',
  funruralSenar: '', // 'sim' ou 'nao'
  origem: '',
  destino: '',
  tipoFornecedor: ''
};

// --- Elementos da Compra de Mercadoria ---
const radioEmiteNotaCompraSim = document.querySelector('input[name="emite_nota_compra"][value="sim"]');
const radioEmiteNotaCompraNao = document.querySelector('input[name="emite_nota_compra"][value="nao"]');
const radioFunruralSim = document.querySelector('input[name="funrural"][value="funrural"]');
const radioFunruralNao = document.querySelector('input[name="funrural"][value="senar"]');
const selectEstadoOrigem = document.getElementById('select-estado-origem');
const selectEstadoDestino = document.getElementById('select-estado-destino');
const selectClassFiscal = document.getElementById('select-class-fiscal');
const inputValorTonCompra = document.getElementById('input-valor-ton-compra');
const inputQuantidadeProduto = document.querySelector('.mbr-section .campo-float');
const totalCompraMercadoria = document.querySelectorAll('.mbr-card .mbr-total-value')[1];


// Áreas de exibição de impostos
const areaImpostos = document.getElementById('area-impostos');
const areaAcrescimos = document.getElementById('area-acrescimos');
const areaSemImpostos = document.getElementById('area-sem-impostos');
const areaFunruralComNota = document.getElementById('area-funrural-com-nota');
const areaFunruralSemNota = document.getElementById('area-funrural-sem-nota');

// Campos de valores
const valorIcms = document.getElementById('valor-icms');
const valorPis = document.getElementById('valor-pis');
const valorCofins = document.getElementById('valor-cofins');
const valorFunruralComNota = document.getElementById('valor-funrural-com-nota');
const valorSemNota = document.getElementById('valor-sem-nota');
const valorFunruralSemNota = document.getElementById('valor-funrural-sem-nota');

// Elementos para mostrar as porcentagens
const percentFunruralComNota = document.getElementById('percent-funrural-com-nota');
const percentFunruralSemNota = document.getElementById('percent-funrural-sem-nota');

// Função para atualizar as referências de porcentagem
function atualizarReferenciasContribuicao() {
  const tipoContribuicao = compraMercadoriaData.funruralSenar;
  const descontado = compraMercadoriaData.funruralDescontado;

  let textoReferencia = '';

  // Sempre mostra a porcentagem correta independente se foi descontado ou não
  if (tipoContribuicao === 'funrural') {
    textoReferencia = '(1,5%)';
  } else if (tipoContribuicao === 'senar') {
    textoReferencia = '(0,2%)';
  }

  // Atualiza ambos os campos
  if (percentFunruralComNota) {
    percentFunruralComNota.textContent = textoReferencia;
  }
  if (percentFunruralSemNota) {
    percentFunruralSemNota.textContent = textoReferencia;
  }
}

// Função para mostrar/ocultar campos conforme emissão de nota
function atualizarCamposCompra() {
  const areaDocFiscal = document.getElementById('area-doc-fiscal-compra');
  const areaFunruralDescontado = document.getElementById('area-funrural-descontado');

  if (radioEmiteNotaCompraNao && radioEmiteNotaCompraNao.checked) {
    if (areaDocFiscal) areaDocFiscal.style.display = '';
    if (selectEstadoOrigem) selectEstadoOrigem.parentElement.style.display = '';
    if (selectEstadoDestino) selectEstadoDestino.parentElement.style.display = '';
    if (selectClassFiscal) selectClassFiscal.parentElement.style.display = '';
  } else if (radioEmiteNotaCompraSim && radioEmiteNotaCompraSim.checked) {
    if (areaDocFiscal) areaDocFiscal.style.display = 'none';
    if (selectEstadoOrigem) selectEstadoOrigem.parentElement.style.display = '';
    if (selectEstadoDestino) selectEstadoDestino.parentElement.style.display = '';
    if (selectClassFiscal) selectClassFiscal.parentElement.style.display = '';
  } else {
    if (areaDocFiscal) areaDocFiscal.style.display = 'none';
    if (selectEstadoOrigem) selectEstadoOrigem.parentElement.style.display = '';
    if (selectEstadoDestino) selectEstadoDestino.parentElement.style.display = '';
    if (selectClassFiscal) selectClassFiscal.parentElement.style.display = '';
  }

  // Campo de contribuição descontada sempre visível pois sempre há Funrural ou Senar
  if (areaFunruralDescontado) areaFunruralDescontado.style.display = '';
}

// Função para atualizar a exibição dos impostos/acréscimos
function atualizarExibicaoImpostos() {
  const emiteNota = radioEmiteNotaCompraSim && radioEmiteNotaCompraSim.checked;
  const naoEmiteNota = radioEmiteNotaCompraNao && radioEmiteNotaCompraNao.checked;

  // Esconde todas as áreas primeiro
  if (areaImpostos) areaImpostos.style.display = 'none';
  if (areaAcrescimos) areaAcrescimos.style.display = 'none';
  if (areaSemImpostos) areaSemImpostos.style.display = 'none';
  if (areaFunruralComNota) areaFunruralComNota.style.display = 'none';
  if (areaFunruralSemNota) areaFunruralSemNota.style.display = 'none';

  if (naoEmiteNota) {
    // SEM NOTA FISCAL: Mostra impostos (créditos) E acréscimos
    if (areaImpostos) areaImpostos.style.display = 'block';
    if (areaAcrescimos) areaAcrescimos.style.display = 'block';

    // Sempre mostra campo de contribuição (Funrural ou Senar)
    if (areaFunruralSemNota) {
      areaFunruralSemNota.style.display = 'block';
    }
  } else if (emiteNota) {
    // COM NOTA FISCAL: Mostra apenas impostos normais
    if (areaImpostos) areaImpostos.style.display = 'block';

    // Sempre mostra campo de contribuição (Funrural ou Senar)
    if (areaFunruralComNota) {
      areaFunruralComNota.style.display = 'block';
    }
  } else {
    // NENHUMA OPÇÃO: Mensagem padrão
    if (areaSemImpostos) areaSemImpostos.style.display = 'block';
  }
}

// Função para calcular total da compra e impostos
function calcularCompraMercadoria() {
  compraMercadoriaData.tipoEmissao = radioEmiteNotaCompraSim && radioEmiteNotaCompraSim.checked ? 'sim' : 'nao';
  compraMercadoriaData.funruralSenar = radioFunruralSim && radioFunruralSim.checked ? 'funrural' : 'senar';
  const radioFunruralDescontadoSim = document.querySelector('input[name="funrural_descontado"][value="sim"]');
  compraMercadoriaData.funruralDescontado = radioFunruralDescontadoSim && radioFunruralDescontadoSim.checked ? 'sim' : 'nao';
  const radioDocFiscalSim = document.querySelector('input[name="doc_fiscal_compra"][value="sim"]');
  compraMercadoriaData.documentacaoFiscal = radioDocFiscalSim && radioDocFiscalSim.checked ? 'sim' : 'nao';
  compraMercadoriaData.origem = selectEstadoOrigem ? selectEstadoOrigem.value : '';
  compraMercadoriaData.destino = selectEstadoDestino ? selectEstadoDestino.value : '';
  compraMercadoriaData.tipoFornecedor = selectClassFiscal ? selectClassFiscal.value : '';

  // Atualiza as referências de porcentagem nos labels
  atualizarReferenciasContribuicao();

  // Calcula o total base da compra
  let valorTonCentavos = inputValorTonCompra ? inputValorTonCompra.value.replace(/\D/g, "") : "0";
  let quantidade = inputQuantidadeProduto ? inputQuantidadeProduto.value.replace(',', '.') : "0";

  // Converte para valores numéricos
  valorTonCentavos = parseFloat(valorTonCentavos) || 0;
  quantidade = parseFloat(quantidade) || 0;

  // Calcula total base e já fixa em 2 casas decimais
  let totalCompraReais = parseFloat(((valorTonCentavos / 100) * quantidade).toFixed(2));

  let icms = 0, pis = 0, cofins = 0, acrescimos = 0, funruralValor = 0;

  // LÓGICA DE CRÉDITOS FISCAIS:
  // Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
  // Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
  // Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
  const emiteNota = compraMercadoriaData.tipoEmissao === 'sim';
  const ajusteFiscal = compraMercadoriaData.documentacaoFiscal === 'sim';
  const geraCreditos = emiteNota || (!emiteNota && ajusteFiscal);

  // Calcula impostos APENAS quando gera créditos
  if (geraCreditos) {
    if ((compraMercadoriaData.destino === 'RS' && compraMercadoriaData.origem === 'SC' && compraMercadoriaData.tipoFornecedor === 'PR_PF') ||
      (compraMercadoriaData.destino === 'SC' && compraMercadoriaData.origem === 'RS' && compraMercadoriaData.tipoFornecedor === 'PR_PF')) {
      icms = parseFloat((totalCompraReais * 0.12).toFixed(2));
      pis = 0;
      cofins = 0;
    } else if ([
      'PR_PJ_SIMPLES', 'PJ_SIMPLES'
    ].includes(compraMercadoriaData.tipoFornecedor)) {
      icms = 0;
      pis = parseFloat((totalCompraReais * 0.0165).toFixed(2));
      cofins = parseFloat((totalCompraReais * 0.076).toFixed(2));
    } else if ([
      'PR_PJ_REAL', 'PJ_REAL', 'PR_PJ_REAL/PRESUMIDO', 'PJ_REAL/PRESUMIDO'
    ].includes(compraMercadoriaData.tipoFornecedor)) {
      if ((compraMercadoriaData.destino === 'RS' && compraMercadoriaData.origem === 'SC') ||
        (compraMercadoriaData.destino === 'SC' && compraMercadoriaData.origem === 'RS') ||
        (compraMercadoriaData.destino === 'RS' && compraMercadoriaData.origem === 'RS')) {
        icms = parseFloat((totalCompraReais * 0.12).toFixed(2));
      } else {
        icms = 0;
      }
      pis = parseFloat((totalCompraReais * 0.0165).toFixed(2));
      cofins = parseFloat((totalCompraReais * 0.076).toFixed(2));
    }
  }

  // SEMPRE calcula Funrural/Senar para exibir na área de impostos
  if (compraMercadoriaData.funruralSenar === 'funrural') {
    funruralValor = parseFloat((totalCompraReais * 0.015).toFixed(2)); // 1,5% FUNRURAL
  } else if (compraMercadoriaData.funruralSenar === 'senar') {
    funruralValor = parseFloat((totalCompraReais * 0.002).toFixed(2)); // 0,2% SENAR
  }

  // Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
  if (!emiteNota && ajusteFiscal) {
    acrescimos = parseFloat((totalCompraReais * 0.05).toFixed(2));
  } else {
    acrescimos = 0;
  }

  // Atualiza campos visuais (valores em centavos para formatação)
  if (compraMercadoriaData.tipoEmissao === 'nao') {
    // SEM NOTA FISCAL
    if (valorIcms) valorIcms.value = formatarParaMoedaBRL(parseInt((icms * 100).toFixed(0)));
    if (valorPis) valorPis.value = formatarParaMoedaBRL(parseInt((pis * 100).toFixed(0)));
    if (valorCofins) valorCofins.value = formatarParaMoedaBRL(parseInt((cofins * 100).toFixed(0)));
    if (valorSemNota) valorSemNota.value = formatarParaMoedaBRL(parseInt((acrescimos * 100).toFixed(0)));
    if (valorFunruralSemNota) valorFunruralSemNota.value = formatarParaMoedaBRL(parseInt((funruralValor * 100).toFixed(0)));
  } else {
    // COM NOTA FISCAL
    if (valorIcms) valorIcms.value = formatarParaMoedaBRL(parseInt((icms * 100).toFixed(0)));
    if (valorPis) valorPis.value = formatarParaMoedaBRL(parseInt((pis * 100).toFixed(0)));
    if (valorCofins) valorCofins.value = formatarParaMoedaBRL(parseInt((cofins * 100).toFixed(0)));
    if (valorFunruralComNota) valorFunruralComNota.value = formatarParaMoedaBRL(parseInt((funruralValor * 100).toFixed(0)));
  }

  // CÁLCULO DO TOTAL FINAL DA COMPRA:
  // Total = (quantidade * valor R$/ton) + acréscimos fiscais + funrural/senar (quando não descontado)
  let totalFinalReais = totalCompraReais;

  // Soma acréscimo fiscal (5%) quando aplicável
  totalFinalReais += acrescimos;

  // Soma Funrural/Senar apenas se descontado = 'nao' (empresa precisa pagar)
  if (compraMercadoriaData.funruralDescontado === 'nao') {
    totalFinalReais += funruralValor;
  }

  // Guarda valores em centavos para compatibilidade
  compraMercadoriaData.total = parseInt((totalFinalReais * 100).toFixed(0));
  compraMercadoriaData.icms = parseInt((icms * 100).toFixed(0));
  compraMercadoriaData.pis = parseInt((pis * 100).toFixed(0));
  compraMercadoriaData.cofins = parseInt((cofins * 100).toFixed(0));
  
  // Acréscimos inclui apenas documentação fiscal (5%) e funrural quando necessário
  if (compraMercadoriaData.funruralDescontado === 'nao') {
    compraMercadoriaData.acrescimos = parseInt(((acrescimos + funruralValor) * 100).toFixed(0));
  } else {
    // Quando funrural é descontado, não conta como acréscimo no total
    compraMercadoriaData.acrescimos = parseInt((acrescimos * 100).toFixed(0));
  }

  if (totalCompraMercadoria) {
    totalCompraMercadoria.textContent = formatarParaMoedaBRL(compraMercadoriaData.total);
  }

  // Atualiza exibição
  atualizarExibicaoImpostos();
  calcularLucroBruto();
  atualizarResumoImpostos();
  atualizarTabelaAcrescimos();
}


// Eventos para atualização dinâmica
if (radioEmiteNotaCompraSim) radioEmiteNotaCompraSim.addEventListener('change', function () {
  atualizarCamposCompra();
  calcularCompraMercadoria();
});
if (radioEmiteNotaCompraNao) radioEmiteNotaCompraNao.addEventListener('change', function () {
  atualizarCamposCompra();
  calcularCompraMercadoria();
});
if (inputValorTonCompra) inputValorTonCompra.addEventListener('input', calcularCompraMercadoria);
if (inputQuantidadeProduto) inputQuantidadeProduto.addEventListener('input', calcularCompraMercadoria);
if (radioFunruralSim) radioFunruralSim.addEventListener('change', calcularCompraMercadoria);
if (radioFunruralNao) radioFunruralNao.addEventListener('change', calcularCompraMercadoria);
if (selectEstadoOrigem) selectEstadoOrigem.addEventListener('change', calcularCompraMercadoria);
if (selectEstadoDestino) selectEstadoDestino.addEventListener('change', calcularCompraMercadoria);
if (selectClassFiscal) selectClassFiscal.addEventListener('change', calcularCompraMercadoria);
if (selectClassFiscal) selectClassFiscal.addEventListener('change', calcularCompraMercadoria);

const radioDocFiscalCompraSim = document.querySelector('input[name="doc_fiscal_compra"][value="sim"]');
const radioDocFiscalCompraNao = document.querySelector('input[name="doc_fiscal_compra"][value="nao"]');
if (radioDocFiscalCompraSim) radioDocFiscalCompraSim.addEventListener('change', calcularCompraMercadoria);
if (radioDocFiscalCompraNao) radioDocFiscalCompraNao.addEventListener('change', calcularCompraMercadoria);

const radioFunruralDescontadoSim = document.querySelector('input[name="funrural_descontado"][value="sim"]');
const radioFunruralDescontadoNao = document.querySelector('input[name="funrural_descontado"][value="nao"]');
if (radioFunruralDescontadoSim) radioFunruralDescontadoSim.addEventListener('change', calcularCompraMercadoria);
if (radioFunruralDescontadoNao) radioFunruralDescontadoNao.addEventListener('change', calcularCompraMercadoria);

if (radioFunruralSim) radioFunruralSim.addEventListener('change', function () {
  atualizarCamposCompra();
  calcularCompraMercadoria();
});
if (radioFunruralNao) radioFunruralNao.addEventListener('change', function () {
  atualizarCamposCompra();
  calcularCompraMercadoria();
});

// Inicialização
window.addEventListener('DOMContentLoaded', function () {
  atualizarCamposCompra();
  atualizarExibicaoImpostos();
  calcularCompraMercadoria();
});

// Utiliza a máscara já existente do sistema
if (typeof aplicarMascaraMoeda === 'function') {
  aplicarMascaraMoeda();
}

// ----------------------
// ETAPA: FRETE
// ----------------------
const freteData = {
  total: 0,
  icms: 0,
  pis: 0,
  cofins: 0,
  acrescimos: 0,
  tipoEmissao: '',
  tipoPrestador: '',
  tipoNota: '',
  origem: '',
  destino: ''
};

// Elementos da área de frete
const radioEmiteNotaFreteSim = document.getElementById('radio-frete-sim');
const radioEmiteNotaFreteNao = document.getElementById('radio-frete-nao');
const selectOrigemFrete = document.getElementById('select-origem-frete');
const selectDestinoFrete = document.getElementById('select-destino-frete');
const selectPrestadorFrete = document.getElementById('select-prestador-frete');
const selectTipoNotaFrete = document.getElementById('select-tipo-nota-frete');
const inputValorFrete = document.getElementById('input-valor-frete');
const totalFrete = document.querySelectorAll('.mbr-card .mbr-total-value')[2];

// Áreas de exibição de impostos - Frete
const areaImpostosFrete = document.getElementById('area-impostos-frete');
const areaAcrescimosFrete = document.getElementById('area-acrescimos-frete');
const areaSemImpostosFrete = document.getElementById('area-sem-impostos-frete');

// Campos de valores - Frete
const valorIcmsFrete = document.getElementById('valor-icms-frete');
const valorPisFrete = document.getElementById('valor-pis-frete');
const valorCofinsFrete = document.getElementById('valor-cofins-frete');
const valorSemNotaFrete = document.getElementById('valor-sem-nota-frete');

// Função para atualizar exibição dos impostos - Frete
function atualizarExibicaoImpostosFrete() {
  const emiteNota = radioEmiteNotaFreteSim && radioEmiteNotaFreteSim.checked;
  const naoEmiteNota = radioEmiteNotaFreteNao && radioEmiteNotaFreteNao.checked;

  // Esconde todas as áreas primeiro
  if (areaImpostosFrete) areaImpostosFrete.style.display = 'none';
  if (areaAcrescimosFrete) areaAcrescimosFrete.style.display = 'none';
  if (areaSemImpostosFrete) areaSemImpostosFrete.style.display = 'none';

  if (naoEmiteNota) {
    // SEM NOTA FISCAL: Mostra impostos (créditos) E acréscimos
    if (areaImpostosFrete) areaImpostosFrete.style.display = 'block';
    if (areaAcrescimosFrete) areaAcrescimosFrete.style.display = 'block';
  } else if (emiteNota) {
    // COM NOTA FISCAL: Esconde campo de documentação fiscal
    if (areaImpostosFrete) areaImpostosFrete.style.display = 'block';
  } else {
    if (areaSemImpostosFrete) areaSemImpostosFrete.style.display = 'block';
  }
}

// Função para calcular impostos do frete
function calcularFrete() {
  // Verifica se madeira posta está marcada como SIM
  const madeiraPostaSim = radioMadeiraPostaSim && radioMadeiraPostaSim.checked;

  if (madeiraPostaSim) {
    // Se madeira posta = SIM, zera tudo
    freteData.total = 0;
    freteData.icms = 0;
    freteData.pis = 0;
    freteData.cofins = 0;
    freteData.acrescimos = 0;

    if (totalFrete) {
      totalFrete.textContent = 'R$ 0,00';
    }
    return;
  }

  // Captura dados
  freteData.tipoEmissao = radioEmiteNotaFreteSim && radioEmiteNotaFreteSim.checked ? 'sim' : 'nao';
  const radioDocFiscalSim = document.querySelector('input[name="doc_fiscal_frete"][value="sim"]');
  freteData.documentacaoFiscal = radioDocFiscalSim && radioDocFiscalSim.checked ? 'sim' : 'nao';
  freteData.tipoPrestador = selectPrestadorFrete ? selectPrestadorFrete.value : '';
  freteData.tipoNota = selectTipoNotaFrete ? selectTipoNotaFrete.value : '';
  freteData.origem = selectOrigemFrete ? selectOrigemFrete.value : '';
  freteData.destino = selectDestinoFrete ? selectDestinoFrete.value : '';

  // Converte centavos para reais e calcula total base
  let valorFreteCentavos = inputValorFrete ? inputValorFrete.value.replace(/\D/g, "") : "0";
  let quantidade = inputQuantidadeProduto ? inputQuantidadeProduto.value.replace(',', '.') : "1";

  valorFreteCentavos = parseFloat(valorFreteCentavos) || 0;  // Valor em centavos
  quantidade = parseFloat(quantidade) || 1;

  // Calcula total base e já fixa em 2 casas decimais
  let totalFreteReais = parseFloat(((valorFreteCentavos / 100) * quantidade).toFixed(2));

  let icms = 0, pis = 0, cofins = 0, acrescimos = 0;

  // LÓGICA DE CRÉDITOS FISCAIS:
  // Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
  // Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
  // Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
  const emiteNota = freteData.tipoEmissao === 'sim';
  const ajusteFiscal = freteData.documentacaoFiscal === 'sim';
  const geraCreditos = emiteNota || (!emiteNota && ajusteFiscal);

  if (geraCreditos) {
    if (freteData.tipoPrestador === 'PJ_SIMPLES') {
      icms = 0;
      if (freteData.tipoNota === 'CTE') {
        pis = parseFloat((totalFreteReais * 0.012375).toFixed(2)); // 1,2375%
        cofins = parseFloat((totalFreteReais * 0.057).toFixed(2)); // 5,7%
      } else if (freteData.tipoNota === 'SERVICO') {
        pis = parseFloat((totalFreteReais * 0.0165).toFixed(2)); // 1,65%
        cofins = parseFloat((totalFreteReais * 0.076).toFixed(2)); // 7,6%
      }
    } else if (freteData.tipoPrestador === 'PJ_REAL') {
      pis = parseFloat((totalFreteReais * 0.0165).toFixed(2)); // 1,65%
      cofins = parseFloat((totalFreteReais * 0.076).toFixed(2)); // 7,6%

      if (freteData.tipoNota === 'CTE') {
        // ICMS apenas se origem diferente do destino
        if (freteData.origem !== freteData.destino) {
          icms = parseFloat((totalFreteReais * 0.12).toFixed(2)); // 12%
        } else {
          icms = 0;
        }
      } else if (freteData.tipoNota === 'SERVICO') {
        icms = 0; // Nota de serviço não tem ICMS
      }
    }
  }

  // Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
  if (!emiteNota && ajusteFiscal) {
    acrescimos = parseFloat((totalFreteReais * 0.05).toFixed(2));
  } else {
    acrescimos = 0;
  }

  // CÁLCULO DO TOTAL FINAL DO FRETE:
  // Total = valor_base + acréscimos fiscais (ICMS, PIS, COFINS NÃO somam)
  let totalFinalReais = totalFreteReais + acrescimos;

  // Guarda valores em centavos para compatibilidade
  freteData.total = parseInt((totalFinalReais * 100).toFixed(0));
  freteData.icms = parseInt((icms * 100).toFixed(0));
  freteData.pis = parseInt((pis * 100).toFixed(0));
  freteData.cofins = parseInt((cofins * 100).toFixed(0));
  freteData.acrescimos = parseInt((acrescimos * 100).toFixed(0));

  // Atualiza campos visuais (valores em centavos para formatação)
  if (valorIcmsFrete) valorIcmsFrete.value = formatarParaMoedaBRL(parseInt((icms * 100).toFixed(0)));
  if (valorPisFrete) valorPisFrete.value = formatarParaMoedaBRL(parseInt((pis * 100).toFixed(0)));
  if (valorCofinsFrete) valorCofinsFrete.value = formatarParaMoedaBRL(parseInt((cofins * 100).toFixed(0)));
  if (valorSemNotaFrete) valorSemNotaFrete.value = formatarParaMoedaBRL(parseInt((acrescimos * 100).toFixed(0)));

  // Atualiza total
  if (totalFrete) {
    totalFrete.textContent = formatarParaMoedaBRL(freteData.total);
  }

  // Atualiza exibição
  atualizarExibicaoImpostosFrete();
  calcularLucroBruto();
  atualizarResumoImpostos();
  atualizarTabelaAcrescimos();
}

// Função para mostrar/ocultar campos conforme emissão de nota - FRETE
function atualizarCamposFrete() {
  const areaDocFiscal = document.getElementById('area-doc-fiscal-frete');

  if (radioEmiteNotaFreteNao && radioEmiteNotaFreteNao.checked) {
    // SEM NOTA FISCAL: Mostra campo de documentação fiscal
    if (areaDocFiscal) areaDocFiscal.style.display = '';

    // Esconde campos quando NÃO emite nota
    if (selectOrigemFrete) selectOrigemFrete.parentElement.style.display = '';
    if (selectDestinoFrete) selectDestinoFrete.parentElement.style.display = '';
    if (selectPrestadorFrete) selectPrestadorFrete.parentElement.style.display = '';
    if (selectTipoNotaFrete) selectTipoNotaFrete.parentElement.style.display = '';
  } else if (radioEmiteNotaFreteSim && radioEmiteNotaFreteSim.checked) {
    // COM NOTA FISCAL: Esconde campo de documentação fiscal
    if (areaDocFiscal) areaDocFiscal.style.display = 'none';

    // Mostra campos quando SIM emite nota
    if (selectOrigemFrete) selectOrigemFrete.parentElement.style.display = '';
    if (selectDestinoFrete) selectDestinoFrete.parentElement.style.display = '';
    if (selectPrestadorFrete) selectPrestadorFrete.parentElement.style.display = '';
    if (selectTipoNotaFrete) selectTipoNotaFrete.parentElement.style.display = '';
  } else {
    if (areaDocFiscal) areaDocFiscal.style.display = 'none';
    if (selectOrigemFrete) selectOrigemFrete.parentElement.style.display = '';
    if (selectDestinoFrete) selectDestinoFrete.parentElement.style.display = '';
    if (selectPrestadorFrete) selectPrestadorFrete.parentElement.style.display = '';
    if (selectTipoNotaFrete) selectTipoNotaFrete.parentElement.style.display = '';
  }
}

// Event listeners para frete
if (radioEmiteNotaFreteSim) radioEmiteNotaFreteSim.addEventListener('change', function () {
  atualizarCamposFrete();
  calcularFrete();
});
if (radioEmiteNotaFreteNao) radioEmiteNotaFreteNao.addEventListener('change', function () {
  atualizarCamposFrete();
  calcularFrete();
});
if (radioEmiteNotaFreteSim) radioEmiteNotaFreteSim.addEventListener('change', calcularFrete);
if (radioEmiteNotaFreteNao) radioEmiteNotaFreteNao.addEventListener('change', calcularFrete);
if (selectOrigemFrete) selectOrigemFrete.addEventListener('change', calcularFrete);
if (selectDestinoFrete) selectDestinoFrete.addEventListener('change', calcularFrete);
if (selectPrestadorFrete) selectPrestadorFrete.addEventListener('change', calcularFrete);
if (selectTipoNotaFrete) selectTipoNotaFrete.addEventListener('change', calcularFrete);
if (inputValorFrete) inputValorFrete.addEventListener('input', calcularFrete);

const radioDocFiscalFreteSim = document.querySelector('input[name="doc_fiscal_frete"][value="sim"]');
const radioDocFiscalFreteNao = document.querySelector('input[name="doc_fiscal_frete"][value="nao"]');
if (radioDocFiscalFreteSim) radioDocFiscalFreteSim.addEventListener('change', calcularFrete);
if (radioDocFiscalFreteNao) radioDocFiscalFreteNao.addEventListener('change', calcularFrete);

// Inicialização do frete
window.addEventListener('DOMContentLoaded', function () {
  atualizarExibicaoImpostosFrete();
  calcularFrete();

  if (typeof aplicarMascaraMoeda === 'function') {
    aplicarMascaraMoeda();
  }
});

// ----------------------
// ETAPA: EXTRAÇÃO
// ----------------------
const extracaoData = {
  total: 0,
  icms: 0,
  pis: 0,
  cofins: 0,
  acrescimos: 0,
  tipoEmissao: '',
  tipoPrestador: ''
};

// Elementos da área de extração
const radioEmiteNotaExtracaoSim = document.getElementById('radio-extracao-sim');
const radioEmiteNotaExtracaoNao = document.getElementById('radio-extracao-nao');
const selectPrestadorExtracao = document.getElementById('select-prestador-extracao');
const inputValorExtracao = document.getElementById('input-valor-extracao');
const totalExtracao = document.querySelectorAll('.mbr-card .mbr-total-value')[3];

// Áreas de exibição de impostos - Extração
const areaImpostosExtracao = document.getElementById('area-impostos-extracao');
const areaAcrescimosExtracao = document.getElementById('area-acrescimos-extracao');
const areaSemImpostosExtracao = document.getElementById('area-sem-impostos-extracao');

// Campos de valores - Extração
const valorIcmsExtracao = document.getElementById('valor-icms-extracao');
const valorPisExtracao = document.getElementById('valor-pis-extracao');
const valorCofinsExtracao = document.getElementById('valor-cofins-extracao');
const valorSemNotaExtracao = document.getElementById('valor-sem-nota-extracao');

// Função para mostrar/ocultar campos conforme emissão de nota - EXTRAÇÃO
function atualizarCamposExtracao() {
  const colPrestador = document.getElementById('col-prestador-extracao');
  const colValor = document.getElementById('col-valor-extracao');

  const areaDocExtracao = document.getElementById('area-doc-fiscal-extracao');

  if (radioEmiteNotaExtracaoNao && radioEmiteNotaExtracaoNao.checked) {
    if (areaDocExtracao) areaDocExtracao.style.display = '';
    // Esconde prestador e valor ocupa col-12
    if (colPrestador) colPrestador.style.display = '';
    // if (colValor) {
    //     colValor.classList.remove('col-md-6');
    //     colValor.classList.add('col-md-12');
    // }
  } else if (radioEmiteNotaExtracaoSim && radioEmiteNotaExtracaoSim.checked) {
    if (areaDocExtracao) areaDocExtracao.style.display = 'none';
    // Mostra prestador e valor volta para col-6
    if (colPrestador) colPrestador.style.display = '';
    // if (colValor) {
    //     colValor.classList.remove('col-md-12');
    //     colValor.classList.add('col-md-6');
    // }
  } else {
    if (areaDocExtracao) areaDocExtracao.style.display = 'none';
    if (colPrestador) colPrestador.style.display = '';
    // if (colValor) {
    //     colValor.classList.remove('col-md-12');
    //     colValor.classList.add('col-md-6');
    // }
  }
}

// Função para atualizar exibição dos impostos - Extração
function atualizarExibicaoImpostosExtracao() {
  const emiteNota = radioEmiteNotaExtracaoSim && radioEmiteNotaExtracaoSim.checked;
  const naoEmiteNota = radioEmiteNotaExtracaoNao && radioEmiteNotaExtracaoNao.checked;

  // Esconde todas as áreas primeiro
  if (areaImpostosExtracao) areaImpostosExtracao.style.display = 'none';
  if (areaAcrescimosExtracao) areaAcrescimosExtracao.style.display = 'none';
  if (areaSemImpostosExtracao) areaSemImpostosExtracao.style.display = 'none';

  if (naoEmiteNota) {
    if (areaImpostosExtracao) areaImpostosExtracao.style.display = 'block';
    if (areaAcrescimosExtracao) areaAcrescimosExtracao.style.display = 'block';
  } else if (emiteNota) {
    // COM NOTA FISCAL: Esconde campo de documentação fiscal
    if (areaImpostosExtracao) areaImpostosExtracao.style.display = 'block';
  } else {
    if (areaSemImpostosExtracao) areaSemImpostosExtracao.style.display = 'block';
  }
}

// Função para calcular impostos da extração
function calcularExtracao() {
  // Captura dados
  extracaoData.tipoEmissao = radioEmiteNotaExtracaoSim && radioEmiteNotaExtracaoSim.checked ? 'sim' : 'nao';
  const radioDocFiscalSim = document.querySelector('input[name="doc_fiscal_extracao"][value="sim"]');
  extracaoData.documentacaoFiscal = radioDocFiscalSim && radioDocFiscalSim.checked ? 'sim' : 'nao';
  extracaoData.tipoPrestador = selectPrestadorExtracao ? selectPrestadorExtracao.value : '';

  // Converte centavos para reais e calcula total base
  let valorExtracaoCentavos = inputValorExtracao ? inputValorExtracao.value.replace(/\D/g, "") : "0";
  let quantidade = inputQuantidadeProduto ? inputQuantidadeProduto.value.replace(',', '.') : "1";

  valorExtracaoCentavos = parseFloat(valorExtracaoCentavos) || 0;  // Valor em centavos
  quantidade = parseFloat(quantidade) || 1;

  // Calcula total base e já fixa em 2 casas decimais
  let totalExtracaoReais = parseFloat(((valorExtracaoCentavos / 100) * quantidade).toFixed(2));

  let icms = 0, pis = 0, cofins = 0, acrescimos = 0;

  // LÓGICA DE CRÉDITOS FISCAIS:
  // Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
  // Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
  // Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
  const emiteNota = extracaoData.tipoEmissao === 'sim';
  const ajusteFiscal = extracaoData.documentacaoFiscal === 'sim';
  const geraCreditos = emiteNota || (!emiteNota && ajusteFiscal);

  if (geraCreditos) {
    // Para extração, sempre: ICMS = 0, PIS = 1,65%, COFINS = 7,6%
    icms = 0; // Sempre 0 para serviços de extração
    pis = parseFloat((totalExtracaoReais * 0.0165).toFixed(2)); // 1,65%
    cofins = parseFloat((totalExtracaoReais * 0.076).toFixed(2)); // 7,6%
  }

  // Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
  if (!emiteNota && ajusteFiscal) {
    acrescimos = parseFloat((totalExtracaoReais * 0.05).toFixed(2));
  } else {
    acrescimos = 0;
  }

  // CÁLCULO DO TOTAL FINAL DA EXTRAÇÃO:
  // Total = valor_base + acréscimos fiscais (ICMS, PIS, COFINS NÃO somam)
  let totalFinalReais = totalExtracaoReais + acrescimos;

  // Guarda valores em centavos para compatibilidade
  extracaoData.total = parseInt((totalFinalReais * 100).toFixed(0));
  extracaoData.icms = parseInt((icms * 100).toFixed(0));
  extracaoData.pis = parseInt((pis * 100).toFixed(0));
  extracaoData.cofins = parseInt((cofins * 100).toFixed(0));
  extracaoData.acrescimos = parseInt((acrescimos * 100).toFixed(0));

  // Atualiza campos visuais (valores em centavos para formatação)
  if (valorIcmsExtracao) valorIcmsExtracao.value = formatarParaMoedaBRL(parseInt((icms * 100).toFixed(0)));
  if (valorPisExtracao) valorPisExtracao.value = formatarParaMoedaBRL(parseInt((pis * 100).toFixed(0)));
  if (valorCofinsExtracao) valorCofinsExtracao.value = formatarParaMoedaBRL(parseInt((cofins * 100).toFixed(0)));
  if (valorSemNotaExtracao) valorSemNotaExtracao.value = formatarParaMoedaBRL(parseInt((acrescimos * 100).toFixed(0)));

  // Atualiza total na nova área
  if (totalExtracao) {
    totalExtracao.textContent = formatarParaMoedaBRL(extracaoData.total);
  }

  // Atualiza exibição
  atualizarExibicaoImpostosExtracao();
  calcularLucroBruto();
  atualizarResumoImpostos();
  atualizarTabelaAcrescimos();
}

// Event listeners para extração
if (radioEmiteNotaExtracaoSim) radioEmiteNotaExtracaoSim.addEventListener('change', function () {
  atualizarCamposExtracao();
  calcularExtracao();
});
if (radioEmiteNotaExtracaoNao) radioEmiteNotaExtracaoNao.addEventListener('change', function () {
  atualizarCamposExtracao();
  calcularExtracao();
});
if (selectPrestadorExtracao) selectPrestadorExtracao.addEventListener('change', calcularExtracao);
if (inputValorExtracao) inputValorExtracao.addEventListener('input', calcularExtracao);

const radioDocFiscalExtracaoSim = document.querySelector('input[name="doc_fiscal_extracao"][value="sim"]');
const radioDocFiscalExtracaoNao = document.querySelector('input[name="doc_fiscal_extracao"][value="nao"]');
if (radioDocFiscalExtracaoSim) radioDocFiscalExtracaoSim.addEventListener('change', calcularExtracao);
if (radioDocFiscalExtracaoNao) radioDocFiscalExtracaoNao.addEventListener('change', calcularExtracao);

// Inicialização da extração
window.addEventListener('DOMContentLoaded', function () {
  atualizarCamposExtracao();
  atualizarExibicaoImpostosExtracao();
  calcularExtracao();

  if (typeof aplicarMascaraMoeda === 'function') {
    aplicarMascaraMoeda();
  }
});

// ----------------------
// ETAPA: COMISSÃO
// ----------------------
const comissaoData = {
  total: 0,
  icms: 0,
  pis: 0,
  cofins: 0,
  acrescimos: 0,
  tipoEmissao: '',
  tipoPrestador: ''
};

// Elementos da área de comissão
const radioEmiteNotaComissaoSim = document.getElementById('radio-comissao-sim');
const radioEmiteNotaComissaoNao = document.getElementById('radio-comissao-nao');
const selectPrestadorComissao = document.getElementById('select-prestador-comissao');
const inputValorComissao = document.getElementById('input-valor-comissao');
const totalComissao = document.querySelectorAll('.mbr-card .mbr-total-value')[4];

// Áreas de exibição de impostos - Comissão
const areaImpostosComissao = document.getElementById('area-impostos-comissao');
const areaAcrescimosComissao = document.getElementById('area-acrescimos-comissao');
const areaSemImpostosComissao = document.getElementById('area-sem-impostos-comissao');

// Campos de valores - Comissão
const valorIcmsComissao = document.getElementById('valor-icms-comissao');
const valorPisComissao = document.getElementById('valor-pis-comissao');
const valorCofinsComissao = document.getElementById('valor-cofins-comissao');
const valorSemNotaComissao = document.getElementById('valor-sem-nota-comissao');

// Função para mostrar/ocultar campos conforme emissão de nota - COMISSÃO
function atualizarCamposComissao() {
  const colPrestador = document.getElementById('col-prestador-comissao');
  const colValor = document.getElementById('col-valor-comissao');

  const areaDocComissao = document.getElementById('area-doc-fiscal-comissao');

  if (radioEmiteNotaComissaoNao && radioEmiteNotaComissaoNao.checked) {
    if (areaDocComissao) areaDocComissao.style.display = '';
    // Esconde prestador e valor ocupa col-12
    if (colPrestador) colPrestador.style.display = '';
    // if (colValor) {
    //     colValor.classList.remove('col-md-6');
    //     colValor.classList.add('col-md-12');
    // }
  } else if (radioEmiteNotaComissaoSim && radioEmiteNotaComissaoSim.checked) {
    if (areaDocComissao) areaDocComissao.style.display = 'none';
    // Mostra prestador e valor volta para col-6
    if (colPrestador) colPrestador.style.display = '';
    // if (colValor) {
    //     colValor.classList.remove('col-md-12');
    //     colValor.classList.add('col-md-6');
    // } 
  } else {
    if (areaDocComissao) areaDocComissao.style.display = 'none';
    if (colPrestador) colPrestador.style.display = '';
  }
}

// Função para atualizar exibição dos impostos - Comissão
function atualizarExibicaoImpostosComissao() {
  const emiteNota = radioEmiteNotaComissaoSim && radioEmiteNotaComissaoSim.checked;
  const naoEmiteNota = radioEmiteNotaComissaoNao && radioEmiteNotaComissaoNao.checked;

  // Esconde todas as áreas primeiro
  if (areaImpostosComissao) areaImpostosComissao.style.display = 'none';
  if (areaAcrescimosComissao) areaAcrescimosComissao.style.display = 'none';
  if (areaSemImpostosComissao) areaSemImpostosComissao.style.display = 'none';

  if (naoEmiteNota) {
    if (areaImpostosComissao) areaImpostosComissao.style.display = 'block';
    if (areaAcrescimosComissao) areaAcrescimosComissao.style.display = 'block';
  } else if (emiteNota) {
    if (areaImpostosComissao) areaImpostosComissao.style.display = 'block';
  } else {
    if (areaSemImpostosComissao) areaSemImpostosComissao.style.display = 'block';
  }
}

// Função para calcular impostos da comissão
function calcularComissao() {
  // Captura dados
  comissaoData.tipoEmissao = radioEmiteNotaComissaoSim && radioEmiteNotaComissaoSim.checked ? 'sim' : 'nao';
  const radioDocFiscalSim = document.querySelector('input[name="doc_fiscal_comissao"][value="sim"]');
  comissaoData.documentacaoFiscal = radioDocFiscalSim && radioDocFiscalSim.checked ? 'sim' : 'nao';
  comissaoData.tipoPrestador = selectPrestadorComissao ? selectPrestadorComissao.value : '';

  // Converte centavos para reais e calcula total base
  let valorComissaoCentavos = inputValorComissao ? inputValorComissao.value.replace(/\D/g, "") : "0";
  let quantidade = inputQuantidadeProduto ? inputQuantidadeProduto.value.replace(',', '.') : "1";

  valorComissaoCentavos = parseFloat(valorComissaoCentavos) || 0;  // Valor em centavos
  quantidade = parseFloat(quantidade) || 1;

  // Calcula total base e já fixa em 2 casas decimais
  let totalComissaoReais = parseFloat(((valorComissaoCentavos / 100) * quantidade).toFixed(2));

  let icms = 0, pis = 0, cofins = 0, acrescimos = 0;

  // LÓGICA DE CRÉDITOS FISCAIS:
  // Se emite_nota = "sim" → Gera créditos fiscais (sem acréscimos)
  // Se emite_nota = "não" E ajuste_fiscal = "sim" → Gera créditos fiscais E acréscimos
  // Se emite_nota = "não" E ajuste_fiscal = "não" → NÃO gera créditos fiscais nem acréscimos
  const emiteNota = comissaoData.tipoEmissao === 'sim';
  const ajusteFiscal = comissaoData.documentacaoFiscal === 'sim';
  const geraCreditos = emiteNota || (!emiteNota && ajusteFiscal);

  if (geraCreditos) {
    // Para comissão: ICMS = 0, PIS = 1,65%, COFINS = 7,6% (sempre)
    icms = 0; // Sempre 0 para serviços de comissão
    pis = parseFloat((totalComissaoReais * 0.0165).toFixed(2)); // 1,65%
    cofins = parseFloat((totalComissaoReais * 0.076).toFixed(2)); // 7,6%
  }

  // Verifica acréscimos fiscais (5% apenas quando sem nota e com ajuste fiscal)
  if (!emiteNota && ajusteFiscal) {
    acrescimos = parseFloat((totalComissaoReais * 0.05).toFixed(2));
  } else {
    acrescimos = 0;
  }

  // CÁLCULO DO TOTAL FINAL DA COMISSÃO:
  // Total = valor_base + acréscimos fiscais (ICMS, PIS, COFINS NÃO somam)
  let totalFinalReais = totalComissaoReais + acrescimos;

  // Guarda valores em centavos para compatibilidade
  comissaoData.total = parseInt((totalFinalReais * 100).toFixed(0));
  comissaoData.icms = parseInt((icms * 100).toFixed(0));
  comissaoData.pis = parseInt((pis * 100).toFixed(0));
  comissaoData.cofins = parseInt((cofins * 100).toFixed(0));
  comissaoData.acrescimos = parseInt((acrescimos * 100).toFixed(0));

  // Atualiza campos visuais (valores em centavos para formatação)
  if (valorIcmsComissao) valorIcmsComissao.value = formatarParaMoedaBRL(parseInt((icms * 100).toFixed(0)));
  if (valorPisComissao) valorPisComissao.value = formatarParaMoedaBRL(parseInt((pis * 100).toFixed(0)));
  if (valorCofinsComissao) valorCofinsComissao.value = formatarParaMoedaBRL(parseInt((cofins * 100).toFixed(0)));
  if (valorSemNotaComissao) valorSemNotaComissao.value = formatarParaMoedaBRL(parseInt((acrescimos * 100).toFixed(0)));

  // Atualiza total na nova área
  if (totalComissao) {
    totalComissao.textContent = formatarParaMoedaBRL(comissaoData.total);
  }

  // Atualiza exibição
  atualizarExibicaoImpostosComissao();
  calcularLucroBruto();
  atualizarResumoImpostos();
  atualizarTabelaAcrescimos();
}

// Event listeners para comissão
if (radioEmiteNotaComissaoSim) radioEmiteNotaComissaoSim.addEventListener('change', function () {
  atualizarCamposComissao();
  calcularComissao();
});
if (radioEmiteNotaComissaoNao) radioEmiteNotaComissaoNao.addEventListener('change', function () {
  atualizarCamposComissao();
  calcularComissao();
});
if (selectPrestadorComissao) selectPrestadorComissao.addEventListener('change', calcularComissao);
if (inputValorComissao) inputValorComissao.addEventListener('input', calcularComissao);

const radioDocFiscalComissaoSim = document.querySelector('input[name="doc_fiscal_comissao"][value="sim"]');
const radioDocFiscalComissaoNao = document.querySelector('input[name="doc_fiscal_comissao"][value="nao"]');
if (radioDocFiscalComissaoSim) radioDocFiscalComissaoSim.addEventListener('change', calcularComissao);
if (radioDocFiscalComissaoNao) radioDocFiscalComissaoNao.addEventListener('change', calcularComissao);

// Inicialização da comissão
window.addEventListener('DOMContentLoaded', function () {
  atualizarCamposComissao();
  atualizarExibicaoImpostosComissao();
  calcularComissao();

  if (typeof aplicarMascaraMoeda === 'function') {
    aplicarMascaraMoeda();
  }

});


// ----------------------
// FUNÇÃO PARA CRIAR MODAIS TABLER.IO
// ----------------------

function criarModalAviso(titulo, mensagem, tipo = 'warning') {
  // Remove modal existente se houver
  const modalExistente = document.getElementById('modal-aviso');
  if (modalExistente) {
    modalExistente.remove();
  }

  // Define configurações por tipo
  const configuracoes = {
    warning: {
      cor: 'warning',
      icone: `<path d="M12 9v4" /><path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" /><path d="M12 16h.01" />`,
      botaoTexto: 'Entendi'
    },
    danger: {
      cor: 'danger',
      icone: `<path d="M12 9v4" /><path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" /><path d="M12 16h.01" />`,
      botaoTexto: 'Fechar'
    },
    info: {
      cor: 'info',
      icone: `<path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /><path d="M12 9h.01" /><path d="M11 12h1v4h1" />`,
      botaoTexto: 'OK'
    }
  };

  const config = configuracoes[tipo] || configuracoes.warning;

  // Cria o HTML do modal
  const modalHTML = `
        <div class="modal modal-blur fade" id="modal-aviso" tabindex="-1" role="dialog" aria-hidden="true">
            <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
                <div class="modal-content">
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    <div class="modal-status bg-${config.cor}"></div>
                    <div class="modal-body text-center py-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="icon mb-2 text-${config.cor} icon-lg">
                            ${config.icone}
                        </svg>
                        <h3>${titulo}</h3>
                        <div class="text-secondary">${mensagem}</div>
                    </div>
                    <div class="modal-footer">
                        <div class="w-100">
                            <div class="row">
                                <div class="col">
                                    <button type="button" class="btn w-100" data-bs-dismiss="modal">
                                        Cancelar
                                    </button>
                                </div>
                                <div class="col">
                                    <button type="button" class="btn btn-${config.cor} w-100" data-bs-dismiss="modal">
                                        ${config.botaoTexto}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

  // Adiciona o modal ao body
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // Mostra o modal
  const modal = new bootstrap.Modal(document.getElementById('modal-aviso'));
  modal.show();

  // Remove o modal do DOM quando for fechado
  document.getElementById('modal-aviso').addEventListener('hidden.bs.modal', function () {
    this.remove();
  });
}

// Função específica para modal simples (apenas OK)
function criarModalSimples(titulo, mensagem, tipo = 'warning') {
  // Remove modal existente se houver
  const modalExistente = document.getElementById('modal-simples');
  if (modalExistente) {
    modalExistente.remove();
  }

  // Define configurações por tipo
  const configuracoes = {
    warning: {
      cor: 'warning',
      icone: `<path d="M12 9v4" /><path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" /><path d="M12 16h.01" />`
    },
    danger: {
      cor: 'danger',
      icone: `<path d="M12 9v4" /><path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" /><path d="M12 16h.01" />`
    }
  };

  const config = configuracoes[tipo] || configuracoes.warning;

  // Cria o HTML do modal simples
  const modalHTML = `
        <div class="modal modal-blur fade" id="modal-simples" tabindex="-1" role="dialog" aria-hidden="true">
            <div class="modal-dialog modal-sm modal-dialog-centered" role="document">
                <div class="modal-content">
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    <div class="modal-status bg-${config.cor}"></div>
                    <div class="modal-body text-center py-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="icon mb-2 text-${config.cor} icon-lg">
                            ${config.icone}
                        </svg>
                        <h3>${titulo}</h3>
                        <div class="text-secondary">${mensagem}</div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-${config.cor} w-100" data-bs-dismiss="modal">
                            Entendi
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

  // Adiciona o modal ao body
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // Mostra o modal
  const modal = new bootstrap.Modal(document.getElementById('modal-simples'));
  modal.show();

  // Remove o modal do DOM quando for fechado
  document.getElementById('modal-simples').addEventListener('hidden.bs.modal', function () {
    this.remove();
  });
}

// ----------------------
// FUNÇÃO PARA PREPARAR RELATÓRIO (MODIFICADA COM MODAIS)
// ----------------------


function prepararRelatorio() {
  // Validação básica
  if (!validarCamposProduto()) {
    criarModalSimples(
      'Campos obrigatórios',
      'Preencha todos os dados do produto antes de gerar o relatório!',
      'danger'
    );
    return false; // Cancela o submit
  }

  try {
    // === DADOS DO PRODUTO ===
    const produto = document.getElementById('select-produto')?.value || '';
    const bitola = document.getElementById('select-bitola')?.value || '';
    // Valor unitário em centavos (inteiro)
    const valorUnitario = inputValorUnitario ? parseFloat(inputValorUnitario.value.replace(/\D/g, "")) : 0;
    // Quantidade em float
    const quantidade = inputQuantidade ? parseFloat(inputQuantidade.value.replace(',', '.')) : 0;
    const madeiraPostaSim = radioMadeiraPostaSim?.checked;
    const madeiraPosta = madeiraPostaSim ? 'sim' : 'nao';

    // === COMPRA DE MERCADORIA ===
    const emiteNotaCompraSim = radioEmiteNotaCompraSim?.checked;
    const emiteNotaCompra = emiteNotaCompraSim ? 'sim' : 'nao';
    const funruralSim = radioFunruralSim?.checked;
    const funrural = radioFunruralSim && radioFunruralSim.checked ? 'funrural' : 'senar';
    const estadoOrigem = selectEstadoOrigem?.value || '';
    const estadoDestino = selectEstadoDestino?.value || '';
    const classeFiscal = selectClassFiscal?.value || '';
    // Valor tonelada compra em centavos (inteiro)
    const valorTonCompra = inputValorTonCompra ? parseFloat(inputValorTonCompra.value.replace(/\D/g, "")) : 0;

    // === FRETE ===
    const emiteNotaFreteSim = radioEmiteNotaFreteSim?.checked;
    const emiteNotaFrete = emiteNotaFreteSim ? 'sim' : 'nao';
    const origemFrete = selectOrigemFrete?.value || '';
    const destinoFrete = selectDestinoFrete?.value || '';
    const prestadorFrete = selectPrestadorFrete?.value || '';
    const tipoNotaFrete = selectTipoNotaFrete?.value || '';
    // Valor frete em centavos (inteiro)
    const valorFrete = inputValorFrete ? parseFloat(inputValorFrete.value.replace(/\D/g, "")) : 0;

    // === EXTRAÇÃO ===
    const emiteNotaExtracaoSim = radioEmiteNotaExtracaoSim?.checked;
    const emiteNotaExtracao = emiteNotaExtracaoSim ? 'sim' : 'nao';
    const prestadorExtracao = selectPrestadorExtracao?.value || '';
    // Valor extração em centavos (inteiro)
    const valorExtracao = inputValorExtracao ? parseFloat(inputValorExtracao.value.replace(/\D/g, "")) : 0;

    // === COMISSÃO ===
    const emiteNotaComissaoSim = radioEmiteNotaComissaoSim?.checked;
    const emiteNotaComissao = emiteNotaComissaoSim ? 'sim' : 'nao';
    const prestadorComissao = selectPrestadorComissao?.value || '';
    // Valor comissão em centavos (inteiro)
    const valorComissao = inputValorComissao ? parseFloat(inputValorComissao.value.replace(/\D/g, "")) : 0;

    // === PREENCHE OS CAMPOS HIDDEN ===

    // Dados do produto
    document.getElementById('hidden-produto').value = produto;
    document.getElementById('hidden-bitola').value = bitola;
    document.getElementById('hidden-valor-unitario').value = valorUnitario;
    document.getElementById('hidden-quantidade').value = quantidade;
    document.getElementById('hidden-madeira-posta').value = madeiraPosta;

    // Compra de mercadoria
    document.getElementById('hidden-emite-nota-compra').value = emiteNotaCompra;
    document.getElementById('hidden-funrural').value = funrural;
    document.getElementById('hidden-estado-origem').value = estadoOrigem;
    document.getElementById('hidden-estado-destino').value = estadoDestino;
    document.getElementById('hidden-classificacao-fiscal').value = classeFiscal;
    document.getElementById('hidden-valor-ton-compra').value = valorTonCompra;

    // === NOVOS CAMPOS - DOCUMENTAÇÃO FISCAL E FUNRURAL DESCONTADO ===

    // Documentação fiscal - COMPRA
    const radioDocFiscalCompraSim = document.querySelector('input[name="doc_fiscal_compra"][value="sim"]');
    const documentacaoFiscalCompra = radioDocFiscalCompraSim?.checked ? 'sim' : 'nao';

    // Funrural descontado - COMPRA
    const radioFunruralDescontadoSim = document.querySelector('input[name="funrural_descontado"][value="sim"]');
    const funruralDescontado = radioFunruralDescontadoSim?.checked ? 'sim' : 'nao';

    // Preenche os campos hidden da compra
    if (document.getElementById('hidden-documentacao-fiscal-compra')) {
      document.getElementById('hidden-documentacao-fiscal-compra').value = documentacaoFiscalCompra;
    }
    if (document.getElementById('hidden-funrural-descontado')) {
      document.getElementById('hidden-funrural-descontado').value = funruralDescontado;
    }

    // Frete
    document.getElementById('hidden-emite-nota-frete').value = emiteNotaFrete;
    document.getElementById('hidden-origem-frete').value = origemFrete;
    document.getElementById('hidden-destino-frete').value = destinoFrete;
    document.getElementById('hidden-prestador-frete').value = prestadorFrete;
    document.getElementById('hidden-tipo-nota-frete').value = tipoNotaFrete;
    document.getElementById('hidden-valor-frete').value = valorFrete;

    // Documentação fiscal - FRETE
    const radioDocFiscalFreteSim = document.querySelector('input[name="doc_fiscal_frete"][value="sim"]');
    const documentacaoFiscalFrete = radioDocFiscalFreteSim?.checked ? 'sim' : 'nao';
    if (document.getElementById('hidden-documentacao-fiscal-frete')) {
      document.getElementById('hidden-documentacao-fiscal-frete').value = documentacaoFiscalFrete;
    }

    // Extração
    document.getElementById('hidden-emite-nota-extracao').value = emiteNotaExtracao;
    document.getElementById('hidden-prestador-extracao').value = prestadorExtracao;
    document.getElementById('hidden-valor-extracao').value = valorExtracao;

    // Documentação fiscal - EXTRAÇÃO
    const radioDocFiscalExtracaoSim = document.querySelector('input[name="doc_fiscal_extracao"][value="sim"]');
    const documentacaoFiscalExtracao = radioDocFiscalExtracaoSim?.checked ? 'sim' : 'nao';
    if (document.getElementById('hidden-documentacao-fiscal-extracao')) {
      document.getElementById('hidden-documentacao-fiscal-extracao').value = documentacaoFiscalExtracao;
    }

    // Comissão
    document.getElementById('hidden-emite-nota-comissao').value = emiteNotaComissao;
    document.getElementById('hidden-prestador-comissao').value = prestadorComissao;
    document.getElementById('hidden-valor-comissao').value = valorComissao;

    // Documentação fiscal - COMISSÃO
    const radioDocFiscalComissaoSim = document.querySelector('input[name="doc_fiscal_comissao"][value="sim"]');
    const documentacaoFiscalComissao = radioDocFiscalComissaoSim?.checked ? 'sim' : 'nao';
    if (document.getElementById('hidden-documentacao-fiscal-comissao')) {
      document.getElementById('hidden-documentacao-fiscal-comissao').value = documentacaoFiscalComissao;
    }

    // A função será chamada antes do submit, então não precisa modificar botões aqui
    // pois os botões são type="button" e não type="submit"

    return true; // Permite o submit

  } catch (error) {
    console.error('[RELATÓRIO] Erro ao preparar dados:', error);
    criarModalSimples(
      'Erro no processamento',
      'Erro ao preparar dados para o relatório. Verifique se todos os campos estão preenchidos.',
      'danger'
    );
    return false; // Cancela o submit
  }
}

// ----------------------
// FUNÇÃO PARA GERAR RELATÓRIOS (DETALHADO/SIMPLIFICADO)
// ----------------------

function gerarRelatorio(tipo) {
  // Define o tipo de relatório no campo hidden
  document.getElementById('hidden-tipo-relatorio').value = tipo;

  // Prepara os dados
  if (prepararRelatorio()) {
    // Adiciona loading visual no botão clicado
    const botaoClicado = event.target;
    const textoOriginal = botaoClicado.innerHTML;

    botaoClicado.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
                 class="icon icon-tabler icons-tabler-outline icon-tabler-loader-2" style="margin-right: 8px; animation: spin 1s linear infinite;">
              <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
              <path d="M12 3a9 9 0 1 0 9 9"/>
            </svg>
            Gerando Relatório...
        `;
    botaoClicado.disabled = true;

    // Adiciona CSS para animação se não existir
    if (!document.getElementById('loading-animation')) {
      const style = document.createElement('style');
      style.id = 'loading-animation';
      style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
      document.head.appendChild(style);
    }

    // Restaura o botão após delay
    setTimeout(() => {
      botaoClicado.innerHTML = textoOriginal;
      botaoClicado.disabled = false;
    }, 5000);

    // Se a preparação foi bem-sucedida, submete o formulário
    document.getElementById('form-relatorio').submit();
  }
}