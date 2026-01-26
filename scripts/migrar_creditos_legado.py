"""
Script de Migração de Créditos Legado para Nova Arquitetura

Migra dados das tabelas antigas:
- ex_extrato_credito_fornecedor
- ex_extrato_credito_freteiro
- ex_extrato_credito_extrator

Para a nova tabela unificada:
- cre_transacao_credito

Mantém as tabelas antigas intactas para rollback se necessário.
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from sistema.models_views.base_model import db
from sistema.models_views.financeiro.controle_adiantamentos.transacao_credito_model import (
    TransacaoCreditoModel, 
    TipoTransacaoCredito, 
    TipoPessoa
)
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_fornecedor_model import ExtratoCreditoFornecedorModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_freteiro_model import ExtratoCreditoFreteiroModel
from sistema.models_views.faturamento.controle_credito.extrato_credito.extrato_credito_extrator_model import ExtratoCreditoExtratorModel


class MigradorCreditos:
    """Classe para migração de créditos do sistema legado para nova arquitetura"""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.estatisticas = {
            'fornecedor': {'total': 0, 'migrados': 0, 'ignorados': 0, 'erros': 0},
            'freteiro': {'total': 0, 'migrados': 0, 'ignorados': 0, 'erros': 0},
            'extrator': {'total': 0, 'migrados': 0, 'ignorados': 0, 'erros': 0}
        }
        self.erros = []
    
    def gerar_codigo_transacao(self, tipo_pessoa):
        """Gera código único para a transação no formato ADFOR-XXXXX, ADEXT-XXXXX, ADFRE-XXXXX"""
        prefixo = {
            TipoPessoa.FORNECEDOR: 'ADFOR',
            TipoPessoa.FRETEIRO: 'ADFRE',
            TipoPessoa.EXTRATOR: 'ADEXT'
        }[tipo_pessoa]
        
        # Busca último código com esse prefixo
        ultimo = TransacaoCreditoModel.query.filter(
            TransacaoCreditoModel.codigo_transacao.like(f'{prefixo}-%')
        ).order_by(TransacaoCreditoModel.id.desc()).first()
        
        if ultimo:
            ultimo_seq = int(ultimo.codigo_transacao.split('-')[-1])
            novo_seq = ultimo_seq + 1
        else:
            novo_seq = 1
        
        return f"{prefixo}-{novo_seq:05d}"
    
    def mapear_tipo_transacao(self, tipo_movimentacao):
        """
        Mapeia tipo_movimentacao do legado para novo enum
        Legado: 1-Entrada, 2-Saída, 3-Cancelamento, 4-Estorno
        Novo: 1-Lançamento, 2-Utilização, 3-Estorno, 4-Cancelamento
        """
        mapeamento = {
            1: TipoTransacaoCredito.LANCAMENTO,
            2: TipoTransacaoCredito.UTILIZACAO,
            3: TipoTransacaoCredito.CANCELAMENTO,
            4: TipoTransacaoCredito.ESTORNO
        }
        return mapeamento.get(tipo_movimentacao, TipoTransacaoCredito.LANCAMENTO)
    
    def migrar_fornecedor(self, registro):
        """Migra um registro de crédito de fornecedor"""
        try:
            # Verificar se já foi migrado
            existe = TransacaoCreditoModel.query.filter_by(
                tipo_pessoa=TipoPessoa.FORNECEDOR,
                fornecedor_id=registro.fornecedor_id,
                data_movimentacao=registro.data_movimentacao,
                valor_original_100=registro.valor_credito_100,
                descricao=registro.descricao
            ).first()
            
            if existe:
                print(f"  ⚠️  Registro {registro.id} já migrado (ID na nova tabela: {existe.id})")
                return False
            
            # Validar dados obrigatórios antes de migrar
            if not registro.fornecedor_id:
                raise ValueError(f"Registro {registro.id} sem fornecedor_id")
            if not registro.usuario_id:
                raise ValueError(f"Registro {registro.id} sem usuario_id")
            
            # Validar valor: aceitar zero apenas para CANCELAMENTO (3) ou ESTORNO (4)
            if registro.valor_credito_100 is None:
                raise ValueError(f"Registro {registro.id} com valor_credito_100 NULL")
            if registro.valor_credito_100 == 0 and registro.tipo_movimentacao not in [3, 4]:
                # Valor zero só é válido para cancelamentos e estornos
                self.estatisticas['fornecedor']['ignorados'] += 1
                print(f"  ⚠️  Ignorando registro {registro.id}: Valor zero para tipo {registro.tipo_movimentacao} (esperado apenas para Cancelamento=3 ou Estorno=4)")
                return False
            
            # Criar nova transação
            transacao = TransacaoCreditoModel(
                tipo_transacao=self.mapear_tipo_transacao(registro.tipo_movimentacao),
                tipo_pessoa=TipoPessoa.FORNECEDOR,
                data_movimentacao=registro.data_movimentacao,
                descricao=registro.descricao or f"Migração crédito fornecedor #{registro.id}",
                fornecedor_id=registro.fornecedor_id,
                valor_original_100=registro.valor_credito_100,
                valor_utilizado_100=registro.valor_credito_100 if registro.credito_utilizado else 0,
                usuario_id=registro.usuario_id,
                ativo=registro.ativo,
                extrato_legado_id=registro.id,
                extrato_legado_tipo='fornecedor'
            )
            
            # Setar código de transação manualmente
            transacao.codigo_transacao = self.gerar_codigo_transacao(TipoPessoa.FORNECEDOR)
            
            if not self.dry_run:
                db.session.add(transacao)
            
            self.estatisticas['fornecedor']['migrados'] += 1
            print(f"  ✅ Migrado: ID {registro.id} -> {transacao.codigo_transacao}")
            return True
            
        except ValueError as ve:
            self.estatisticas['fornecedor']['erros'] += 1
            erro = f"Validação falhou para fornecedor ID {registro.id}: {str(ve)}"
            self.erros.append(erro)
            print(f"  ❌ {erro}")
            return False
        except Exception as e:
            self.estatisticas['fornecedor']['erros'] += 1
            erro = f"Erro ao migrar fornecedor ID {registro.id}: {str(e)}"
            self.erros.append(erro)
            print(f"  ❌ {erro}")
            db.session.rollback()
            return False
    
    def migrar_freteiro(self, registro):
        """Migra um registro de crédito de freteiro/transportadora"""
        try:
            # Verificar se já foi migrado
            existe = TransacaoCreditoModel.query.filter_by(
                tipo_pessoa=TipoPessoa.FRETEIRO,
                transportadora_id=registro.transportadora_id,
                data_movimentacao=registro.data_movimentacao,
                valor_original_100=registro.valor_credito_100,
                descricao=registro.descricao
            ).first()
            
            if existe:
                print(f"  ⚠️  Registro {registro.id} já migrado (ID na nova tabela: {existe.id})")
                return False
            
            # Validar dados obrigatórios antes de migrar
            if not registro.transportadora_id:
                raise ValueError(f"Registro {registro.id} sem transportadora_id")
            if not registro.usuario_id:
                raise ValueError(f"Registro {registro.id} sem usuario_id")
            
            # Validar valor: aceitar zero apenas para CANCELAMENTO (3) ou ESTORNO (4)
            if registro.valor_credito_100 is None:
                raise ValueError(f"Registro {registro.id} com valor_credito_100 NULL")
            if registro.valor_credito_100 == 0 and registro.tipo_movimentacao not in [3, 4]:
                # Valor zero só é válido para cancelamentos e estornos
                self.estatisticas['freteiro']['ignorados'] += 1
                print(f"  ⚠️  Ignorando registro {registro.id}: Valor zero para tipo {registro.tipo_movimentacao} (esperado apenas para Cancelamento=3 ou Estorno=4)")
                return False
            
            # Criar nova transação
            transacao = TransacaoCreditoModel(
                tipo_transacao=self.mapear_tipo_transacao(registro.tipo_movimentacao),
                tipo_pessoa=TipoPessoa.FRETEIRO,
                data_movimentacao=registro.data_movimentacao,
                descricao=registro.descricao or f"Migração crédito freteiro #{registro.id}",
                transportadora_id=registro.transportadora_id,
                valor_original_100=registro.valor_credito_100,
                valor_utilizado_100=registro.valor_credito_100 if registro.credito_utilizado else 0,
                usuario_id=registro.usuario_id,
                ativo=registro.ativo,
                extrato_legado_id=registro.id,
                extrato_legado_tipo='freteiro'
            )
            
            # Setar código de transação manualmente
            transacao.codigo_transacao = self.gerar_codigo_transacao(TipoPessoa.FRETEIRO)
            
            if not self.dry_run:
                db.session.add(transacao)
            
            self.estatisticas['freteiro']['migrados'] += 1
            print(f"  ✅ Migrado: ID {registro.id} -> {transacao.codigo_transacao}")
            return True
            
        except ValueError as ve:
            self.estatisticas['freteiro']['erros'] += 1
            erro = f"Validação falhou para freteiro ID {registro.id}: {str(ve)}"
            self.erros.append(erro)
            print(f"  ❌ {erro}")
            return False
        except Exception as e:
            self.estatisticas['freteiro']['erros'] += 1
            erro = f"Erro ao migrar freteiro ID {registro.id}: {str(e)}"
            self.erros.append(erro)
            print(f"  ❌ {erro}")
            db.session.rollback()
            return False
    
    def migrar_extrator(self, registro):
        """Migra um registro de crédito de extrator"""
        try:
            # Verificar se já foi migrado
            existe = TransacaoCreditoModel.query.filter_by(
                tipo_pessoa=TipoPessoa.EXTRATOR,
                extrator_id=registro.extrator_id,
                data_movimentacao=registro.data_movimentacao,
                valor_original_100=registro.valor_credito_100,
                descricao=registro.descricao
            ).first()
            
            if existe:
                print(f"  ⚠️  Registro {registro.id} já migrado (ID na nova tabela: {existe.id})")
                return False
            
            # Validar dados obrigatórios antes de migrar
            if not registro.extrator_id:
                raise ValueError(f"Registro {registro.id} sem extrator_id")
            if not registro.usuario_id:
                raise ValueError(f"Registro {registro.id} sem usuario_id")
            
            # Validar valor: aceitar zero apenas para CANCELAMENTO (3) ou ESTORNO (4)
            if registro.valor_credito_100 is None:
                raise ValueError(f"Registro {registro.id} com valor_credito_100 NULL")
            if registro.valor_credito_100 == 0 and registro.tipo_movimentacao not in [3, 4]:
                # Valor zero só é válido para cancelamentos e estornos
                self.estatisticas['extrator']['ignorados'] += 1
                print(f"  ⚠️  Ignorando registro {registro.id}: Valor zero para tipo {registro.tipo_movimentacao} (esperado apenas para Cancelamento=3 ou Estorno=4)")
                return False
            
            # Criar nova transação
            transacao = TransacaoCreditoModel(
                tipo_transacao=self.mapear_tipo_transacao(registro.tipo_movimentacao),
                tipo_pessoa=TipoPessoa.EXTRATOR,
                data_movimentacao=registro.data_movimentacao,
                descricao=registro.descricao or f"Migração crédito extrator #{registro.id}",
                extrator_id=registro.extrator_id,
                valor_original_100=registro.valor_credito_100,
                valor_utilizado_100=registro.valor_credito_100 if registro.credito_utilizado else 0,
                usuario_id=registro.usuario_id,
                ativo=registro.ativo,
                extrato_legado_id=registro.id,
                extrato_legado_tipo='extrator'
            )
            
            # Setar código de transação manualmente
            transacao.codigo_transacao = self.gerar_codigo_transacao(TipoPessoa.EXTRATOR)
            
            if not self.dry_run:
                db.session.add(transacao)
            
            self.estatisticas['extrator']['migrados'] += 1
            print(f"  ✅ Migrado: ID {registro.id} -> {transacao.codigo_transacao}")
            return True
            
        except ValueError as ve:
            self.estatisticas['extrator']['erros'] += 1
            erro = f"Validação falhou para extrator ID {registro.id}: {str(ve)}"
            self.erros.append(erro)
            print(f"  ❌ {erro}")
            return False
        except Exception as e:
            self.estatisticas['extrator']['erros'] += 1
            erro = f"Erro ao migrar extrator ID {registro.id}: {str(e)}"
            self.erros.append(erro)
            print(f"  ❌ {erro}")
            db.session.rollback()
            return False
    
    def executar(self):
        """Executa a migração completa"""
        print("=" * 80)
        print("🔄 MIGRAÇÃO DE CRÉDITOS - LEGADO PARA NOVA ARQUITETURA")
        print("=" * 80)
        print(f"Modo: {'DRY RUN (Simulação)' if self.dry_run else 'PRODUÇÃO (Execução Real)'}")
        print()
        
        with app.app_context():
            try:
                # ===== FORNECEDORES =====
                print("\n📦 MIGRANDO CRÉDITOS DE FORNECEDORES...")
                print("-" * 80)
                registros_fornecedor = ExtratoCreditoFornecedorModel.query.all()
                self.estatisticas['fornecedor']['total'] = len(registros_fornecedor)
                print(f"Total de registros encontrados: {self.estatisticas['fornecedor']['total']}")
                
                for registro in registros_fornecedor:
                    self.migrar_fornecedor(registro)
                
                # ===== FRETEIROS =====
                print("\n🚚 MIGRANDO CRÉDITOS DE FRETEIROS/TRANSPORTADORAS...")
                print("-" * 80)
                registros_freteiro = ExtratoCreditoFreteiroModel.query.all()
                self.estatisticas['freteiro']['total'] = len(registros_freteiro)
                print(f"Total de registros encontrados: {self.estatisticas['freteiro']['total']}")
                
                for registro in registros_freteiro:
                    self.migrar_freteiro(registro)
                
                # ===== EXTRATORES =====
                print("\n🌲 MIGRANDO CRÉDITOS DE EXTRATORES...")
                print("-" * 80)
                registros_extrator = ExtratoCreditoExtratorModel.query.all()
                self.estatisticas['extrator']['total'] = len(registros_extrator)
                print(f"Total de registros encontrados: {self.estatisticas['extrator']['total']}")
                
                for registro in registros_extrator:
                    self.migrar_extrator(registro)
                
                # ===== COMMIT =====
                if not self.dry_run:
                    print("\n💾 Salvando alterações no banco de dados...")
                    db.session.commit()
                    print("✅ Alterações salvas com sucesso!")
                else:
                    print("\n⚠️  DRY RUN - Nenhuma alteração foi salva no banco")
                
                # ===== ESTATÍSTICAS =====
                self.exibir_estatisticas()
                
                return True
                
            except Exception as e:
                if not self.dry_run:
                    db.session.rollback()
                print(f"\n❌ ERRO CRÍTICO: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
    
    def exibir_estatisticas(self):
        """Exibe estatísticas da migração"""
        print("\n" + "=" * 80)
        print("📊 ESTATÍSTICAS DA MIGRAÇÃO")
        print("=" * 80)
        
        total_geral = 0
        migrados_geral = 0
        ignorados_geral = 0
        erros_geral = 0
        
        for entidade, stats in self.estatisticas.items():
            print(f"\n{entidade.upper()}:")
            print(f"  Total:     {stats['total']}")
            print(f"  Migrados:  {stats['migrados']} ✅")
            print(f"  Ignorados: {stats['ignorados']} ⚠️")
            print(f"  Erros:     {stats['erros']} ❌")
            
            total_geral += stats['total']
            migrados_geral += stats['migrados']
            ignorados_geral += stats['ignorados']
            erros_geral += stats['erros']
        
        print("\n" + "-" * 80)
        print(f"TOTAL GERAL:")
        print(f"  Registros:      {total_geral}")
        print(f"  Migrados:       {migrados_geral} ✅")
        print(f"  Ignorados:      {ignorados_geral} ⚠️")
        print(f"  Erros:          {erros_geral} ❌")
        print(f"  Taxa sucesso:   {(migrados_geral/total_geral*100) if total_geral > 0 else 0:.2f}%")
        
        if self.erros:
            print("\n⚠️  ERROS ENCONTRADOS:")
            for erro in self.erros[:10]:  # Exibir apenas os 10 primeiros
                print(f"  - {erro}")
            if len(self.erros) > 10:
                print(f"  ... e mais {len(self.erros) - 10} erros")
        
        print("=" * 80)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migração de Créditos do Sistema Legado')
    parser.add_argument(
        '--executar',
        action='store_true',
        help='Executar migração real (sem este parâmetro, roda em modo DRY RUN)'
    )
    
    args = parser.parse_args()
    
    dry_run = not args.executar
    
    if not dry_run:
        print("\n⚠️  ATENÇÃO: Você está prestes a executar a migração REAL!")
        print("As alterações serão salvas no banco de dados.")
        resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
        
        if resposta.strip().upper() != 'SIM':
            print("❌ Migração cancelada pelo usuário.")
            return
    
    migrador = MigradorCreditos(dry_run=dry_run)
    sucesso = migrador.executar()
    
    if sucesso:
        print("\n✅ Migração concluída!")
        if dry_run:
            print("💡 Para executar a migração real, use: python scripts/migrar_creditos_legado.py --executar")
    else:
        print("\n❌ Migração falhou! Verifique os erros acima.")
        sys.exit(1)


if __name__ == '__main__':
    main()
