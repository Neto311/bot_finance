from datetime import datetime, timedelta

from database import SessionLocal
from models.minhas_economias_token import MinhasEconomiasToken


def salvar_tokens(usuario_id, access_token, refresh_token, token_type, expires_in):
    db = SessionLocal()

    try:
        expires_at = datetime.now() + timedelta(seconds=int(expires_in))

        registro = (
            db.query(MinhasEconomiasToken).filter(MinhasEconomiasToken.usuario_id == usuario_id).first()
        )

        if registro:
            registro.access_token = access_token
            registro.token_type = token_type
            registro.expires_at = expires_at

            if refresh_token:
                registro.refresh_token = refresh_token

        else:
            registro = MinhasEconomiasToken(
                usuario_id = usuario_id,
                access_token = access_token,
                refresh_token = refresh_token,
                token_type = token_type,
                expires_at = expires_at
            )

            db.add(registro)

        db.commit()
        db.refresh(registro)
        return registro

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def buscar_tokens(usuario_id):
    db = SessionLocal()

    try:
        busca = db.query(MinhasEconomiasToken).filter(MinhasEconomiasToken.usuario_id == usuario_id).first()

        if not busca:
            return None

        return {
            'access_token': busca.access_token,
            'refresh_token': busca.refresh_token,
            'token_type': busca.token_type,
            'expires_at': busca.expires_at
        }

    finally:
        db.close()