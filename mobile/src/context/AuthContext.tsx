import React, { createContext, useContext, useEffect, useState } from "react";
import { UsuarioAuth } from "../types/api";
import { apiAuth } from "../services/api";
import { limparTokens, obterAccessToken, salvarTokens } from "../services/storage";

interface ContextoAuthProps {
  usuario: UsuarioAuth | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<void>;
  registrar: (nome: string, email: string, senha: string) => Promise<void>;
  entrarComGoogle: (idToken: string) => Promise<void>;
  sair: () => Promise<void>;
  recarregarUsuario: () => Promise<void>;
}

const AuthContext = createContext<ContextoAuthProps>({} as ContextoAuthProps);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioAuth | null>(null);
  const [carregando, setCarregando] = useState(true);

  const recarregarUsuario = async () => {
    try {
      const token = await obterAccessToken();
      if (!token) {
        setUsuario(null);
        return;
      }
      const perfil = await apiAuth.obterPerfil();
      setUsuario(perfil);
    } catch {
      await limparTokens();
      setUsuario(null);
    }
  };

  useEffect(() => {
    recarregarUsuario().finally(() => setCarregando(false));
  }, []);

  const entrar = async (email: string, senha: string) => {
    const resp = await apiAuth.login(email.trim(), senha);
    await salvarTokens(resp.access_token, resp.refresh_token);
    setUsuario(resp.usuario);
  };

  const registrar = async (nome: string, email: string, senha: string) => {
    const resp = await apiAuth.registrar(nome.trim(), email.trim(), senha);
    await salvarTokens(resp.access_token, resp.refresh_token);
    setUsuario(resp.usuario);
  };

  const entrarComGoogle = async (idToken: string) => {
    const resp = await apiAuth.loginGoogle(idToken);
    await salvarTokens(resp.access_token, resp.refresh_token);
    setUsuario(resp.usuario);
  };

  const sair = async () => {
    await limparTokens();
    setUsuario(null);
  };

  return (
    <AuthContext.Provider
      value={{
        usuario,
        carregando,
        entrar,
        registrar,
        entrarComGoogle,
        sair,
        recarregarUsuario,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
