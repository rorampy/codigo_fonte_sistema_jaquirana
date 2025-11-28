#!/usr/bin/env python3
"""
Script de Migração: Fornecedores para Estrutura Normalizada
============================================================

Este script migra os dados das tabelas antigas de fornecedores para a nova estrutura normalizada:

MIGRAÇÃO DE TABELAS:
1. for_fornecedor → for_fornecedor_cadastro (dados básicos)
2. for_fornecedor → for_fornecedor_preco_custo_bitola (preços de custo)
3. for_fornecedor → for_fornecedor_preco_custo_extracao (custos de extração)
4. for_fornecedor → for_fornecedor_conta_bancaria (dados bancários)
5. for_fornecedor_madeira_posta → for_fornecedor_madeira_posta_preco_bitola (madeira posta normalizada)

FILTROS APLICADOS:
- Apenas registros com ativo=True e deletado=False são migrados
- Para custos de extração: também filtra por custo_extracao=True
- Para madeira posta: verifica se o fornecedor associado também está ativo

IMPORTANTE: 
- Execute com cuidado em ambiente de produção
- Faça backup das tabelas antes de executar
- Teste em ambiente de desenvolvimento primeiro

USO: python migracao_fornecedores_normalizacao.py
"""

import os
import sys
from datetime import datetime

from sistema import app, db
from sistema.models_views.gerenciar.fornecedor.fornecedor_model import FornecedorModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_cadastro_model import FornecedorCadastroModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_bitola_model import FornecedorPrecoCustoBitolaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_preco_custo_extracao_model import FornecedorPrecoCustoExtracaoModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_conta_bancaria_model import FornecedorContaBancariaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_madeira_posta_model import FornecedorMadeiraPostaModel
from sistema.models_views.gerenciar.fornecedor.fornecedor_madeira_posta_preco_bitola_model import FornecedorMadeiraPostaPrecoBitolaModel


def log_migração(mensagem):
    """Helper para log da migração"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensagem}")


def verificar_dados_existentes():
    """Verifica se já existem dados nas tabelas normalizadas"""
    log_migração("Verificando dados existentes nas tabelas normalizadas...")
    
    cadastros_existentes = FornecedorCadastroModel.query.count()
    precos_existentes = FornecedorPrecoCustoBitolaModel.query.count()
    extrações_existentes = FornecedorPrecoCustoExtracaoModel.query.count()
    contas_existentes = FornecedorContaBancariaModel.query.count()
    madeiras_existentes = FornecedorMadeiraPostaPrecoBitolaModel.query.count()
    
    log_migração(f"Registros encontrados:")
    log_migração(f"  - Fornecedores cadastro: {cadastros_existentes}")
    log_migração(f"  - Preços custo bitola: {precos_existentes}")
    log_migração(f"  - Custos extração: {extrações_existentes}")
    log_migração(f"  - Contas bancárias: {contas_existentes}")
    log_migração(f"  - Madeiras posta normalizadas: {madeiras_existentes}")
    
    # Mostrar quantos registros ativos serão migrados
    log_migração("\nRegistros ativos disponíveis para migração:")
    fornecedores_ativos = FornecedorModel.query.filter_by(deletado=False, ativo=True).count()
    fornecedores_com_extracao = FornecedorModel.query.filter(
        FornecedorModel.deletado == False,
        FornecedorModel.ativo == True,
        FornecedorModel.custo_extracao == True
    ).count()
    madeiras_ativas = FornecedorMadeiraPostaModel.query.filter_by(deletado=False, ativo=True).count()
    
    log_migração(f"  - Fornecedores ativos: {fornecedores_ativos}")
    log_migração(f"  - Fornecedores com extração: {fornecedores_com_extracao}")
    log_migração(f"  - Registros de madeira posta ativos: {madeiras_ativas}")
    
    if any([cadastros_existentes, precos_existentes, extrações_existentes, contas_existentes, madeiras_existentes]):
        resposta = input("\nATENÇÃO: Já existem dados nas tabelas normalizadas. Continuar? (s/N): ")
        if resposta.lower() != 's':
            log_migração("Migração cancelada pelo usuário.")
            return False
    
    return True


def migrar_dados_basicos_fornecedores():
    """Migra dados básicos de for_fornecedor para for_fornecedor_cadastro
    Filtra apenas fornecedores ativos e não deletados
    """
    log_migração("Iniciando migração de dados básicos dos fornecedores...")
    
    fornecedores_antigos = FornecedorModel.query.filter_by(deletado=False, ativo=True).all()
    total = len(fornecedores_antigos)
    log_migração(f"Encontrados {total} fornecedores para migrar")
    
    migrados = 0
    for idx, fornecedor_antigo in enumerate(fornecedores_antigos, 1):
        try:
            # Verificar se já existe
            fornecedor_existente = FornecedorCadastroModel.query.filter_by(
                numero_documento=fornecedor_antigo.numero_documento
            ).first()
            
            if fornecedor_existente:
                log_migração(f"[{idx}/{total}] Fornecedor {fornecedor_antigo.identificacao} já migrado - PULANDO")
                continue
            
            # Criar novo registro normalizado
            novo_fornecedor = FornecedorCadastroModel(
                fatura_via_cpf=fornecedor_antigo.fatura_via_cpf,
                identificacao=fornecedor_antigo.identificacao,
                numero_documento=fornecedor_antigo.numero_documento,
                telefone=fornecedor_antigo.telefone,
                classe_fornecedor=fornecedor_antigo.classe_fornecedor,
                senar=fornecedor_antigo.senar,
                funrural=fornecedor_antigo.funrural,
                controle_entrada=fornecedor_antigo.controle_entrada,
                valor_contrato_100=fornecedor_antigo.valor_contrato_100,
                estimativa_tonelada=fornecedor_antigo.estimativa_tonelada,
                ativo=fornecedor_antigo.ativo,
                arquivo_senar_id=fornecedor_antigo.arquivo_senar_id,
                imposto_id=fornecedor_antigo.imposto_id,
                contrato_fornecedor_id=fornecedor_antigo.contrato_fornecedor_id,
                madeira_posta=fornecedor_antigo.madeira_posta,
                possui_comissionado=fornecedor_antigo.possui_comissionado,
                custo_extracao=fornecedor_antigo.custo_extracao
            )
            
            # Preservar campos de auditoria
            novo_fornecedor.data_cadastro = fornecedor_antigo.data_cadastro
            novo_fornecedor.data_alteracao = fornecedor_antigo.data_alteracao
            
            db.session.add(novo_fornecedor)
            db.session.flush()  # Para obter o ID
            
            # Associar o ID antigo com o novo para as próximas migrações
            fornecedor_antigo._novo_id = novo_fornecedor.id
            
            migrados += 1
            log_migração(f"[{idx}/{total}] Migrado: {fornecedor_antigo.identificacao} (ID antigo: {fornecedor_antigo.id} → ID novo: {novo_fornecedor.id})")
            
        except Exception as e:
            log_migração(f"[{idx}/{total}] ERRO ao migrar {fornecedor_antigo.identificacao}: {e}")
            db.session.rollback()
            raise
    
    log_migração(f"Migração de dados básicos concluída: {migrados}/{total} fornecedores migrados")
    return migrados


def migrar_precos_custo_bitola():
    """Migra preços de custo por bitola para tabela normalizada
    Filtra apenas fornecedores ativos e não deletados
    """
    log_migração("Iniciando migração de preços de custo por bitola...")
    
    fornecedores_antigos = FornecedorModel.query.filter_by(deletado=False, ativo=True).all()
    total = len(fornecedores_antigos)
    migrados = 0
    
    # Mapeamento produto_id → bitola_id → campos no modelo antigo
    mapeamento_precos = {
        1: {  # Eucalipto
            1: ('euca_bitola_1_id', 'euca_preco_custo_bitola_1_100'),  # Torete
            2: ('euca_bitola_2_id', 'euca_preco_custo_bitola_2_100'),  # 18-25
            3: ('euca_bitola_3_id', 'euca_preco_custo_bitola_3_100'),  # 25-32
            4: ('euca_bitola_4_id', 'euca_preco_custo_bitola_4_100'),  # 33-40
        },
        2: {  # Pinus
            1: ('pinus_bitola_1_id', 'pinus_preco_custo_bitola_1_100'),  # Torete
            2: ('pinus_bitola_2_id', 'pinus_preco_custo_bitola_2_100'),  # 18-25
            3: ('pinus_bitola_3_id', 'pinus_preco_custo_bitola_3_100'),  # 25-32
            4: ('pinus_bitola_4_id', 'pinus_preco_custo_bitola_4_100'),  # 33-40
            6: ('pinus_bitola_5_id', 'pinus_preco_custo_bitola_5_100'),  # 40+ (Madeira Serrada)
        },
        3: {  # Biomassa
            5: ('bio_bitola_5_id', 'bio_preco_custo_bitola_5_100'),    # Cavaco
            7: ('bio_bitola_7_id', 'bio_preco_custo_bitola_7_100'),    # Madeira
        }
    }
    
    for idx, fornecedor_antigo in enumerate(fornecedores_antigos, 1):
        try:
            # Buscar o fornecedor novo correspondente
            fornecedor_novo = FornecedorCadastroModel.query.filter_by(
                numero_documento=fornecedor_antigo.numero_documento
            ).first()
            
            if not fornecedor_novo:
                log_migração(f"[{idx}/{total}] Fornecedor novo não encontrado para {fornecedor_antigo.identificacao}")
                continue
            
            registros_criados = 0
            
            for produto_id, bitolas in mapeamento_precos.items():
                for bitola_id, (campo_bitola_id, campo_preco) in bitolas.items():
                    # Verificar se tem valores definidos
                    bitola_id_valor = getattr(fornecedor_antigo, campo_bitola_id, None)
                    preco_valor = getattr(fornecedor_antigo, campo_preco, None)
                    
                    if preco_valor is not None and preco_valor > 0:
                        # Usar o bitola_id do mapeamento se não estiver definido no campo _id
                        bitola_final = bitola_id_valor if bitola_id_valor else bitola_id
                        
                        # Verificar se já existe
                        preco_existente = FornecedorPrecoCustoBitolaModel.query.filter_by(
                            fornecedor_id=fornecedor_novo.id,
                            produto_id=produto_id,
                            bitola_id=bitola_final
                        ).first()
                        
                        if not preco_existente:
                            novo_preco = FornecedorPrecoCustoBitolaModel(
                                fornecedor_id=fornecedor_novo.id,
                                produto_id=produto_id,
                                bitola_id=bitola_final,
                                valor_preco_custo_100=preco_valor
                            )
                            
                            # Preservar auditoria
                            novo_preco.data_cadastro = fornecedor_antigo.data_cadastro
                            novo_preco.data_alteracao = fornecedor_antigo.data_alteracao
                            
                            db.session.add(novo_preco)
                            registros_criados += 1
            
            if registros_criados > 0:
                migrados += 1
                log_migração(f"[{idx}/{total}] Preços custo migrados: {fornecedor_antigo.identificacao} ({registros_criados} registros)")
            
        except Exception as e:
            log_migração(f"[{idx}/{total}] ERRO ao migrar preços custo {fornecedor_antigo.identificacao}: {e}")
            db.session.rollback()
            raise
    
    log_migração(f"Migração de preços custo concluída: {migrados} fornecedores processados")
    return migrados


def migrar_custos_extracao():
    """Migra custos de extração para tabela normalizada"""
    log_migração("Iniciando migração de custos de extração...")
    
    fornecedores_antigos = FornecedorModel.query.filter(
        FornecedorModel.deletado == False,
        FornecedorModel.ativo == True,
        FornecedorModel.custo_extracao == True
    ).all()
    total = len(fornecedores_antigos)
    migrados = 0
    
    # Mapeamento produto_id → bitola_id → campo no modelo antigo
    mapeamento_extrações = {
        1: {  # Eucalipto
            1: 'euca_custo_extracao_bitola_1_100',  # Torete
            2: 'euca_custo_extracao_bitola_2_100',  # 18-25
            3: 'euca_custo_extracao_bitola_3_100',  # 25-32
            4: 'euca_custo_extracao_bitola_4_100',  # 33-40
        },
        2: {  # Pinus
            1: 'pinus_custo_extracao_bitola_1_100',  # Torete
            2: 'pinus_custo_extracao_bitola_2_100',  # 18-25
            3: 'pinus_custo_extracao_bitola_3_100',  # 25-32
            4: 'pinus_custo_extracao_bitola_4_100',  # 33-40
            6: 'pinus_custo_extracao_bitola_5_100',  # 40+ (Madeira Serrada)
        },
        3: {  # Biomassa
            5: 'bio_custo_extracao_bitola_5_100',    # Cavaco
            7: 'bio_custo_extracao_bitola_7_100',    # Madeira
        }
    }
    
    for idx, fornecedor_antigo in enumerate(fornecedores_antigos, 1):
        try:
            # Buscar o fornecedor novo correspondente
            fornecedor_novo = FornecedorCadastroModel.query.filter_by(
                numero_documento=fornecedor_antigo.numero_documento
            ).first()
            
            if not fornecedor_novo:
                log_migração(f"[{idx}/{total}] Fornecedor novo não encontrado para {fornecedor_antigo.identificacao}")
                continue
            
            registros_criados = 0
            
            for produto_id, bitolas in mapeamento_extrações.items():
                for bitola_id, campo_custo in bitolas.items():
                    custo_valor = getattr(fornecedor_antigo, campo_custo, None)
                    
                    if custo_valor is not None and custo_valor > 0:
                        # extrator_id é obrigatório - pular se não tiver
                        if not fornecedor_antigo.extrator_id:
                            continue
                            
                        # Verificar se já existe
                        custo_existente = FornecedorPrecoCustoExtracaoModel.query.filter_by(
                            fornecedor_id=fornecedor_novo.id,
                            produto_id=produto_id,
                            bitola_id=bitola_id
                        ).first()
                        
                        if not custo_existente:
                            novo_custo = FornecedorPrecoCustoExtracaoModel(
                                fornecedor_id=fornecedor_novo.id,
                                extrator_id=fornecedor_antigo.extrator_id,
                                produto_id=produto_id,
                                bitola_id=bitola_id,
                                custo_extracao_100=custo_valor
                            )
                            
                            # Preservar auditoria
                            novo_custo.data_cadastro = fornecedor_antigo.data_cadastro
                            novo_custo.data_alteracao = fornecedor_antigo.data_alteracao
                            
                            db.session.add(novo_custo)
                            registros_criados += 1
            
            if registros_criados > 0:
                migrados += 1
                log_migração(f"[{idx}/{total}] Custos extração migrados: {fornecedor_antigo.identificacao} ({registros_criados} registros)")
            
        except Exception as e:
            log_migração(f"[{idx}/{total}] ERRO ao migrar custos extração {fornecedor_antigo.identificacao}: {e}")
            db.session.rollback()
            raise
    
    log_migração(f"Migração de custos extração concluída: {migrados} fornecedores processados")
    return migrados


def migrar_contas_bancarias():
    """Migra dados bancários para tabela normalizada"""
    log_migração("Iniciando migração de contas bancárias...")
    
    fornecedores_antigos = FornecedorModel.query.filter(
        FornecedorModel.deletado == False,
        FornecedorModel.ativo == True
    ).all()
    total = len(fornecedores_antigos)
    migrados = 0
    
    for idx, fornecedor_antigo in enumerate(fornecedores_antigos, 1):
        try:
            # Verificar se tem dados bancários
            tem_dados_bancarios = any([
                fornecedor_antigo.instituicao_financeira_id,
                fornecedor_antigo.agencia_bancaria,
                fornecedor_antigo.conta_bancaria,
                fornecedor_antigo.chave_pix
            ])
            
            if not tem_dados_bancarios:
                continue
            
            # Buscar o fornecedor novo correspondente
            fornecedor_novo = FornecedorCadastroModel.query.filter_by(
                numero_documento=fornecedor_antigo.numero_documento
            ).first()
            
            if not fornecedor_novo:
                log_migração(f"[{idx}/{total}] Fornecedor novo não encontrado para {fornecedor_antigo.identificacao}")
                continue
            
            # Verificar se já existe conta bancária
            conta_existente = FornecedorContaBancariaModel.query.filter_by(
                fornecedor_id=fornecedor_novo.id
            ).first()
            
            if not conta_existente:
                nova_conta = FornecedorContaBancariaModel(
                    fornecedor_id=fornecedor_novo.id,
                    instituicao_financeira_id=fornecedor_antigo.instituicao_financeira_id,
                    agencia_bancaria=fornecedor_antigo.agencia_bancaria,
                    conta_bancaria=fornecedor_antigo.conta_bancaria,
                    chave_pix=fornecedor_antigo.chave_pix
                )
                
                # Preservar auditoria
                nova_conta.data_cadastro = fornecedor_antigo.data_cadastro
                nova_conta.data_alteracao = fornecedor_antigo.data_alteracao
                
                db.session.add(nova_conta)
                migrados += 1
                log_migração(f"[{idx}/{total}] Conta bancária migrada: {fornecedor_antigo.identificacao}")
            
        except Exception as e:
            log_migração(f"[{idx}/{total}] ERRO ao migrar conta bancária {fornecedor_antigo.identificacao}: {e}")
            db.session.rollback()
            raise
    
    log_migração(f"Migração de contas bancárias concluída: {migrados} contas migradas")
    return migrados


def migrar_madeira_posta():
    """Migra madeira posta da tabela antiga para a nova estrutura normalizada"""
    log_migração("Iniciando migração de madeira posta...")
    
    madeiras_antigas = FornecedorMadeiraPostaModel.query.filter_by(deletado=False, ativo=True).all()
    total = len(madeiras_antigas)
    migrados = 0
    
    # Mapeamento produto_id → bitola_id → (campo_bitola_id, campo_preco) no modelo antigo
    mapeamento_madeira_posta = {
        1: {  # Eucalipto
            1: ('euca_bitola_1_id', 'euca_bitola_1_preco_100'),  # Torete
            2: ('euca_bitola_2_id', 'euca_bitola_2_preco_100'),  # 18-25
            3: ('euca_bitola_3_id', 'euca_bitola_3_preco_100'),  # 25-32
            4: ('euca_bitola_4_id', 'euca_bitola_4_preco_100'),  # 33-40
        },
        2: {  # Pinus
            1: ('pinus_bitola_1_id', 'pinus_bitola_1_preco_100'),  # Torete
            2: ('pinus_bitola_2_id', 'pinus_bitola_2_preco_100'),  # 18-25
            3: ('pinus_bitola_3_id', 'pinus_bitola_3_preco_100'),  # 25-32
            4: ('pinus_bitola_4_id', 'pinus_bitola_4_preco_100'),  # 33-40
            6: ('pinus_bitola_5_id', 'pinus_bitola_5_preco_100'),  # 40+ (Madeira Serrada)
        },
        3: {  # Biomassa
            5: ('bio_bitola_5_id', 'bio_bitola_5_preco_100'),    # Cavaco
            7: ('bio_bitola_7_id', 'bio_bitola_7_preco_100'),    # Madeira
        }
    }
    
    for idx, madeira_antiga in enumerate(madeiras_antigas, 1):
        try:
            # Buscar o fornecedor novo correspondente
            fornecedor_antigo = FornecedorModel.query.filter(
                FornecedorModel.id == madeira_antiga.fornecedor_id,
                FornecedorModel.deletado == False,
                FornecedorModel.ativo == True
            ).first()
            if not fornecedor_antigo:
                log_migração(f"[{idx}/{total}] Fornecedor antigo não encontrado ou inativo (ID: {madeira_antiga.fornecedor_id})")
                continue
                
            fornecedor_novo = FornecedorCadastroModel.query.filter_by(
                numero_documento=fornecedor_antigo.numero_documento
            ).first()
            
            if not fornecedor_novo:
                log_migração(f"[{idx}/{total}] Fornecedor novo não encontrado para {fornecedor_antigo.identificacao}")
                continue
            
            registros_criados = 0
            
            for produto_id, bitolas in mapeamento_madeira_posta.items():
                for bitola_id, (campo_bitola_id, campo_preco) in bitolas.items():
                    # Verificar se tem valores definidos
                    bitola_id_valor = getattr(madeira_antiga, campo_bitola_id, None)
                    preco_valor = getattr(madeira_antiga, campo_preco, None)
                    
                    if preco_valor is not None and preco_valor > 0:
                        # Usar o bitola_id do mapeamento se não estiver definido no campo _id
                        bitola_final = bitola_id_valor if bitola_id_valor else bitola_id
                        
                        # Verificar se já existe
                        madeira_existente = FornecedorMadeiraPostaPrecoBitolaModel.query.filter_by(
                            fornecedor_id=fornecedor_novo.id,
                            cliente_id=madeira_antiga.cliente_id,
                            produto_id=produto_id,
                            bitola_id=bitola_final,
                            transportadora_id=madeira_antiga.transportadora_id
                        ).first()
                        
                        if not madeira_existente:
                            nova_madeira = FornecedorMadeiraPostaPrecoBitolaModel(
                                fornecedor_id=fornecedor_novo.id,
                                cliente_id=madeira_antiga.cliente_id,
                                transportadora_id=madeira_antiga.transportadora_id,
                                produto_id=produto_id,
                                bitola_id=bitola_final,
                                preco_madeira_posta_100=preco_valor
                            )
                            
                            # Preservar auditoria
                            nova_madeira.data_cadastro = madeira_antiga.data_cadastro
                            nova_madeira.data_alteracao = madeira_antiga.data_alteracao
                            
                            db.session.add(nova_madeira)
                            registros_criados += 1
            
            if registros_criados > 0:
                migrados += 1
                log_migração(f"[{idx}/{total}] Madeira posta migrada: {fornecedor_antigo.identificacao} → Cliente ID {madeira_antiga.cliente_id} ({registros_criados} registros)")
            
        except Exception as e:
            log_migração(f"[{idx}/{total}] ERRO ao migrar madeira posta (ID: {madeira_antiga.id}): {e}")
            db.session.rollback()
            raise
    
    log_migração(f"Migração de madeira posta concluída: {migrados} registros processados")
    return migrados


def executar_migração():
    """Executa todas as migrações em sequência"""
    log_migração("=" * 60)
    log_migração("INICIANDO MIGRAÇÃO DE FORNECEDORES PARA ESTRUTURA NORMALIZADA")
    log_migração("=" * 60)
    
    with app.app_context():
        try:
            # Verificação inicial
            if not verificar_dados_existentes():
                return
            
            # 1. Migrar dados básicos
            dados_basicos_migrados = migrar_dados_basicos_fornecedores()
            db.session.commit()
            log_migração(f"✓ Dados básicos commitados: {dados_basicos_migrados} fornecedores")
            
            # 2. Migrar preços de custo
            precos_migrados = migrar_precos_custo_bitola()
            db.session.commit()
            log_migração(f"✓ Preços de custo commitados: {precos_migrados} fornecedores")
            
            # 3. Migrar custos de extração
            extrações_migradas = migrar_custos_extracao()
            db.session.commit()
            log_migração(f"✓ Custos de extração commitados: {extrações_migradas} fornecedores")
            
            # 4. Migrar contas bancárias
            contas_migradas = migrar_contas_bancarias()
            db.session.commit()
            log_migração(f"✓ Contas bancárias commitadas: {contas_migradas} contas")
            
            # 5. Migrar madeira posta
            madeiras_migradas = migrar_madeira_posta()
            db.session.commit()
            log_migração(f"✓ Madeira posta commitada: {madeiras_migradas} registros")
            
            log_migração("=" * 60)
            log_migração("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            log_migração("=" * 60)
            log_migração("RESUMO:")
            log_migração(f"  - Fornecedores migrados: {dados_basicos_migrados}")
            log_migração(f"  - Preços de custo: {precos_migrados} fornecedores")
            log_migração(f"  - Custos de extração: {extrações_migradas} fornecedores")
            log_migração(f"  - Contas bancárias: {contas_migradas} contas")
            log_migração(f"  - Madeira posta: {madeiras_migradas} registros")
            log_migração("=" * 60)
            
        except Exception as e:
            log_migração(f"ERRO DURANTE A MIGRAÇÃO: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    executar_migração()