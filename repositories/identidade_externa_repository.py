from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models.financas import IdentidadeExterna, Usuario


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

def obter_ou_criar_usuario(provedor, identificador_externo, nome):
    db = SessionLocal()

    try:
        if not provedor or not identificador_externo:
            raise ValueError("Provedor e identificador externo são obrigatórios")
        
        provedor_normalizado = str(provedor).lower().strip()
        identificador_normalizado = str(identificador_externo).strip()
        nome_normalizado = str(nome).strip() or "Usuário"

        usuario = (
            db.query(Usuario)
            .join(
                IdentidadeExterna, IdentidadeExterna.usuario_id==Usuario.id
                )
            .filter(
                IdentidadeExterna.provedor==provedor_normalizado, 
                IdentidadeExterna.identificador_externo==identificador_normalizado).first())

        if not usuario:
            usuario = Usuario(
                nome = nome_normalizado,
                ativo = True,
                saldo = 0.0,
                proximo_numero_transacao = 1,
            )

            db.add(usuario)
            db.flush()

            identidade = IdentidadeExterna(
                usuario_id = usuario.id,
                provedor = provedor_normalizado,
                identificador_externo = identificador_normalizado
            )

            db.add(identidade)
            db.commit()
            return {
                "usuario_id": usuario.id,
                "nome": usuario.nome,
                "ativo": usuario.ativo,
                "criado": True,
            }

        return {
            "usuario_id": usuario.id,
            "nome": usuario.nome,
            "ativo": usuario.ativo,
            "criado": False,
        }

    except IntegrityError:
        db.rollback()

        usuario = (
            db.query(Usuario)
            .join(
                IdentidadeExterna,
                IdentidadeExterna.usuario_id == Usuario.id
            )
            .filter(
                IdentidadeExterna.provedor == provedor_normalizado,
                IdentidadeExterna.identificador_externo == identificador_normalizado
            )
            .first()
        )

        if not usuario:
            raise

        return {
            "usuario_id": usuario.id,
            "nome": usuario.nome,
            "ativo": usuario.ativo,
            "criado": False,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
    