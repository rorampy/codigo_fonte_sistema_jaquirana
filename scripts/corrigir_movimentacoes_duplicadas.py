"""
Script para corrigir movimentações financeiras duplicadas.
Desativa movimentações órfãs vinculadas a agendamentos/lançamentos já excluídos
ou a transações OFX desconciliadas.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from sistema.models_views.base_model import db

with app.app_context():
    print("=" * 60)
    print("Corrigindo movimentações financeiras duplicadas...")
    print("=" * 60)

    # 1) Movimentações vinculadas a agendamentos excluídos
    db.session.execute(db.text("""
        UPDATE mov_movimentacao_financeira m
        INNER JOIN fin_agendamento_pagamento a ON m.agendamento_id = a.id
        SET m.ativo = 0,
            m.deletado = 1,
            m.data_alteracao = NOW()
        WHERE m.ativo = 1
          AND m.deletado = 0
          AND (a.deletado = 1 OR a.ativo = 0)
    """))

    # 2) Movimentações vinculadas a lançamentos avulsos excluídos
    db.session.execute(db.text("""
        UPDATE mov_movimentacao_financeira m
        INNER JOIN lan_lancamento_avulso la ON m.conciliacao_lancamento_avulso_id = la.id
        SET m.ativo = 0,
            m.deletado = 1,
            m.data_alteracao = NOW()
        WHERE m.ativo = 1
          AND m.deletado = 0
          AND (la.deletado = 1 OR la.ativo = 0)
    """))

    # 3) Movimentações de conciliação cujas transações OFX foram desconciliadas
    db.session.execute(db.text("""
        UPDATE mov_movimentacao_financeira m
        INNER JOIN im_importacao_ofx ofx ON m.importacao_ofx_id = ofx.id
        SET m.ativo = 0,
            m.deletado = 1,
            m.data_alteracao = NOW()
        WHERE m.ativo = 1
          AND m.deletado = 0
          AND m.conciliacao_bancaria = 1
          AND ofx.conciliado = 0
          AND ofx.dados_conciliacao_json IS NULL
    """))

    db.session.commit()
    print("Correção aplicada com sucesso!")
