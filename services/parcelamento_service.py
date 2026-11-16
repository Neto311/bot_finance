from calendar import monthrange
from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session

from models import financas as model

def adicionar_meses(data_base: datetime, meses: int) -> datetime:
    mes_zero = (data_base.month - 1) + meses
    ano = data_base.year + mes_zero // 12
    mes = (mes_zero % 12) + 1
    ultimo_dia = monthrange(ano, mes)[1]
    dia = min(data_base.day, ultimo_dia)

    return data_base.replace(year=ano, month=mes, day=dia)

def salvar_parcelamento(
    db: Session,
    usuario_id: int,
    dados: dict,
    origem: str = "local",
) -> list[model.Financa]:
    
    parcelas_total = max(int(dados.get("parcelas_total") or 1), 1)
    valor_informado = float(dados["valor"])
    valor_eh_parcela = bool(dados.get("valor_eh_parcela", False))

    if valor_eh_parcela:
        valor_parcela = round(valor_informado, 2)
    else:
        valor_parcela = round(valor_informado / parcelas_total, 2)

    usuario = (
        db.query(model.Usuario)
        .filter(model.Usuario.id == usuario_id)
        .with_for_update()
        .first()

    )
    if not usuario:
        raise ValueError("Usuário não encontrado")
    
    grupo_id = str(uuid4())
    data_inicial = dados["data"]

    if isinstance(data_inicial, str):
        data_inicial = datetime.strptime(data_inicial, "%Y-%m-%d")

    parcelas_criadas: list[model.Financa] = []

    for i in range(1, parcelas_total + 1):
        numero_usuario = usuario.proximo_numero_transacao
        usuario.proximo_numero_transacao += 1
        nova = model.Financa(
            usuario_id=usuario_id,
            valor=valor_parcela,
            categoria=dados["categoria"],
            descricao=f"{dados['descricao']} ({i}/{parcelas_total})",
            tipo=dados["tipo"],
            data=adicionar_meses(data_inicial, i - 1),
            numero_usuario=numero_usuario,
            origem=origem,
            grupo_parcelamento_id=grupo_id,
            parcela_atual=i,
            parcela_total=parcelas_total,
        )
        db.add(nova)
        parcelas_criadas.append(nova)

    if dados["tipo"] == "GANHO":
        usuario.saldo += valor_parcela
    else:
        usuario.saldo -= valor_parcela

    db.commit()

    for p in parcelas_criadas:
        db.refresh(p)

    return parcelas_criadas