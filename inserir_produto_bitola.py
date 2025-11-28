"""
Script para inserir bitolas faltantes e relacionamentos entre produtos e bitolas
Baseado na estrutura de produtos e bitolas do sistema
"""
from sistema import app, db
from sistema.models_views.parametros.produto_bitola.produto_bitola_model import ProdutoBitolaModel
from sistema.models_views.parametros.bitola.bitola_model import BitolaModel

with app.app_context():
    print("="*60)
    print("ETAPA 1: Verificando e criando bitolas faltantes...")
    print("="*60)
    
    # Bitolas que devem existir baseado na imagem
    bitolas_necessarias = [
        {'id': 1, 'nome': 'Torete'},
        {'id': 2, 'nome': '18-25'},
        {'id': 3, 'nome': '25-32'},
        {'id': 4, 'nome': '30-40'},
        {'id': 5, 'nome': 'Cavaco'},
        {'id': 6, 'nome': '33+'},
        {'id': 7, 'nome': 'Madeira'},
        # Novas bitolas da imagem que precisam ser criadas
        {'id': 8, 'nome': '14/17 X 2,50'},
        {'id': 9, 'nome': '14/17 X 2,65'},
        {'id': 10, 'nome': '14/17 X 2,73'},
        {'id': 11, 'nome': '14/18 X 2,13'},
        {'id': 12, 'nome': '14/18 X 2,33'},
        {'id': 13, 'nome': '16/22 X 2,33'},
        {'id': 14, 'nome': '16/22 X 2,55'},
        {'id': 15, 'nome': '16/22 X 4,10'},
        {'id': 16, 'nome': '18/22 X 2,12'},
        {'id': 17, 'nome': '18/24 X 2,33'},
        {'id': 18, 'nome': '18/24 X 2,42'},
        {'id': 19, 'nome': '18/24 X 2,55'},
        {'id': 20, 'nome': '18/24 X 2,65'},
        {'id': 21, 'nome': '18/24 X 2,73'},
        {'id': 22, 'nome': '18/24 X 4,10'},
        {'id': 23, 'nome': '23/32 X 2,65'},
        {'id': 24, 'nome': '23/32 X 3,15'},
        {'id': 25, 'nome': '23/32 X 4,10'},
        {'id': 26, 'nome': '25/32 X 2,55'},
        {'id': 27, 'nome': '25/32 X 2,65'},
        {'id': 28, 'nome': '25/32 X 2,73'},
        {'id': 29, 'nome': '25/32 X 3,15'},
        {'id': 30, 'nome': '25/32 X 3,75'},
        {'id': 31, 'nome': '25/32 X 4,10'},
        {'id': 32, 'nome': '25/35 X 2,40'},
        {'id': 33, 'nome': '30/40 X 4,10'},
    ]
    
    bitolas_criadas = 0
    bitolas_existentes = 0
    
    for bitola_data in bitolas_necessarias:
        bitola_existe = BitolaModel.query.filter_by(
            bitola=bitola_data['nome'],
            deletado=False
        ).first()
        
        if bitola_existe:
            print(f"✓ Bitola já existe: {bitola_data['nome']} (ID: {bitola_existe.id})")
            bitolas_existentes += 1
        else:
            nova_bitola = BitolaModel(bitola=bitola_data['nome'], ativo=True)
            db.session.add(nova_bitola)
            db.session.flush()  # Para obter o ID
            print(f"+ Bitola criada: {bitola_data['nome']} (ID: {nova_bitola.id})")
            bitolas_criadas += 1
    
    db.session.commit()
    
    print(f"\nResumo Bitolas:")
    print(f"- Criadas: {bitolas_criadas}")
    print(f"- Já existentes: {bitolas_existentes}")
    
    print("\n" + "="*60)
    print("ETAPA 2: Criando relacionamentos produto-bitola...")
    print("="*60)
    
    # Buscar IDs reais das bitolas após inserção
    bitola_torete = BitolaModel.query.filter_by(bitola='Torete', deletado=False).first()
    bitola_18_25 = BitolaModel.query.filter_by(bitola='18-25', deletado=False).first()
    bitola_25_32 = BitolaModel.query.filter_by(bitola='25-32', deletado=False).first()
    bitola_30_40 = BitolaModel.query.filter_by(bitola='30-40', deletado=False).first()
    bitola_cavaco = BitolaModel.query.filter_by(bitola='Cavaco', deletado=False).first()
    bitola_33_mais = BitolaModel.query.filter_by(bitola='33+', deletado=False).first()
    bitola_madeira = BitolaModel.query.filter_by(bitola='Madeira', deletado=False).first()
    
    # Mapeamento baseado na imagem fornecida:
    # Eucalipto (ID: 1) -> Bitolas: Torete, 18-25, 25-32, 33+
    # Pinus (ID: 2) -> Bitolas: Todas as medidas específicas (14/17, 18/24, 23/32, etc.)
    # Biomassa (ID: 3) -> Bitolas: Cavaco, Madeira
    
    # Mapeamento baseado na imagem fornecida:
    # Eucalipto (ID: 1) -> Bitolas: Torete, 18-25, 25-32, 33+
    # Pinus (ID: 2) -> Bitolas: Todas as medidas específicas (14/17, 18/24, 23/32, etc.)
    # Biomassa (ID: 3) -> Bitolas: Cavaco, Madeira
    
    relacionamentos = []
    
    # Eucalipto (produto_id=1)
    if bitola_torete:
        relacionamentos.append({'produto_id': 1, 'bitola_id': bitola_torete.id})
    if bitola_18_25:
        relacionamentos.append({'produto_id': 1, 'bitola_id': bitola_18_25.id})
    if bitola_25_32:
        relacionamentos.append({'produto_id': 1, 'bitola_id': bitola_25_32.id})
    if bitola_33_mais:
        relacionamentos.append({'produto_id': 1, 'bitola_id': bitola_33_mais.id})
    
    # Pinus (produto_id=2) - Bitolas corretas
    pinus_bitolas = [
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
    
    # Adicionar todas as bitolas do Pinus
    for nome_bitola in pinus_bitolas:
        bitola = BitolaModel.query.filter_by(bitola=nome_bitola, deletado=False).first()
        if bitola:
            relacionamentos.append({'produto_id': 2, 'bitola_id': bitola.id})
    
    # Biomassa (produto_id=3)
    if bitola_cavaco:
        relacionamentos.append({'produto_id': 3, 'bitola_id': bitola_cavaco.id})
    if bitola_madeira:
        relacionamentos.append({'produto_id': 3, 'bitola_id': bitola_madeira.id})
    
    inseridos = 0
    ja_existentes = 0
    
    for rel in relacionamentos:
        # Verificar se já existe
        existe = ProdutoBitolaModel.query.filter_by(
            produto_id=rel['produto_id'],
            bitola_id=rel['bitola_id'],
            deletado=False
        ).first()
        
        if existe:
            ja_existentes += 1
        else:
            # Inserir novo relacionamento
            novo = ProdutoBitolaModel(
                produto_id=rel['produto_id'],
                bitola_id=rel['bitola_id'],
                ativo=True
            )
            db.session.add(novo)
            inseridos += 1
    
    # Commitar todas as inserções
    db.session.commit()
    
    print(f"\nResumo Relacionamentos:")
    print(f"- Inseridos: {inseridos}")
    print(f"- Já existentes: {ja_existentes}")
    print(f"- Total processado: {len(relacionamentos)}")
    print("\n" + "="*60)
    print("Concluído com sucesso!")
    print("="*60)
