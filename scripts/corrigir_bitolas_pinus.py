"""
Script para corrigir relacionamentos de bitolas do Pinus
Remove relacionamentos incorretos e mantém apenas os corretos
"""
from sistema import app, db
from sistema.models_views.parametros.produto_bitola.produto_bitola_model import ProdutoBitolaModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel

with app.app_context():
    print("="*60)
    print("Corrigindo relacionamentos de bitolas do Pinus...")
    print("="*60)
    
    # Bitolas corretas para Pinus (produto_id = 2) baseado no que está renderizando
    bitolas_corretas_pinus = [
        'Torete',
        '18-25',
        '25-32',
        '30-40',
        '33+',
        '14/17 X 2,50',
        '14/17 X 2,65',
        '14/17 X 2,73',
        '14/18 X 2,13',
        '14/18 X 2,33',
        '16/22 X 2,33',
        '16/22 X 2,55',
        '16/22 X 4,10',
        '18/22 X 2,12',
        '18/24 X 2,33',
        '18/24 X 2,42',
        '18/24 X 2,55',
        '18/24 X 2,65',
        '18/24 X 2,73',
        '18/24 X 4,10',
        '23/32 X 2,65',
        '23/32 X 3,15',
        '23/32 X 4,10',
        '25/32 X 2,55',
        '25/32 X 2,65',
        '25/32 X 2,73',
        '25/32 X 3,15',
        '25/32 X 3,75',
        '25/32 X 4,10',
        '25/35 X 2,40',
        '30/40 X 4,10'
    ]
    
    # Buscar IDs das bitolas corretas
    ids_bitolas_corretas = []
    bitolas_nao_encontradas = []
    
    for nome_bitola in bitolas_corretas_pinus:
        bitola = BitolaModel.query.filter_by(bitola=nome_bitola, deletado=False).first()
        if bitola:
            ids_bitolas_corretas.append(bitola.id)
            print(f"✓ Bitola encontrada: {nome_bitola} (ID: {bitola.id})")
        else:
            bitolas_nao_encontradas.append(nome_bitola)
            print(f"✗ Bitola NÃO encontrada: {nome_bitola}")
    
    if bitolas_nao_encontradas:
        print(f"\n⚠️  ATENÇÃO: {len(bitolas_nao_encontradas)} bitolas não foram encontradas no banco!")
        print("Essas bitolas precisam ser criadas primeiro.")
        for b in bitolas_nao_encontradas:
            print(f"  - {b}")
    
    print("\n" + "="*60)
    print("Removendo relacionamentos incorretos do Pinus...")
    print("="*60)
    
    # Buscar todos os relacionamentos atuais do Pinus
    relacionamentos_pinus = ProdutoBitolaModel.query.filter_by(
        produto_id=2,
        deletado=False
    ).all()
    
    removidos = 0
    mantidos = 0
    
    for rel in relacionamentos_pinus:
        if rel.bitola_id not in ids_bitolas_corretas:
            # Remover relacionamento incorreto
            bitola_obj = BitolaModel.query.get(rel.bitola_id)
            nome_bitola = bitola_obj.bitola if bitola_obj else f"ID {rel.bitola_id}"
            print(f"- Removendo: {nome_bitola}")
            rel.deletado = True
            rel.ativo = False
            removidos += 1
        else:
            mantidos += 1
    
    db.session.commit()
    
    print("\n" + "="*60)
    print("Adicionando relacionamentos faltantes...")
    print("="*60)
    
    adicionados = 0
    
    for bitola_id in ids_bitolas_corretas:
        # Verificar se já existe
        existe = ProdutoBitolaModel.query.filter_by(
            produto_id=2,
            bitola_id=bitola_id,
            deletado=False
        ).first()
        
        if not existe:
            # Adicionar novo relacionamento
            bitola_obj = BitolaModel.query.get(bitola_id)
            nome_bitola = bitola_obj.bitola if bitola_obj else f"ID {bitola_id}"
            
            novo = ProdutoBitolaModel(
                produto_id=2,
                bitola_id=bitola_id,
                ativo=True
            )
            db.session.add(novo)
            print(f"+ Adicionado: {nome_bitola}")
            adicionados += 1
    
    db.session.commit()
    
    print("\n" + "="*60)
    print("RESUMO:")
    print("="*60)
    print(f"Relacionamentos mantidos: {mantidos}")
    print(f"Relacionamentos removidos: {removidos}")
    print(f"Relacionamentos adicionados: {adicionados}")
    print(f"Total de bitolas corretas para Pinus: {len(ids_bitolas_corretas)}")
    print("="*60)
    print("Concluído com sucesso!")
