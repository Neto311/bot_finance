import React, { createContext, useContext, useEffect, useState } from "react";
import { Platform } from "react-native";
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
    const inicializarAuth = async () => {
      if (Platform.OS === "web" && typeof window !== "undefined" && window.location.hash) {
        const params = new URLSearchParams(window.location.hash.slice(1));
        const idTokenGoogle = params.get("id_token");
        if (idTokenGoogle) {
          window.history.replaceState(null, "", window.location.pathname + window.location.search);
          try {
            await entrarComGoogle(idTokenGoogle);
            return;
          } catch {
            // Se falhar o login Google, segue para verificação normal de token
          }
        }
      }
      await recarregarUsuario();
    };

    inicializarAuth().finally(() => setCarregando(false));
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
