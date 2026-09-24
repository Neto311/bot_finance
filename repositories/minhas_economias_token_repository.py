from datetime import datetime, timedelta

from database import SessionLocal
from models.financas import Usuario  # noqa: F401
from models.minhas_economias_token import MinhasEconomiasToken
from services.token_crypto_service import (
    criptografar_token,
    descriptografar_token,
)


def salvar_tokens(usuario_id, access_token, refresh_token, token_type, expires_in):
    db = SessionLocal()

    try:
        expires_at = datetime.now() + timedelta(  # noqa: DTZ005
            seconds=int(expires_in))

        access_token_criptografado = criptografar_token(access_token)

        refresh_token_criptografado = (
            criptografar_token(refresh_token)
            if refresh_token else None
        )

        registro = (
            db.query(MinhasEconomiasToken).filter(MinhasEconomiasToken.usuario_id == usuario_id).first()
        )

        if registro:
            registro.access_token = access_token_criptografado
            registro.token_type = token_type
            registro.expires_at = expires_at

            if refresh_token_criptografado:
                registro.refresh_token = refresh_token_criptografado

        else:
            if not refresh_token_criptografado:
                raise ValueError("Refresh token obrigatório para um nova conexão")

            registro = MinhasEconomiasToken(
                usuario_id = usuario_id,
                access_token = access_token_criptografado,
                refresh_token = refresh_token_criptografado,
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

        access_token = descriptografar_token(busca.access_token)
        refresh_token = descriptografar_token(busca.refresh_token)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': busca.token_type,
            'expires_at': busca.expires_at
        }

    finally:
        db.close()

def excluir_tokens(usuario_id):
    db = SessionLocal()

    try:
        busca = db.query(MinhasEconomiasToken).filter(MinhasEconomiasToken.usuario_id == usuario_id).first()

        if not busca:
            return False

        db.delete(busca)
        db.commit()

        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

