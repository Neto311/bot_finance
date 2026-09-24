from database import SessionLocal
from models.financas import Usuario
from models.integracao_usuario import IntegracaoUsuario


def buscar_integracao_principal(usuario_id):
    db = SessionLocal()

    try:
        resultado = db.query(IntegracaoUsuario).filter(IntegracaoUsuario.usuario_id==usuario_id, IntegracaoUsuario.principal.is_(True), IntegracaoUsuario.ativo.is_(True)).first()

        return resultado.provedor if resultado else None
    
    finally:
        db.close()

def selecionar_integracao_principal(usuario_id: int, provedor: str):
    db = SessionLocal()

    try:
        provedor = provedor.strip().lower()
        if provedor not in {"local", "minhas_economias"}:
            raise ValueError("Provedor Inválido")
        
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.ativo.is_(True)).with_for_update().first()

        if not usuario:
            raise ValueError ("Usuário não encontrado ou desativado")


        integracoes = db.query(IntegracaoUsuario).filter(IntegracaoUsuario.usuario_id == usuario_id).all()

        for integracao in integracoes:
            integracao.principal = False

        db.flush()

        integracao_escolhida = None

        for integracao in integracoes:
            if integracao.provedor == provedor:
                integracao_escolhida = integracao
                break

        if not integracao_escolhida:
            integracao_escolhida = IntegracaoUsuario(usuario_id=usuario_id, provedor=provedor, ativo=True, principal=True)
            db.add(integracao_escolhida)
        else:
            integracao_escolhida.ativo = True
            integracao_escolhida.principal = True

        db.commit()

        return provedor

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
    