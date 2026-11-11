import { Platform } from "react-native";
import Constants from "expo-constants";
import {
  limparTokens,
  obterAccessToken,
  obterRefreshToken,
  salvarTokens,
} from "./storage";
import {
  RespostaEnvioChat,
  RespostaHistoricoChat,
  RespostaTokens,
  UsuarioAuth,
} from "../types/api";

function obterUrlApiPadrao(): string {
  if (Platform.OS === "web") {
    return "http://localhost:8000";
  }
  const hostExpo = Constants.expoConfig?.hostUri?.split(":")[0];
  if (hostExpo) {
    return `http://${hostExpo}:8000`;
  }
  return Platform.OS === "android"
    ? "http://10.0.2.2:8000"
    : "http://localhost:8000";
}

export const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_URL || obterUrlApiPadrao()
).replace(/\/$/, "");

let promessaRefreshEmAndamento: Promise<string | null> | null = null;

async function tentarRenovarToken(): Promise<string | null> {
  if (promessaRefreshEmAndamento) {
    return promessaRefreshEmAndamento;
  }

  promessaRefreshEmAndamento = (async () => {
    try {
      const refreshToken = await obterRefreshToken();
      if (!refreshToken) return null;

      const resposta = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!resposta.ok) {
        await limparTokens();
        return null;
      }

      const dados: RespostaTokens = await resposta.json();
      await salvarTokens(dados.access_token, dados.refresh_token);
      return dados.access_token;
    } catch {
      return null;
    } finally {
      promessaRefreshEmAndamento = null;
    }
  })();

  return promessaRefreshEmAndamento;
}

export async function requisicaoApi<T>(
  caminho: string,
  opcoes: RequestInit = {},
  tentarRefresh = true
): Promise<T> {
  const token = await obterAccessToken();
  const headers = new Headers(opcoes.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(opcoes.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const resposta = await fetch(`${API_BASE_URL}${caminho}`, {
    ...opcoes,
    headers,
  });

  if (resposta.status === 401 && tentarRefresh && !caminho.startsWith("/auth/login")) {
    const novoToken = await tentarRenovarToken();
    if (novoToken) {
      return requisicaoApi<T>(caminho, opcoes, false);
    }
  }

  if (!resposta.ok) {
    let mensagemErro = `Erro ${resposta.status}`;
    try {
      const corpoErro = await resposta.json();
      if (corpoErro?.detail) {
        mensagemErro =
          typeof corpoErro.detail === "string"
            ? corpoErro.detail
            : JSON.stringify(corpoErro.detail);
      }
    } catch {
      // ignora erro de parse
    }
    throw new Error(mensagemErro);
  }

  return (await resposta.json()) as T;
}

export const apiAuth = {
  registrar: (nome: string, email: string, senha: string) =>
    requisicaoApi<RespostaTokens>(
      "/auth/registro",
      {
        method: "POST",
        body: JSON.stringify({ nome, email, senha }),
      },
      false
    ),

  login: (email: string, senha: string) =>
    requisicaoApi<RespostaTokens>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, senha }),
      },
      false
    ),

  loginGoogle: (idToken: string) =>
    requisicaoApi<RespostaTokens>(
      "/auth/google",
      {
        method: "POST",
        body: JSON.stringify({ id_token: idToken }),
      },
      false
    ),

  obterPerfil: () => requisicaoApi<UsuarioAuth>("/auth/me"),
};

export const apiChat = {
  listarMensagens: (cursor?: number | null, limite = 30) => {
    const params = new URLSearchParams({ limite: String(limite) });
    if (cursor) params.set("cursor", String(cursor));
    return requisicaoApi<RespostaHistoricoChat>(`/chat/mensagens?${params.toString()}`);
  },

  enviarTexto: (texto: string) =>
    requisicaoApi<RespostaEnvioChat>("/chat/texto", {
      method: "POST",
      body: JSON.stringify({ texto }),
    }),

  enviarAudio: async (uriAudio: string, duracaoSegundos?: number) => {
    const formData = new FormData();
    const extensao = uriAudio.split(".").pop() || "m4a";

    if (Platform.OS === "web") {
      const respBlob = await fetch(uriAudio);
      const blob = await respBlob.blob();
      formData.append("file", blob, `gravacao.${extensao}`);
      if (duracaoSegundos !== undefined) {
        formData.append("duracao_segundos", String(duracaoSegundos));
      }
      return requisicaoApi<RespostaEnvioChat>("/chat/audio", {
        method: "POST",
        body: formData,
      });
    }

    formData.append("file", {
      uri: uriAudio,
      name: `gravacao.${extensao}`,
      type: `audio/${extensao === "m4a" ? "mp4" : extensao}`,
    } as any);

    if (duracaoSegundos !== undefined) {
      formData.append("duracao_segundos", String(duracaoSegundos));
    }

    const enviarComXhr = async (tokenAtual: string | null) =>
      new Promise<{ status: number; texto: string }>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API_BASE_URL}/chat/audio`);
        if (tokenAtual) {
          xhr.setRequestHeader("Authorization", `Bearer ${tokenAtual}`);
        }
        xhr.onload = () =>
          resolve({ status: xhr.status, texto: xhr.responseText });
        xhr.onerror = () =>
          reject(new Error("Falha de rede ao enviar áudio"));
        xhr.send(formData);
      });

    let token = await obterAccessToken();
    let resultado = await enviarComXhr(token);

    if (resultado.status === 401) {
      const novoToken = await tentarRenovarToken();
      if (novoToken) {
        resultado = await enviarComXhr(novoToken);
      }
    }

    if (resultado.status < 200 || resultado.status >= 300) {
      let mensagemErro = `Erro ${resultado.status}`;
      try {
        const corpoErro = JSON.parse(resultado.texto);
        if (corpoErro?.detail) {
          mensagemErro =
            typeof corpoErro.detail === "string"
              ? corpoErro.detail
              : JSON.stringify(corpoErro.detail);
        }
      } catch {
        // ignora erro de parse
      }
      throw new Error(mensagemErro);
    }

    return JSON.parse(resultado.texto) as RespostaEnvioChat;
  },
};

export const apiFinancas = {
  editarTransacao: (
    numeroUsuario: number,
    dados: {
      valor: number;
      categoria: string;
      descricao: string;
      tipo: string;
      data: string;
    }
  ) =>
    requisicaoApi(`/financas/${numeroUsuario}`, {
      method: "PUT",
      body: JSON.stringify({
        texto: `${dados.descricao} ${dados.valor} (${dados.categoria})`,
      }),
    }),

  excluirTransacao: (numeroUsuario: number) =>
    requisicaoApi(`/financas/${numeroUsuario}`, {
      method: "DELETE",
    }),

  selecionarIntegracao: (provedor: "local" | "minhas_economias") =>
    requisicaoApi("/usuarios/integracao-principal", {
      method: "POST",
      body: JSON.stringify({ provedor }),
    }),
};
