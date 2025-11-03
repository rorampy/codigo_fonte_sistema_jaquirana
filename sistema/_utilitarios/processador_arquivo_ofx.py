import ofxparse
from datetime import datetime
import re
import io

class OFXProcessor:
    def __init__(self):
        self.transacoes = []
        self.resumo = {}
        
    def processar_arquivo(self, arquivo_conteudo):
        """
        Processa o conteudo do arquivo OFX e extrai todas as informações disponíveis
        """
        try:
            if isinstance(arquivo_conteudo, bytes):
                try:
                    arquivo_str = arquivo_conteudo.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        arquivo_str = arquivo_conteudo.decode('latin-1')
                    except UnicodeDecodeError:
                        arquivo_str = arquivo_conteudo.decode('cp1252', errors='ignore')
                arquivo_io = io.StringIO(arquivo_str)
            else:
                arquivo_io = io.StringIO(arquivo_conteudo)
            
            ofx = ofxparse.OfxParser.parse(arquivo_io)
            conta = ofx.account
            
            # Informações completas da instituição financeira
            instituicao_info = {}
            if hasattr(conta, 'institution') and conta.institution:
                instituicao_info = {
                    'organization': getattr(conta.institution, 'organization', ''),
                    'fid': getattr(conta.institution, 'fid', ''),
                    'broker_id': getattr(conta.institution, 'broker_id', ''),
                    'url': getattr(conta.institution, 'url', ''),
                }
            
            # Informações completas da conta
            conta_info = {
                'bank_id': getattr(conta, 'bank_id', ''),
                'branch_id': getattr(conta, 'branch_id', ''),
                'account_id': getattr(conta, 'account_id', ''),
                'account_type': getattr(conta, 'account_type', ''),
                'routing_number': getattr(conta, 'routing_number', ''),
                'currency': getattr(conta, 'currency', 'BRL'),
            }
            
            # Informações do statement
            statement_info = {}
            if hasattr(conta, 'statement') and conta.statement:
                statement_info = {
                    'currency': getattr(conta.statement, 'currency', 'BRL'),
                    'start_date': conta.statement.start_date.strftime('%Y-%m-%d') if conta.statement.start_date else '',
                    'end_date': conta.statement.end_date.strftime('%Y-%m-%d') if conta.statement.end_date else '',
                    'balance': float(getattr(conta.statement, 'balance', 0)),
                    'balance_date': conta.statement.balance_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(conta.statement, 'balance_date') and conta.statement.balance_date else '',
                    'available_balance': float(getattr(conta.statement, 'available_balance', 0)) if hasattr(conta.statement, 'available_balance') else None,
                    'available_balance_date': conta.statement.available_balance_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(conta.statement, 'available_balance_date') and conta.statement.available_balance_date else '',
                }
            
            # Resumo consolidado
            self.resumo = {
                'instituicao': instituicao_info,
                'conta': conta_info,
                'statement': statement_info,
                'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_transacoes': len(conta.statement.transactions) if conta.statement else 0,
            }
            
            # Processamento completo das transações
            total_creditos = 0
            total_debitos = 0
            tipos_transacao = {}
            
            for idx, transacao in enumerate(conta.statement.transactions):
                valor = float(transacao.amount)
                
                # Todos os campos possíveis da transação
                transacao_completa = {
                    # Identificadores
                    'indice': idx + 1,
                    'fitid': getattr(transacao, 'id', ''),
                    'refnum': getattr(transacao, 'refnum', ''),
                    'checknum': getattr(transacao, 'checknum', ''),
                    'srvrtid': getattr(transacao, 'srvrtid', ''),
                    
                    # Datas
                    'date': transacao.date.strftime('%Y-%m-%d') if transacao.date else '',
                    'date_user': transacao.date_user.strftime('%Y-%m-%d') if hasattr(transacao, 'date_user') and transacao.date_user else '',
                    'date_available': transacao.date_available.strftime('%Y-%m-%d') if hasattr(transacao, 'date_available') and transacao.date_available else '',
                    'date_posted': transacao.date.strftime('%Y-%m-%d %H:%M:%S') if transacao.date else '',
                    
                    # Valores
                    'amount': valor,
                    'amount_original': getattr(transacao, 'amount_original', valor),
                    'commission': float(getattr(transacao, 'commission', 0)) if hasattr(transacao, 'commission') else 0,
                    'fees': float(getattr(transacao, 'fees', 0)) if hasattr(transacao, 'fees') else 0,
                    'taxes': float(getattr(transacao, 'taxes', 0)) if hasattr(transacao, 'taxes') else 0,
                    'withholding': float(getattr(transacao, 'withholding', 0)) if hasattr(transacao, 'withholding') else 0,
                    
                    # Tipos e categorias
                    'type': getattr(transacao, 'type', ''),
                    'trntype': getattr(transacao, 'type', ''),
                    'trntype_orig': getattr(transacao, 'trntype_orig', ''),
                    
                    # Descrições
                    'memo': getattr(transacao, 'memo', ''),
                    'payee': getattr(transacao, 'payee', ''),
                    'name': getattr(transacao, 'name', ''),
                    'category': getattr(transacao, 'category', ''),
                    
                    # Informações de investimento (se aplicável)
                    'security': getattr(transacao, 'security', ''),
                    'units': getattr(transacao, 'units', ''),
                    'unit_price': getattr(transacao, 'unit_price', ''),
                    'market_value': getattr(transacao, 'market_value', ''),
                    
                    # Informações bancárias adicionais
                    'inv401k_source': getattr(transacao, 'inv401k_source', ''),
                    'bank_account_to': getattr(transacao, 'bank_account_to', ''),
                    'bank_account_from': getattr(transacao, 'bank_account_from', ''),
                    
                    # Campos processados para facilitar uso
                    'valor_absoluto': abs(valor),
                    'tipo_movimento': 'CREDITO' if valor > 0 else 'DEBITO',
                    'descricao_limpa': self._limpar_descricao(getattr(transacao, 'memo', '')),
                    'categoria_automatica': self._determinar_tipo_transacao(transacao),
                    'valor_formatado': f'R$ {abs(valor):,.2f}'.replace('.', '_').replace(',', '.').replace('_', ','),
                    
                    # Informações de debug/controle
                    'raw_data': {attr: str(getattr(transacao, attr, '')) for attr in dir(transacao) 
                               if not attr.startswith('_') and not callable(getattr(transacao, attr, None))},
                }
                
                # Contabilização
                if valor > 0:
                    total_creditos += valor
                else:
                    total_debitos += abs(valor)
                # Contagem por tipo
                tipo = transacao_completa['categoria_automatica']
                if tipo not in tipos_transacao:
                    tipos_transacao[tipo] = {'quantidade': 0, 'valor_total': 0}
                tipos_transacao[tipo]['quantidade'] += 1
                tipos_transacao[tipo]['valor_total'] += abs(valor)
                
                self.transacoes.append(transacao_completa)
            
            # Ordenação por data
            self.transacoes.sort(key=lambda x: x['date'], reverse=True)
            
            # Atualização do resumo com totais
            self.resumo.update({
                'totais': {
                    'creditos': total_creditos,
                    'debitos': total_debitos,
                    'saldo_liquido': total_creditos - total_debitos,
                    'creditos_formatado': f'R$ {total_creditos:,.2f}'.replace('.', '_').replace(',', '.').replace('_', ','),
                    'debitos_formatado': f'R$ {total_debitos:,.2f}'.replace('.', '_').replace(',', '.').replace('_', ','),
                    'saldo_formatado': f'R$ {(total_creditos - total_debitos):,.2f}'.replace('.', '_').replace(',', '.').replace('_', ','),
                },
                'estatisticas_por_tipo': tipos_transacao,
                'periodo': {
                    'primeira_transacao': self.transacoes[-1]['date'] if self.transacoes else '',
                    'ultima_transacao': self.transacoes[0]['date'] if self.transacoes else '',
                    'dias_periodo': (datetime.strptime(self.transacoes[0]['date'], '%Y-%m-%d') - 
                                   datetime.strptime(self.transacoes[-1]['date'], '%Y-%m-%d')).days + 1 if self.transacoes else 0,
                }
            })

            return True, "Arquivo processado com sucesso!"
            
        except Exception as e:
            return False, f"Erro ao processar arquivo: {str(e)}"
    
    def _determinar_tipo_transacao(self, transacao):
        """Categoriza automaticamente a transação baseada nos dados disponíveis"""
        memo = getattr(transacao, 'memo', '').upper()
        trntype = getattr(transacao, 'type', '').upper()
        checknum = getattr(transacao, 'checknum', '')
        
        if checknum or 'CHEQUE' in memo or trntype == 'CHECK':
            return 'CHEQUE'
        elif 'PIX' in memo:
            return 'PIX'
        elif 'TED' in memo:
            return 'TED'
        elif 'DOC' in memo:
            return 'DOC'
        elif 'BOLETO' in memo or 'LIQUIDACAO' in memo:
            return 'BOLETO'
        elif 'COMPRAS NACIONAIS' in memo or 'CARTAO' in memo:
            return 'CARTAO'
        elif 'DEP DINHEIRO' in memo or 'DEPOSITO' in memo:
            return 'DEPOSITO'
        elif 'APLICACAO' in memo or 'RESG.APLIC' in memo:
            return 'INVESTIMENTO'
        elif 'TRANSF' in memo:
            return 'TRANSFERENCIA'
        elif 'DEBITO CONVENIOS' in memo or 'CONVENIOS' in memo:
            return 'DEBITO_AUTOMATICO'
        elif 'SAQUE' in memo:
            return 'SAQUE'
        elif 'TARIFA' in memo or 'TAXA' in memo:
            return 'TARIFA'
        elif 'RECEBIMENTO' in memo:
            return 'RECEBIMENTO'
        elif 'PAGAMENTO' in memo:
            return 'PAGAMENTO'
        elif 'ARRECADACAO' in memo:
            return 'TRIBUTO'
        elif 'PAGAMENTO PIX' in memo or 'RECEBIMENTO PIX' in memo:
            return 'PIX'
        elif 'DEB.CTA.FATURA' in memo:
            return 'FATURA_CARTAO'
        elif 'DEBITO CONVENIOS' in memo:
            return 'DEBITO_AUTOMATICO'
        elif 'DEP DINHEIRO' in memo or 'DEP CHEQUE' in memo:
            return 'DEPOSITO'
        elif 'RESG.APLIC.FIN' in memo or 'APLICACAO FINANCEIRA' in memo:
            return 'INVESTIMENTO'
        elif 'COMPRAS NACIONAIS' in memo:
            return 'CARTAO_DEBITO'
        elif 'TRANSF ENTRE CONTAS' in memo:
            return 'TRANSFERENCIA_INTERNA'
        else:
            return 'OUTROS'
    
    def _limpar_descricao(self, memo):
        """Limpa e formata a descrição da transação"""
        if not memo:
            return "Sem descrição"
            
        descricao = memo.strip()
        
        # Remove códigos técnicos
        descricao = re.sub(r'-[A-Z]{2,3}\d+', '', descricao)
        descricao = re.sub(r'CX\d+\s*', '', descricao)
        descricao = re.sub(r'VE\d+\s*', '', descricao)
        descricao = re.sub(r'ID\s*\d+', '', descricao)
        descricao = re.sub(r'\d{11,}', '', descricao)
        
        # Limpa espaços extras
        descricao = ' '.join(descricao.split())
        
        return descricao if descricao else "Descrição não disponível"
    
    def get_transacoes(self):
        """Retorna todas as transações processadas"""
        return self.transacoes
    
    def get_resumo(self):
        """Retorna o resumo completo"""
        return self.resumo
    
    def get_dados_completos(self):
        """Retorna todos os dados processados"""
        return {
            'resumo': self.resumo,
            'transacoes': self.transacoes,
            'metadata': {
                'versao_processador': '2.0',
                'total_campos_capturados': len(self.transacoes[0].keys()) if self.transacoes else 0,
                'processado_em': datetime.now().isoformat(),
            }
        }
    