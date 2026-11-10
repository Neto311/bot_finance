from sqlalchemy.orm import Session
from sqlalchemy import extract

from datetime import date

from models.chat import MensagemChat
from services.groq_client import interpretar_mensagem_chat
from routes.routes import registrar_conforme_integracao, resumo
from models.financas import Usuario, Financa

async def processar_mensagem_usuario(
        texto: str,
        usuario_id: int,
        db: Session,
        tipo_entrada: str = "texto",
        dados_extras_usuario: dict | None = None,
) -> tuple[MensagemChat, MensagemChat]:
    msg_usuario = MensagemChat(
        usuario_id = usuario_id,
        remetente  = "usuario",
        tipo = tipo_entrada,
        conteudo = texto,
        dados_extras = dados_extras_usuario,
    )

    db.add(msg_usuario)
    db.commit()
    db.refresh(msg_usuario)

    analise = interpretar_mensagem_chat(texto)
    intencao = analise.get("intencao")

    if intencao == "REGISTRAR_GASTO":
        financa = await registrar_conforme_integracao(texto, usuario_id, db)
        tipo_resp = "card_transacao"
        conteudo_resp = f"Gasto registrado: {financa.descricao} - R$ {financa.valor:.2f}"
        extras_resp = {"id": financa.id, "numero_usuario": financa.numero_usuario, "valor": financa.valor,
                        "categoria": financa.categoria, "descricao": financa.descricao, "tipo": financa.tipo, "data": financa.data.strftime("%Y-%m-%d"), "origem": financa.origem}

    elif intencao == "CONSULTAR_SALDO":
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

        tipo_resp = "card_saldo"
        conteudo_resp = f"Seu saldo atual é R${usuario.saldo:.2f}"
        extras_resp = {"saldo": usuario.saldo}

    elif intencao == "ATUALIZAR_SALDO":
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if analise.get("valor") is not None:
            usuario.saldo = float(analise["valor"])
            db.commit()

        tipo_resp = "card_saldo"
        conteudo_resp = f"Saldo atualizado para R$ {usuario.saldo:.2f}"
        extras_resp = {"saldo": usuario.saldo}

    elif intencao == "RESUMO_MES":
        mes = int(analise.get("mes") or date.today().month)
        ano = int(analise.get("ano") or date.today().year)

        dados_resumo  = resumo(mes=mes, ano=ano, usuario_id=usuario_id, db=db)

        tipo_resp="card_resumo"
        conteudo_resp = f"Resumo de {mes:02d}/{ano} - Total gasto: R$ {dados_resumo["gasto_total"]:.2f}"
        extras_resp = dados_resumo

    elif intencao in {"LISTAR_RECENTES", "LISTAR_MES"}:
        consulta = db.query(Financa).filter(Financa.usuario_id == usuario_id)
        if intencao == "LISTAR_MES":
            mes = int(analise.get("mes") or date.today().month)
            ano = int(analise.get("ano") or date.today().year)
            consulta = consulta.filter(
                extract("month", Financa.data) == mes,
                extract("year", Financa.data) == ano,
            )

        itens = consulta.order_by(Financa.data.desc(), Financa.id.desc()).limit(20).all()

        tipo_resp = "card_lista"
        conteudo_resp = f"Encontrei {len(itens)} lançamentos. " if itens else "Nenhuma transação encontrada"
        extras_resp = {"itens": [{"id": i.id, "numero_usuario": i.numero_usuario, "valor": i.valor, "categoria": 
                    i.categoria, "descricao": i.descricao, "tipo": i.tipo, "data": i.data.strftime("%Y-%m-%d")} for i in itens]}

    else:
        tipo_resp = "texto"
        conteudo_resp=analise.get("resposta_curta") or "Envie um gasto (ex: Almoço 35) ou consulte seu saldo e resumo do mês"
        extras_resp = None

    msg_assistente = MensagemChat(
        usuario_id = usuario_id,
        remetente = "assistente",
        tipo = tipo_resp,
        conteudo = conteudo_resp,
        dados_extras = extras_resp
    ) 

    db.add(msg_assistente)
    db.commit()
    db.refresh(msg_assistente)

    return (msg_usuario, msg_assistente)





