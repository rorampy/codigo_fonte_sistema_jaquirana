"""
Script para migrar dados de preços de frete da estrutura antiga (hardcoded) 
para a nova tabela normalizada z_sys_rota_frete_preco_bitola
"""
from sistema import app, db
from sistema.models_views.parametros.rotas_frete.rota_model import RotaFreteModel
from sistema.models_views.parametros.rotas_frete.rota_frete_preco_bitola_model import RotaFretePrecoBitolaModel

def migrar_dados_rota_frete():
    with app.app_context():
        print("Iniciando migração de dados de rotas de frete...")
        
        # Buscar todas as rotas existentes
        rotas = RotaFreteModel.query.filter_by(deletado=False).all()
        
        print(f"Encontradas {len(rotas)} rotas para migrar")
        
        total_migrado = 0
        
        for rota in rotas:
            print(f"\nProcessando rota ID {rota.id}...")
            
            # Mapear campos antigos para produto_id e bitola_id
            # Eucalipto (produto_id = 1)
            campos_eucalipto = [
                (1, 1, rota.euca_preco_custo_frete_bitola_1_100),  # Bitola 1 (Torete)
                (1, 2, rota.euca_preco_custo_frete_bitola_2_100),  # Bitola 2 (18-25)
                (1, 3, rota.euca_preco_custo_frete_bitola_3_100),  # Bitola 3 (25-32)
                (1, 4, rota.euca_preco_custo_frete_bitola_4_100),  # Bitola 4 (33+)
            ]
            
            # Pinus (produto_id = 2)
            campos_pinus = [
                (2, 1, rota.pinus_preco_custo_frete_bitola_1_100),  # Bitola 1 (Torete)
                (2, 2, rota.pinus_preco_custo_frete_bitola_2_100),  # Bitola 2 (18-25)
                (2, 3, rota.pinus_preco_custo_frete_bitola_3_100),  # Bitola 3 (25-32)
                (2, 4, rota.pinus_preco_custo_frete_bitola_4_100),  # Bitola 4 (33+)
                (2, 6, rota.pinus_preco_custo_frete_bitola_5_100),  # Bitola 6 (Madeira Serrada)
            ]
            
            # Biomassa (produto_id = 3)
            campos_biomassa = [
                (3, 5, rota.bio_preco_custo_frete_bitola_5_100),  # Bitola 5 (Cavaco)
            ]
            
            # Juntar todos os campos
            todos_campos = campos_eucalipto + campos_pinus + campos_biomassa
            
            # Inserir na nova tabela normalizada
            for produto_id, bitola_id, preco_100 in todos_campos:
                if preco_100 is not None and preco_100 > 0:
                    # Verificar se já existe
                    existe = RotaFretePrecoBitolaModel.query.filter_by(
                        rota_frete_id=rota.id,
                        produto_id=produto_id,
                        bitola_id=bitola_id,
                        deletado=False
                    ).first()
                    
                    if not existe:
                        novo_preco = RotaFretePrecoBitolaModel(
                            rota_frete_id=rota.id,
                            produto_id=produto_id,
                            bitola_id=bitola_id,
                            preco_frete_100=preco_100,
                            ativo=True
                        )
                        db.session.add(novo_preco)
                        total_migrado += 1
                        print(f"  ✓ Migrado: Produto {produto_id}, Bitola {bitola_id}, Preço: {preco_100}")
        
        # Commit de todas as alterações
        db.session.commit()
        
        print(f"\n{'='*60}")
        print(f"Migração concluída com sucesso!")
        print(f"Total de preços migrados: {total_migrado}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    migrar_dados_rota_frete()
