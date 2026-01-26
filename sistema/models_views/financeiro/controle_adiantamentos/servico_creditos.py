from datetime import datetime
from typing import List, Dict
from sistema import db
from .transacao_credito_model import TransacaoCreditoModel
from sistema._utilitarios import *

class ServicoCreditos:
    """
    Serviço centralizado para operações de crédito.
    Utiliza apenas a nova arquitetura (TransacaoCreditoModel).
    """
    
    # === Operações de Leitura de Saldo ===
    
    def obter_saldo_fornecedor(fornecedor_id: int) -> int:
        """
        Obtém saldo de crédito disponível de um fornecedor.
        
        Args:
            fornecedor_id: ID do fornecedor
            
        Returns:
            Saldo em centavos
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_saldo_pessoa(TipoPessoa.FORNECEDOR, fornecedor_id)
        except Exception as e:
            print(f"[ERRO obter_saldo_fornecedor] {fornecedor_id}: {e}")
            return 0
    
    def obter_saldo_transportadora(transportadora_id: int) -> int:
        """
        Obtém saldo de crédito disponível de uma transportadora.
        
        Args:
            transportadora_id: ID da transportadora
            
        Returns:
            Saldo em centavos
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_saldo_pessoa(TipoPessoa.FRETEIRO, transportadora_id)
        except Exception as e:
            print(f"[ERRO obter_saldo_transportadora] {transportadora_id}: {e}")
            return 0
    
    def obter_saldo_freteiro(transportadora_id: int) -> int:
        """Alias para obter_saldo_transportadora - mantido para compatibilidade."""
        return ServicoCreditos.obter_saldo_transportadora(transportadora_id)
    
    def obter_saldo_extrator(extrator_id: int) -> int:
        """
        Obtém saldo de crédito disponível de um extrator.
        
        Args:
            extrator_id: ID do extrator
            
        Returns:
            Saldo em centavos
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_saldo_pessoa(TipoPessoa.EXTRATOR, extrator_id)
        except Exception as e:
            print(f"[ERRO obter_saldo_extrator] {extrator_id}: {e}")
            return 0
    
    # === Operações de Leitura de Créditos Disponíveis ===
    
    def obter_creditos_disponiveis_fornecedor(fornecedor_id: int) -> List[Dict]:
        """
        Obtém lista de créditos individuais disponíveis de um fornecedor.
        
        Returns:
            Lista de dicts com id, data_movimentacao, descricao, valor_credito_100
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_creditos_disponiveis(TipoPessoa.FORNECEDOR, fornecedor_id)
        except Exception as e:
            print(f"[ERRO obter_creditos_disponiveis_fornecedor] {fornecedor_id}: {e}")
            return []
    
    def obter_creditos_disponiveis_transportadora(transportadora_id: int) -> List[Dict]:
        """Obtém lista de créditos individuais disponíveis de uma transportadora."""
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_creditos_disponiveis(TipoPessoa.FRETEIRO, transportadora_id)
        except Exception as e:
            print(f"[ERRO obter_creditos_disponiveis_transportadora] {transportadora_id}: {e}")
            return []
    
    def obter_creditos_disponiveis_extrator(extrator_id: int) -> List[Dict]:
        """Obtém lista de créditos individuais disponíveis de um extrator."""
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_creditos_disponiveis(TipoPessoa.EXTRATOR, extrator_id)
        except Exception as e:
            print(f"[ERRO obter_creditos_disponiveis_extrator] {extrator_id}: {e}")
            return []
    
    # === Operações de Histórico ===
    
    def obter_historico_fornecedor(fornecedor_id: int, limite: int = None) -> list:
        """Obtém histórico de transações de um fornecedor."""
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_historico_pessoa(TipoPessoa.FORNECEDOR, fornecedor_id, limite)
        except Exception as e:
            print(f"[ERRO obter_historico_fornecedor] {fornecedor_id}: {e}")
            return []
    
    def obter_historico_transportadora(transportadora_id: int, limite: int = None) -> list:
        """Obtém histórico de transações de uma transportadora."""
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_historico_pessoa(TipoPessoa.FRETEIRO, transportadora_id, limite)
        except Exception as e:
            print(f"[ERRO obter_historico_transportadora] {transportadora_id}: {e}")
            return []
    
    def obter_historico_extrator(extrator_id: int, limite: int = None) -> list:
        """Obtém histórico de transações de um extrator."""
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoPessoa
            return TransacaoCreditoModel.obter_historico_pessoa(TipoPessoa.EXTRATOR, extrator_id, limite)
        except Exception as e:
            print(f"[ERRO obter_historico_extrator] {extrator_id}: {e}")
            return []
    
    # === Operações de Lançamento ===
    
    def lancar_credito_fornecedor(
        fornecedor_id: int,
        valor_100: int,
        descricao: str,
        usuario_id: int,
        data_movimentacao: datetime = None,
        tipo_valor: str = 'positivo',
        conta_bancaria_id: int = None,
        faturamento_origem_id: int = None
    ) -> Dict:
        """
        Lança um novo crédito ou débito para fornecedor.
        
        Args:
            valor_100: Valor em centavos. 
                      Positivo = Crédito (MBR deve ao fornecedor)
                      Negativo = Débito (Fornecedor deve à MBR)
            tipo_valor: 'positivo' (crédito) ou 'negativo' (débito)
        
        Returns:
            Dict com 'novo_id' e 'legado_id' (para compatibilidade)
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa
            from .historico_transacao_model import HistoricoTransacaoCreditoModel
            
            data_mov = data_movimentacao or datetime.now().date()
            
            transacao = TransacaoCreditoModel(
                tipo_transacao=TipoTransacaoCredito.LANCAMENTO,
                tipo_pessoa=TipoPessoa.FORNECEDOR,
                fornecedor_id=fornecedor_id,
                data_movimentacao=data_mov,
                descricao=descricao,
                valor_original_100=valor_100,
                tipo_valor=tipo_valor,
                usuario_id=usuario_id,
                conta_bancaria_id=conta_bancaria_id,
                faturamento_origem_id=faturamento_origem_id
            )
            
            db.session.add(transacao)
            db.session.flush()
            
            # Registra no histórico
            HistoricoTransacaoCreditoModel.registrar_criacao(transacao, usuario_id)
            
            return {'novo_id': transacao.id, 'legado_id': None}
            
        except Exception as e:
            print(f"[ERRO lancar_credito_fornecedor] {fornecedor_id}: {e}")
            return {'novo_id': None, 'legado_id': None}
    
    def lancar_credito_transportadora(
        transportadora_id: int,
        valor_100: int,
        descricao: str,
        usuario_id: int,
        data_movimentacao: datetime = None,
        tipo_valor: str = 'positivo',
        conta_bancaria_id: int = None,
        faturamento_origem_id: int = None
    ) -> Dict:
        """
        Lança um novo crédito ou débito para transportadora.
        
        Args:
            valor_100: Valor em centavos.
                      Positivo = Crédito (MBR deve ao freteiro)
                      Negativo = Débito (Freteiro deve à MBR)
            tipo_valor: 'positivo' (crédito) ou 'negativo' (débito)
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa
            from .historico_transacao_model import HistoricoTransacaoCreditoModel
            
            data_mov = data_movimentacao or datetime.now().date()
            
            transacao = TransacaoCreditoModel(
                tipo_transacao=TipoTransacaoCredito.LANCAMENTO,
                tipo_pessoa=TipoPessoa.FRETEIRO,
                transportadora_id=transportadora_id,
                data_movimentacao=data_mov,
                descricao=descricao,
                valor_original_100=valor_100,
                tipo_valor=tipo_valor,
                usuario_id=usuario_id,
                conta_bancaria_id=conta_bancaria_id,
                faturamento_origem_id=faturamento_origem_id
            )
            
            db.session.add(transacao)
            db.session.flush()
            
            HistoricoTransacaoCreditoModel.registrar_criacao(transacao, usuario_id)
            
            return {'novo_id': transacao.id, 'legado_id': None}
            
        except Exception as e:
            print(f"[ERRO lancar_credito_transportadora] {transportadora_id}: {e}")
            return {'novo_id': None, 'legado_id': None}
    
    def lancar_credito_extrator(
        extrator_id: int,
        valor_100: int,
        descricao: str,
        usuario_id: int,
        data_movimentacao: datetime = None,
        tipo_valor: str = 'positivo',
        conta_bancaria_id: int = None,
        faturamento_origem_id: int = None
    ) -> Dict:
        """
        Lança um novo crédito ou débito para extrator.
        
        Args:
            valor_100: Valor em centavos.
                      Positivo = Crédito (MBR deve ao extrator)
                      Negativo = Débito (Extrator deve à MBR)
            tipo_valor: 'positivo' (crédito) ou 'negativo' (débito)
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoTransacaoCredito, TipoPessoa
            from .historico_transacao_model import HistoricoTransacaoCreditoModel
            
            data_mov = data_movimentacao or datetime.now().date()
            
            transacao = TransacaoCreditoModel(
                tipo_transacao=TipoTransacaoCredito.LANCAMENTO,
                tipo_pessoa=TipoPessoa.EXTRATOR,
                extrator_id=extrator_id,
                data_movimentacao=data_mov,
                descricao=descricao,
                valor_original_100=valor_100,
                tipo_valor=tipo_valor,
                usuario_id=usuario_id,
                conta_bancaria_id=conta_bancaria_id,
                faturamento_origem_id=faturamento_origem_id
            )
            
            db.session.add(transacao)
            db.session.flush()
            
            HistoricoTransacaoCreditoModel.registrar_criacao(transacao, usuario_id)
            
            return {'novo_id': transacao.id, 'legado_id': None}
            
        except Exception as e:
            print(f"[ERRO lancar_credito_extrator] {extrator_id}: {e}")
            return {'novo_id': None, 'legado_id': None}
    
    # === Operação de Edição ===
    
    def editar_credito_fornecedor(
        credito_id: int,
        valor_100: int = None,
        descricao: str = None,
        data_movimentacao: datetime = None,
        tipo_valor: str = None,
        usuario_id: int = None
    ) -> Dict:
        """
        Edita um lançamento de crédito existente para fornecedor.
        
        Args:
            credito_id: ID do crédito a ser editado
            valor_100: Novo valor em centavos (opcional)
            descricao: Nova descrição (opcional)
            data_movimentacao: Nova data (opcional)
            tipo_valor: 'positivo' ou 'negativo' (opcional)
            usuario_id: ID do usuário que fez a alteração
        
        Returns:
            Dict com sucesso/mensagem
        """
        return ServicoCreditos._editar_credito(
            credito_id=credito_id,
            valor_100=valor_100,
            descricao=descricao,
            data_movimentacao=data_movimentacao,
            tipo_valor=tipo_valor,
            usuario_id=usuario_id
        )
    
    def editar_credito_transportadora(
        credito_id: int,
        valor_100: int = None,
        descricao: str = None,
        data_movimentacao: datetime = None,
        tipo_valor: str = None,
        usuario_id: int = None
    ) -> Dict:
        """Edita um lançamento de crédito existente para transportadora."""
        return ServicoCreditos._editar_credito(
            credito_id=credito_id,
            valor_100=valor_100,
            descricao=descricao,
            data_movimentacao=data_movimentacao,
            tipo_valor=tipo_valor,
            usuario_id=usuario_id
        )
    
    def editar_credito_extrator(
        credito_id: int,
        valor_100: int = None,
        descricao: str = None,
        data_movimentacao: datetime = None,
        tipo_valor: str = None,
        usuario_id: int = None
    ) -> Dict:
        """Edita um lançamento de crédito existente para extrator."""
        return ServicoCreditos._editar_credito(
            credito_id=credito_id,
            valor_100=valor_100,
            descricao=descricao,
            data_movimentacao=data_movimentacao,
            tipo_valor=tipo_valor,
            usuario_id=usuario_id
        )
    
    def _editar_credito(
        credito_id: int,
        valor_100: int = None,
        descricao: str = None,
        data_movimentacao: datetime = None,
        tipo_valor: str = None,
        usuario_id: int = None
    ) -> Dict:
        """Edita crédito (método interno)"""
        resultado = {'sucesso': False, 'mensagem': ''}
        
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoTransacaoCredito
            from .historico_transacao_model import HistoricoTransacaoCreditoModel, AcaoHistoricoCredito
            
            transacao = TransacaoCreditoModel.query.get(credito_id)
            if not transacao:
                resultado['mensagem'] = f"Crédito ID {credito_id} não encontrado"
                return resultado
            
            # Verificar se não foi utilizado
            if transacao.valor_utilizado_100 > 0:
                resultado['mensagem'] = "Este crédito já foi parcialmente utilizado e não pode ser editado"
                return resultado
            
            # Verificar se é lançamento
            if transacao.tipo_transacao != TipoTransacaoCredito.LANCAMENTO:
                resultado['mensagem'] = "Apenas lançamentos podem ser editados"
                return resultado
            
            # Verificar se está ativo
            if not transacao.ativo:
                resultado['mensagem'] = "Crédito inativo não pode ser editado"
                return resultado
            
            # Guardar valores anteriores para histórico
            dados_anteriores = {
                'valor_original_100': transacao.valor_original_100,
                'descricao': transacao.descricao,
                'data_movimentacao': transacao.data_movimentacao.strftime('%Y-%m-%d') if transacao.data_movimentacao else None,
                'tipo_valor': transacao.tipo_valor
            }
            
            # Aplicar alterações
            alteracoes = []
            if valor_100 is not None and valor_100 != transacao.valor_original_100:
                transacao.valor_original_100 = valor_100
                alteracoes.append(f"valor alterado para {ValoresMonetarios.converter_float_brl_positivo(valor_100/100)}")
            
            if descricao is not None and descricao != transacao.descricao:
                transacao.descricao = descricao
                alteracoes.append("descrição atualizada")
            
            if data_movimentacao is not None and data_movimentacao != transacao.data_movimentacao:
                transacao.data_movimentacao = data_movimentacao
                alteracoes.append(f"data alterada")
            
            if tipo_valor is not None and tipo_valor != transacao.tipo_valor:
                transacao.tipo_valor = tipo_valor
                alteracoes.append(f"tipo alterado para {tipo_valor}")
            
            if not alteracoes:
                resultado['mensagem'] = "Nenhuma alteração detectada"
                return resultado
            
            # Registrar no histórico
            historico = HistoricoTransacaoCreditoModel(
                transacao_credito_id=transacao.id,
                acao=AcaoHistoricoCredito.ALTERACAO,
                usuario_id=usuario_id or transacao.usuario_id,
                valor_original_anterior_100=dados_anteriores['valor_original_100'],
                valor_original_posterior_100=transacao.valor_original_100,
                saldo_anterior_100=dados_anteriores['valor_original_100'],
                saldo_posterior_100=transacao.valor_original_100,
                descricao=f"Edição do lançamento: {', '.join(alteracoes)}",
                snapshot_json={
                    'dados_anteriores': dados_anteriores,
                    'dados_novos': {
                        'valor_original_100': transacao.valor_original_100,
                        'descricao': transacao.descricao,
                        'data_movimentacao': transacao.data_movimentacao.strftime('%Y-%m-%d') if transacao.data_movimentacao else None,
                        'tipo_valor': transacao.tipo_valor
                    }
                }
            )
            db.session.add(historico)
            db.session.commit()
            
            resultado['sucesso'] = True
            resultado['mensagem'] = f"Crédito editado com sucesso: {', '.join(alteracoes)}"
            return resultado
            
        except Exception as e:
            db.session.rollback()
            resultado['mensagem'] = f"Erro ao editar crédito: {str(e)}"
            print(f"[ERRO _editar_credito] {credito_id}: {e}")
            return resultado
    
    # === Operação de Exclusão ===
    
    def excluir_credito(
        tipo: str,
        credito_id: int,
        usuario_id: int,
        motivo: str = None
    ) -> Dict:
        """
        Exclui/cancela um lançamento de crédito.
        
        Args:
            tipo: 'fornecedor', 'freteiro' ou 'extrator'
            credito_id: ID do crédito a excluir
            usuario_id: ID do usuário responsável
            motivo: Motivo da exclusão (opcional)
        
        Returns:
            Dict com sucesso/mensagem
        """
        resultado = {'sucesso': False, 'mensagem': ''}
        
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoTransacaoCredito
            from .historico_transacao_model import HistoricoTransacaoCreditoModel
            
            transacao = TransacaoCreditoModel.query.get(credito_id)
            if not transacao:
                resultado['mensagem'] = f"Crédito ID {credito_id} não encontrado"
                return resultado
            
            # Verificar se não foi utilizado
            if transacao.valor_utilizado_100 > 0:
                resultado['mensagem'] = "Este crédito já foi parcialmente utilizado e não pode ser excluído"
                return resultado
            
            # Verificar se já está cancelado
            if transacao.tipo_transacao == TipoTransacaoCredito.CANCELAMENTO or not transacao.ativo:
                resultado['mensagem'] = "Este crédito já foi cancelado"
                return resultado
            
            # Cancelar a transação
            transacao.ativo = False
            transacao.deletado = True
            
            # Registrar no histórico
            HistoricoTransacaoCreditoModel.registrar_cancelamento(
                transacao=transacao,
                usuario_id=usuario_id,
                motivo=motivo or f"Exclusão manual do crédito {transacao.codigo_transacao}"
            )
            
            db.session.commit()
            resultado['sucesso'] = True
            resultado['mensagem'] = f"Crédito {transacao.codigo_transacao} excluído com sucesso"
            return resultado
            
        except Exception as e:
            db.session.rollback()
            resultado['mensagem'] = f"Erro ao excluir crédito: {str(e)}"
            print(f"[ERRO excluir_credito] {tipo} {credito_id}: {e}")
            return resultado
    
    # === Operação de Utilização ===
    
    def utilizar_credito(
        tipo: str,
        credito_id: int,
        valor_100: int,
        usuario_id: int,
        faturamento_destino_id: int = None,
        descricao: str = None
    ) -> Dict:
        """
        Utiliza (parcial ou totalmente) um crédito ou débito.
        
        Suporta valores positivos (créditos que reduzem o total) e valores negativos
        (débitos que aumentam o total). O método mantém a integridade matemática dos sinais.
        
        Args:
            tipo: 'fornecedor', 'freteiro' ou 'extrator'
            credito_id: ID da transação de crédito/débito
            valor_100: Valor máximo a utilizar em centavos
            usuario_id: ID do usuário responsável
            faturamento_destino_id: ID do faturamento onde será aplicado
            descricao: Descrição personalizada da utilização
            
        Returns:
            Dict com:
                - sucesso: bool
                - valor_utilizado: int (positivo para créditos, negativo para débitos)
                - novo_id: int (ID da transação)
                - mensagem: str
        """
        resultado = {
            'sucesso': False,
            'novo_id': None,
            'valor_utilizado': 0,
            'mensagem': ''
        }
        
        try:
            from .transacao_credito_model import TransacaoCreditoModel
            from .historico_transacao_model import HistoricoTransacaoCreditoModel
            
            transacao = TransacaoCreditoModel.query.get(credito_id)
            if not transacao:
                resultado['mensagem'] = f"Crédito ID {credito_id} não encontrado"
                return resultado
            
            saldo_disponivel = transacao.obter_saldo_disponivel_100()
            
            if saldo_disponivel == 0:
                resultado['mensagem'] = "Crédito sem saldo disponível"
                return resultado
            
            # Calcular valor a utilizar respeitando o sinal do saldo
            if saldo_disponivel > 0:
                valor_a_utilizar = min(abs(valor_100), abs(saldo_disponivel))
            else:
                valor_a_utilizar = -min(abs(valor_100), abs(saldo_disponivel))
            
            # Usar o método do modelo que cria a transação de UTILIZACAO
            nova_transacao = transacao.utilizar_credito(
                valor_100=abs(valor_a_utilizar),
                usuario_id=usuario_id,
                faturamento_destino_id=faturamento_destino_id,
                descricao=descricao
            )
            
            # Registrar no histórico
            HistoricoTransacaoCreditoModel.registrar_utilizacao(
                transacao=transacao,
                valor_utilizado_100=abs(valor_a_utilizar),
                usuario_id=usuario_id,
                faturamento_id=faturamento_destino_id,
                descricao=descricao
            )
            
            resultado['sucesso'] = True
            resultado['novo_id'] = nova_transacao.id
            resultado['valor_utilizado'] = valor_a_utilizar
            resultado['descricao'] = transacao.descricao
            resultado['data_movimentacao'] = transacao.data_movimentacao.strftime('%d/%m/%Y') if transacao.data_movimentacao else ''
            resultado['mensagem'] = f"Crédito utilizado: R$ {valor_a_utilizar/100:.2f}"
            
            return resultado
            
        except Exception as e:
            db.session.rollback()
            resultado['mensagem'] = f"Erro ao utilizar crédito: {str(e)}"
            print(f"[ERRO utilizar_credito] {tipo} {credito_id}: {e}")
            return resultado
    
    def processar_utilizacao_creditos(
        tipo: str,
        pessoa_id: int,
        creditos_ids: List[int],
        valor_maximo_100: int,
        usuario_id: int,
        faturamento_id: int = None,
        descricao_base: str = None
    ) -> Dict:
        """
        Processa a utilização de múltiplos créditos/débitos em uma única operação.
        
        Suporta processamento simultâneo de créditos positivos (limitados ao valor_maximo)
        e débitos negativos (aplicados integralmente). Cria vínculo automático com o
        faturamento quando informado.
        
        Args:
            tipo: 'fornecedor', 'freteiro' ou 'extrator'
            pessoa_id: ID da pessoa
            creditos_ids: Lista de IDs das transações a processar
            valor_maximo_100: Valor máximo para aplicar créditos positivos (centavos)
            usuario_id: ID do usuário responsável
            faturamento_id: ID do faturamento para vínculo (opcional)
            descricao_base: Descrição customizada (opcional)
        
        Returns:
            Dict com:
                - sucesso: bool
                - total_utilizado_100: int (soma algébrica dos valores)
                - creditos_processados: list
                - vinculo_id: int (se faturamento_id informado)
                - mensagem: str
        """
        from .faturamento_credito_vinculo_model import FaturamentoCreditoVinculoModel
        from .transacao_credito_model import TipoPessoa
        
        resultado = {
            'sucesso': False,
            'total_utilizado_100': 0,
            'creditos_processados': [],
            'vinculo_id': None,
            'mensagem': ''
        }
        
        if not creditos_ids:
            resultado['mensagem'] = "Nenhum crédito informado para utilização"
            return resultado
        
        from .transacao_credito_model import TransacaoCreditoModel
        
        valor_restante = valor_maximo_100
        
        for credito_id in creditos_ids:
            transacao_check = TransacaoCreditoModel.query.get(credito_id)
            
            if not transacao_check:
                continue
            
            saldo_check = transacao_check.obter_saldo_disponivel_100()
            
            if saldo_check > 0 and valor_restante <= 0:
                continue
            
            valor_a_passar = 999999999 if saldo_check < 0 else valor_restante
            
            res_utilizacao = ServicoCreditos.utilizar_credito(
                tipo=tipo,
                credito_id=credito_id,
                valor_100=valor_a_passar,
                usuario_id=usuario_id,
                faturamento_destino_id=faturamento_id,
                descricao=descricao_base
            )
            
            if res_utilizacao.get('sucesso'):
                valor_usado = res_utilizacao.get('valor_utilizado', 0)
                
                resultado['creditos_processados'].append({
                    'credito_id': credito_id,
                    'valor_utilizado': valor_usado,
                    'novo_id': res_utilizacao.get('novo_id'),
                    'descricao': res_utilizacao.get('descricao', ''),
                    'data_movimentacao': res_utilizacao.get('data_movimentacao', '')
                })
                resultado['total_utilizado_100'] += valor_usado
                
                if valor_usado > 0:
                    valor_restante -= valor_usado
        
        if faturamento_id and resultado['total_utilizado_100'] != 0:
            try:
                tipo_pessoa_map = {
                    'fornecedor': TipoPessoa.FORNECEDOR,
                    'freteiro': TipoPessoa.FRETEIRO,
                    'extrator': TipoPessoa.EXTRATOR
                }
                
                vinculo = FaturamentoCreditoVinculoModel(
                    faturamento_id=faturamento_id,
                    tipo_pessoa=tipo_pessoa_map[tipo],
                    usuario_id=usuario_id,
                    valor_aplicado_100=resultado['total_utilizado_100'],
                    descricao=f"Créditos utilizados: {creditos_ids}"
                )
                
                # Definir o campo correto da entidade (fornecedor/transportadora/extrator)
                if tipo == 'fornecedor':
                    vinculo.fornecedor_id = pessoa_id
                elif tipo == 'freteiro':
                    vinculo.transportadora_id = pessoa_id
                elif tipo == 'extrator':
                    vinculo.extrator_id = pessoa_id
                
                db.session.add(vinculo)
                db.session.flush()
                resultado['vinculo_id'] = vinculo.id
            except Exception as e:
                print(f"[WARN] Erro ao criar vínculo de crédito: {e}")
                import traceback
                traceback.print_exc()
        
        resultado['sucesso'] = resultado['total_utilizado_100'] != 0
        resultado['mensagem'] = f"Total utilizado: R$ {resultado['total_utilizado_100']/100:.2f}"
        
        return resultado
    
    @staticmethod
    def vincular_faturamento_a_creditos(
        resultado_creditos: dict,
        faturamento_id: int,
        pagamento_id: int = None,
        pagamento_tipo: str = None
    ) -> dict:
        """
        Vincula um faturamento às transações de crédito processadas.
        
        Atualiza os campos faturamento_destino_id, pagamento_destino_id e 
        pagamento_destino_tipo nas transações de utilização de crédito.
        
        Args:
            resultado_creditos: Resultado retornado por processar_utilizacao_creditos()
            faturamento_id: ID do faturamento criado
            pagamento_id: ID do pagamento específico (opcional, usado em faturamento individual)
            pagamento_tipo: Tipo da tabela de pagamento ('fin_fornecedor_a_pagar', 'fin_frete_a_pagar', 'fin_extrator_a_pagar')
            
        Returns:
            Dict com sucesso/erro e quantidade de vínculos criados
            
        Example:
            # Após criar faturamento
            resultado_vinculo = ServicoCreditos.vincular_faturamento_a_creditos(
                resultado_creditos=resultado_creditos,
                faturamento_id=novo_faturamento.id,
                pagamento_id=registro.id,
                pagamento_tipo='fin_fornecedor_a_pagar'
            )
        """
        try:
            if not resultado_creditos.get('sucesso'):
                return {
                    'sucesso': False,
                    'mensagem': 'Resultado de créditos inválido',
                    'vinculos_criados': 0
                }
            
            creditos_processados = resultado_creditos.get('creditos_processados', [])
            vinculos_criados = 0
            
            for credito_proc in creditos_processados:
                novo_id = credito_proc.get('novo_id')
                if novo_id:
                    transacao_utilizacao = TransacaoCreditoModel.query.get(novo_id)
                    if transacao_utilizacao:
                        transacao_utilizacao.faturamento_destino_id = faturamento_id
                        if pagamento_id:
                            transacao_utilizacao.pagamento_destino_id = pagamento_id
                        if pagamento_tipo:
                            transacao_utilizacao.pagamento_destino_tipo = pagamento_tipo
                        vinculos_criados += 1
            
            return {
                'sucesso': True,
                'mensagem': f'{vinculos_criados} vínculo(s) criado(s) com sucesso',
                'vinculos_criados': vinculos_criados
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao vincular faturamento: {str(e)}',
                'vinculos_criados': 0
            }
    
    @staticmethod
    def estornar_utilizacao_creditos(
        faturamento_id: int,
        usuario_id: int,
        motivo: str = "Cancelamento de faturamento"
    ) -> dict:
        """
        Estorna (cancela) todas as utilizações de crédito vinculadas a um faturamento.
        
        Busca todas as transações de UTILIZACAO vinculadas ao faturamento_id e
        cria transações de ESTORNO para cada uma, restaurando o saldo disponível.
        
        Args:
            faturamento_id: ID do faturamento a estornar
            usuario_id: ID do usuário responsável pelo estorno
            motivo: Descrição do motivo do estorno
            
        Returns:
            Dict com sucesso/erro e detalhes dos estornos
            
        Example:
            resultado = ServicoCreditos.estornar_utilizacao_creditos(
                faturamento_id=123,
                usuario_id=current_user.id,
                motivo="Cancelamento de faturamento"
            )
        """
        try:
            from .transacao_credito_model import TransacaoCreditoModel, TipoTransacaoCredito
            print(f"[INFO estornar_utilizacao_creditos] Iniciando estorno para faturamento_id={faturamento_id}")
            # Buscar todas as transações de UTILIZACAO vinculadas a este faturamento
            transacoes_utilizacao = TransacaoCreditoModel.query.filter_by(
                faturamento_destino_id=faturamento_id,
                tipo_transacao=TipoTransacaoCredito.UTILIZACAO
            ).all()
            
            if not transacoes_utilizacao:
                return {
                    'sucesso': True,
                    'mensagem': 'Nenhuma transação de crédito para estornar',
                    'estornos_criados': 0
                }
            
            estornos_criados = []
            total_estornado_100 = 0
            
            for transacao_utilizacao in transacoes_utilizacao:
                # Criar transação de ESTORNO usando o método do model
                transacao_estorno = transacao_utilizacao.estornar(
                    usuario_id=usuario_id,
                    descricao=motivo
                )
                
                if transacao_estorno:
                    db.session.add(transacao_estorno)
                    estornos_criados.append({
                        'utilizacao_id': transacao_utilizacao.id,
                        'estorno_id': transacao_estorno.id,
                        'valor_estornado_100': transacao_estorno.valor_original_100,
                        'pessoa_id': transacao_estorno.obter_pessoa_id(),
                        'tipo_pessoa': transacao_estorno.tipo_pessoa
                    })
                    total_estornado_100 += transacao_estorno.valor_original_100
            
            db.session.flush()
            
            return {
                'sucesso': True,
                'mensagem': f'{len(estornos_criados)} estorno(s) criado(s) com sucesso',
                'estornos_criados': len(estornos_criados),
                'total_estornado_100': total_estornado_100,
                'detalhes': estornos_criados
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERRO estornar_utilizacao_creditos] faturamento_id={faturamento_id}: {e}")
            return {
                'sucesso': False,
                'mensagem': f'Erro ao estornar créditos: {str(e)}',
                'estornos_criados': 0
            }
