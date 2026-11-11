export interface UsuarioAuth {
  id: number;
  nome: string;
  email: string;
  saldo: number;
  provedor_principal: string | null;
}

export interface RespostaTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  usuario: UsuarioAuth;
}

export interface DadosTransacaoCard {
  id: number;
  numero_usuario: number;
  valor: number;
  categoria: string;
  descricao: string;
  tipo: string;
  data: string;
  origem?: string;
}

export interface DadosResumoCard {
  mes: string;
  gasto_total: number;
  total_por_categoria: Record<string, number>;
  categoria_vilao: string | null;
  dica_ia: string;
}

export type TipoMensagemChat =
  | "texto"
  | "audio"
  | "card_transacao"
  | "card_saldo"
  | "card_resumo"
  | "card_lista";

export interface MensagemChat {
  id: number;
  remetente: "usuario" | "assistente";
  tipo: TipoMensagemChat;
  conteudo: string;
  dados_extras?: Record<string, any> | null;
  criado_em: string;
}

export interface RespostaEnvioChat {
  mensagem_usuario: MensagemChat;
  mensagem_assistente: MensagemChat;
}

export interface RespostaHistoricoChat {
  mensagens: MensagemChat[];
  tem_mais: boolean;
  proximo_cursor: number | null;
}
