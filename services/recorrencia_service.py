from calendar import monthrange
from datetime import date, datetime
from sqlalchemy.orm import Session

from models import financas as model


def _competencia(ref: date) -> str:
    return f"{ref.year:04d}-{ref.month:02d}"


def _data_vencimento_no_mes(ano: int, mes: int, dia_vencimento: int) -> datetime:
    ultimo_dia = monthrange(ano, mes)[1]
    dia = min(max(dia_vencimento, 1), ultimo_dia)
    return datetime(ano, mes, dia, 12, 0, 0)


def processar_recorrencias_pendentes(db: Session, usuario_id: int) -> list[model.Financa]:
    hoje = date.today()
    comp_atual = _competencia(hoje)

    pendentes = (
        db.query(model.Recorrencia)
        .filter(
            model.Recorrencia.usuario_id == usuario_id,
            model.Recorrencia.ativa.is_(True),
            (model.Recorrencia.ultima_competencia.is_(None))
            | (model.Recorrencia.ultima_competencia != comp_atual),
            model.Recorrencia.dia_vencimento <= hoje.day,
        )
        .all()
    )

    if not pendentes:
        return []

    usuario = (
        db.query(model.Usuario)
        .filter(model.Usuario.id == usuario_id)
        .with_for_update()
        .first()
    )
    if not usuario:
        return []

    criadas: list[model.Financa] = []
    for rec in pendentes:
        numero_usuario = usuario.proximo_numero_transacao
        usuario.proximo_numero_transacao += 1

        nova = model.Financa(
            usuario_id=usuario_id,
            valor=rec.valor,
            categoria=rec.categoria,
            descricao=rec.descricao,
            tipo=rec.tipo,
            data=_data_vencimento_no_mes(hoje.year, hoje.month, rec.dia_vencimento),
            numero_usuario=numero_usuario,
            origem="local",
            recorrencia_id=rec.id,
        )
        db.add(nova)

        if rec.tipo == "GANHO":
            usuario.saldo += rec.valor
        else:
            usuario.saldo -= rec.valor

        rec.ultima_competencia = comp_atual
        criadas.append(nova)

    db.commit()
    return criadas


def criar_recorrencia(db: Session, usuario_id: int, dados: dict) -> tuple[model.Recorrencia, bool]:
    dia = int(dados.get("dia_vencimento") or date.today().day)
    dia = min(max(dia, 1), 31)

    rec = model.Recorrencia(
        usuario_id=usuario_id,
        valor=float(dados["valor"]),
        categoria=dados.get("categoria") or "Outros",
        descricao=dados.get("descricao") or "Assinatura",
        tipo=dados.get("tipo") or "GASTO",
        dia_vencimento=dia,
        ativa=True,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    criadas = processar_recorrencias_pendentes(db, usuario_id)
    lancou_este_mes = any(c.recorrencia_id == rec.id for c in criadas)
    return rec, lancou_este_mes