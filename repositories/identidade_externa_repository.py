from database import SessionLocal
from models.financas import Usuario, IdentidadeExterna


def buscar_usuario_id_por_identidade(provedor, identificador_externo):
    db = SessionLocal()

    try:
        if not provedor or not identificador_externo:
            return None
        provedor_normalizado = str(provedor).lower().strip()
        identificador_normalizado = str(identificador_externo).strip()


        usuario = (db.query(Usuario).join(IdentidadeExterna, IdentidadeExterna.usuario_id==Usuario.id).filter(IdentidadeExterna.provedor==provedor_normalizado, IdentidadeExterna.identificador_externo==identificador_normalizado, Usuario.ativo.is_(True)).first())

        if not usuario:
            return None

        return usuario.id

    finally:
        db.close()