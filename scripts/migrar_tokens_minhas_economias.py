from database import SessionLocal
from models.financas import Usuario  # noqa: F401
from models.minhas_economias_token import MinhasEconomiasToken
from services.token_crypto_service import criptografar_token, token_esta_criptografado


def migrar_token():
    db = SessionLocal()

    try:
        registros = db.query(MinhasEconomiasToken).all()
        quantidade_migrada = 0

        for registro in registros:
            registro_alterado = False
            if not token_esta_criptografado(registro.access_token):
                registro.access_token = criptografar_token(registro.access_token)
                registro_alterado = True

            if not token_esta_criptografado(registro.refresh_token):
                registro.refresh_token = criptografar_token(registro.refresh_token)
                registro_alterado = True

            if registro_alterado:
                quantidade_migrada += 1

        db.commit()
        print({"migrados": quantidade_migrada})

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrar_token()