#!/usr/bin/env python3
"""
Script para Popular Tabela produto_bitola
=========================================

Este script popula a tabela produto_bitola com os relacionamentos padrão baseados
na estrutura atual do sistema. Define quais bitolas são válidas para cada produto.

Mapeamento atual:
- Eucalipto (ID=1): Torete(1), 18-25(2), 25-32(3), 40+(4)
- Pinus (ID=2): Torete(1), 18-25(2), 25-32(3), 40+(4), Madeira Serrada(6)
- Biomassa (ID=3): Cavaco(5), Madeira(7)

USO: python popular_produto_bitola.py
"""

import os
import sys
from datetime import datetime

from sistema import app, db
from sistema.models_views.controle_carga.produto.produto_model import ProdutoModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel
from sistema.models_views.parametros.produto_bitola.produto_bitola_model import ProdutoBitolaModel


def log_populacao(mensagem):
    """Helper para log da população"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensagem}")


def popular_relacionamentos():
    """Popula a tabela produto_bitola com os relacionamentos padrão"""
    log_populacao("Iniciando população da tabela produto_bitola")
    
    with app.app_context():
        try:
            # Verificar se já existem relacionamentos
            relacionamentos_existentes = ProdutoBitolaModel.query.count()
            if relacionamentos_existentes > 0:
                resposta = input(f"Já existem {relacionamentos_existentes} relacionamentos. Continuar? (s/N): ")
                if resposta.lower() != 's':
                    log_populacao("População cancelada pelo usuário.")
                    return
            
            # Buscar produtos e bitolas existentes
            produtos = ProdutoModel.listar_produtos()
            bitolas = BitolaModel.listar_bitolas_ativas()
            
            log_populacao(f"Encontrados {len(produtos)} produtos e {len(bitolas)} bitolas")
            
            # Criar dicionário de bitolas por nome para facilitar o mapeamento
            bitolas_por_nome = {}
            for bitola in bitolas:
                # Normalizar nomes comuns
                nome = bitola.bitola.lower().strip()
                if 'torete' in nome:
                    bitolas_por_nome['torete'] = bitola.id
                elif '18-25' in nome or '18_25' in nome:
                    bitolas_por_nome['18-25'] = bitola.id
                elif '25-32' in nome or '25_32' in nome:
                    bitolas_por_nome['25-32'] = bitola.id
                elif '40' in nome and ('+' in nome or 'mais' in nome):
                    bitolas_por_nome['40+'] = bitola.id
                elif 'cavaco' in nome:
                    bitolas_por_nome['cavaco'] = bitola.id
                elif 'madeira serrada' in nome or 'madeira_serrada' in nome:
                    bitolas_por_nome['madeira_serrada'] = bitola.id
                elif 'madeira' in nome and 'serrada' not in nome:
                    bitolas_por_nome['madeira'] = bitola.id
                
                bitolas_por_nome[bitola.id] = bitola.id  # Mapeamento por ID também
            
            log_populacao(f"Bitolas mapeadas: {list(bitolas_por_nome.keys())}")
            
            # Definir relacionamentos padrão
            relacionamentos_padrao = {
                'Eucalipto': ['torete', '18-25', '25-32', '40+'],
                'Pinus': ['torete', '18-25', '25-32', '40+', 'madeira_serrada'],  
                'Biomassa': ['cavaco', 'madeira']
            }
            
            # Criar relacionamentos
            total_criados = 0
            for produto in produtos:
                nome_produto = produto.nome.strip()
                log_populacao(f"Processando produto: {nome_produto} (ID: {produto.id})")
                
                bitolas_produto = relacionamentos_padrao.get(nome_produto, [])
                if not bitolas_produto:
                    # Se não encontrar pelo nome exato, tentar busca parcial
                    for nome_padrao, bitolas_list in relacionamentos_padrao.items():
                        if nome_padrao.lower() in nome_produto.lower():
                            bitolas_produto = bitolas_list
                            break
                
                if bitolas_produto:
                    for nome_bitola in bitolas_produto:
                        bitola_id = bitolas_por_nome.get(nome_bitola)
                        if bitola_id:
                            # Verificar se já existe
                            relacionamento_existente = ProdutoBitolaModel.query.filter_by(
                                produto_id=produto.id,
                                bitola_id=bitola_id,
                                deletado=False
                            ).first()
                            
                            if not relacionamento_existente:
                                novo_relacionamento = ProdutoBitolaModel(
                                    produto_id=produto.id,
                                    bitola_id=bitola_id,
                                    ativo=True
                                )
                                db.session.add(novo_relacionamento)
                                total_criados += 1
                                log_populacao(f"  ✓ Criado: {nome_produto} → {nome_bitola} (bitola_id: {bitola_id})")
                            else:
                                log_populacao(f"  - Já existe: {nome_produto} → {nome_bitola}")
                        else:
                            log_populacao(f"  ⚠ Bitola '{nome_bitola}' não encontrada para {nome_produto}")
                else:
                    log_populacao(f"  ⚠ Nenhum relacionamento definido para {nome_produto}")
            
            # Commit das mudanças
            db.session.commit()
            
            log_populacao("=" * 60)
            log_populacao("POPULAÇÃO CONCLUÍDA COM SUCESSO!")
            log_populacao("=" * 60)
            log_populacao(f"Total de relacionamentos criados: {total_criados}")
            
            # Exibir resumo
            log_populacao("\nRESUMO DOS RELACIONAMENTOS:")
            produtos_com_relacionamento = ProdutoBitolaModel.obter_produtos_com_bitolas()
            for produto_id, dados in produtos_com_relacionamento.items():
                bitolas_nomes = [b['nome'] for b in dados['bitolas']]
                log_populacao(f"  {dados['nome']}: {', '.join(bitolas_nomes)}")
            
        except Exception as e:
            log_populacao(f"ERRO DURANTE A POPULAÇÃO: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    popular_relacionamentos()