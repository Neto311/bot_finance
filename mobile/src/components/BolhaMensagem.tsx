import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import {
  DadosResumoCard,
  DadosTransacaoCard,
  MensagemChat,
} from "../types/api";

interface Props {
  mensagem: MensagemChat;
  onEditarTransacao: (transacao: DadosTransacaoCard) => void;
  onExcluirTransacao: (numeroUsuario: number) => void;
}

function formatarMoeda(valor: number): string {
  return Number(valor || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function formatarHora(isoString: string): string {
  try {
    const data = new Date(isoString);
    return data.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function BolhaMensagem({
  mensagem,
  onEditarTransacao,
  onExcluirTransacao,
}: Props) {
  const ehUsuario = mensagem.remetente === "usuario";
  const extras = mensagem.dados_extras || {};

  const renderizarCardTransacao = () => {
    const transacao = extras as DadosTransacaoCard;
    if (!transacao?.numero_usuario) {
      return <Text style={estilos.textoMensagem}>{mensagem.conteudo}</Text>;
    }

    const excluida = Boolean((extras as any).excluida);

    return (
      <View style={estilos.cardInterno}>
        <View style={estilos.cabecalhoCard}>
          <View style={estilos.badgeCategoria}>
            <Ionicons name="pricetag-outline" size={13} color="#10b981" />
            <Text style={estilos.textoBadgeCategoria}>
              {transacao.categoria || "Outros"}
            </Text>
          </View>
          <Text style={estilos.idTransacao}>#{transacao.numero_usuario}</Text>
        </View>

        <Text
          style={[
            estilos.tituloTransacao,
            excluida && estilos.textoRiscado,
          ]}
        >
          {transacao.descricao}
        </Text>

        <Text
          style={[
            estilos.valorGasto,
            excluida && estilos.textoRiscado,
          ]}
        >
          - {formatarMoeda(transacao.valor)}
        </Text>

        <View style={estilos.metaLinha}>
          <Text style={estilos.metaTexto}>📅 {transacao.data}</Text>
          {transacao.origem ? (
            <Text style={estilos.metaTexto}>
              • {transacao.origem === "minhas_economias" ? "Minhas Economias" : "Local"}
            </Text>
          ) : null}
        </View>

        {excluida ? (
          <Text style={estilos.avisoExcluida}>🗑️ Lançamento excluído</Text>
        ) : (
          <View style={estilos.acoesCard}>
            <Pressable
              style={estilos.botaoAcaoCard}
              onPress={() => onEditarTransacao(transacao)}
            >
              <Ionicons name="create-outline" size={15} color="#cbd5e1" />
              <Text style={estilos.textoBotaoAcao}>Editar</Text>
            </Pressable>

            <Pressable
              style={[estilos.botaoAcaoCard, estilos.botaoExcluirCard]}
              onPress={() => onExcluirTransacao(transacao.numero_usuario)}
            >
              <Ionicons name="trash-outline" size={15} color="#fca5a5" />
              <Text style={[estilos.textoBotaoAcao, { color: "#fca5a5" }]}>
                Excluir
              </Text>
            </Pressable>
          </View>
        )}
      </View>
    );
  };

  const renderizarCardSaldo = () => {
    const saldo = Number(extras.saldo ?? 0);
    return (
      <View style={estilos.cardInterno}>
        <View style={estilos.cabecalhoCard}>
          <Ionicons name="wallet-outline" size={18} color="#10b981" />
          <Text style={estilos.tituloSecaoCard}>Saldo Disponível</Text>
        </View>
        <Text style={estilos.valorSaldo}>{formatarMoeda(saldo)}</Text>
        <Text style={estilos.dicaSecundaria}>
          Para alterar, envie por exemplo: "Meu saldo agora é 2500"
        </Text>
      </View>
    );
  };

  const renderizarCardResumo = () => {
    const resumo = extras as DadosResumoCard;
    const categorias = Object.entries(resumo.total_por_categoria || {});
    const total = Number(resumo.gasto_total || 0);

    return (
      <View style={estilos.cardInterno}>
        <View style={estilos.cabecalhoCard}>
          <Ionicons name="pie-chart-outline" size={18} color="#10b981" />
          <Text style={estilos.tituloSecaoCard}>
            Resumo de {resumo.mes || "Mês Atual"}
          </Text>
        </View>

        <Text style={estilos.valorGasto}>{formatarMoeda(total)}</Text>

        {categorias.length > 0 ? (
          <View style={estilos.listaCategorias}>
            {categorias.map(([cat, valorCat]) => {
              const percentual =
                total > 0 ? Math.min(100, Math.round((valorCat / total) * 100)) : 0;
              return (
                <View key={cat} style={estilos.itemCategoria}>
                  <View style={estilos.linhaCategoriaTexto}>
                    <Text style={estilos.nomeCategoria}>{cat}</Text>
                    <Text style={estilos.valorCategoria}>
                      {formatarMoeda(valorCat)} ({percentual}%)
                    </Text>
                  </View>
                  <View style={estilos.barraFundo}>
                    <View
                      style={[estilos.barraPreenchida, { width: `${percentual}%` }]}
                    />
                  </View>
                </View>
              );
            })}
          </View>
        ) : (
          <Text style={estilos.dicaSecundaria}>
            Nenhum gasto registrado neste período.
          </Text>
        )}

        {resumo.categoria_vilao ? (
          <View style={estilos.boxVilao}>
            <Text style={estilos.textoVilao}>
              ⚠️ Maior gasto: <Text style={{ fontWeight: "700" }}>{resumo.categoria_vilao}</Text>
            </Text>
          </View>
        ) : null}

        {resumo.dica_ia ? (
          <View style={estilos.boxDicaIa}>
            <Text style={estilos.textoDicaIa}>💡 {resumo.dica_ia}</Text>
          </View>
        ) : null}
      </View>
    );
  };

  const renderizarCardLista = () => {
    const itens: DadosTransacaoCard[] = Array.isArray(extras.itens)
      ? extras.itens
      : [];

    return (
      <View style={estilos.cardInterno}>
        <View style={estilos.cabecalhoCard}>
          <Ionicons name="list-outline" size={18} color="#10b981" />
          <Text style={estilos.tituloSecaoCard}>{mensagem.conteudo}</Text>
        </View>

        {itens.map((item) => (
          <View key={item.id || item.numero_usuario} style={estilos.itemListaTransacao}>
            <View style={{ flex: 1 }}>
              <Text style={estilos.itemListaTitulo}>
                #{item.numero_usuario} • {item.descricao}
              </Text>
              <Text style={estilos.itemListaSub}>
                {item.categoria} • {item.data}
              </Text>
            </View>
            <View style={{ alignItems: "flex-end" }}>
              <Text style={estilos.itemListaValor}>
                - {formatarMoeda(item.valor)}
              </Text>
              <View style={estilos.itemListaBotoes}>
                <Pressable onPress={() => onEditarTransacao(item)}>
                  <Ionicons name="create-outline" size={16} color="#94a3b8" />
                </Pressable>
                <Pressable onPress={() => onExcluirTransacao(item.numero_usuario)}>
                  <Ionicons name="trash-outline" size={16} color="#f87171" />
                </Pressable>
              </View>
            </View>
          </View>
        ))}
      </View>
    );
  };

  return (
    <View
      style={[
        estilos.linhaContainer,
        ehUsuario ? estilos.linhaDireita : estilos.linhaEsquerda,
      ]}
    >
      <View
        style={[
          estilos.bolha,
          ehUsuario ? estilos.bolhaUsuario : estilos.bolhaAssistente,
        ]}
      >
        {ehUsuario && mensagem.tipo === "audio" ? (
          <View style={estilos.badgeAudio}>
            <Ionicons name="mic" size={14} color="#a7f3d0" />
            <Text style={estilos.textoBadgeAudio}>
              Áudio transcrito
              {extras.duracao_segundos ? ` (${extras.duracao_segundos}s)` : ""}
            </Text>
          </View>
        ) : null}

        {mensagem.tipo === "card_transacao" ? (
          renderizarCardTransacao()
        ) : mensagem.tipo === "card_saldo" ? (
          renderizarCardSaldo()
        ) : mensagem.tipo === "card_resumo" ? (
          renderizarCardResumo()
        ) : mensagem.tipo === "card_lista" ? (
          renderizarCardLista()
        ) : (
          <Text style={estilos.textoMensagem}>{mensagem.conteudo}</Text>
        )}

        <Text style={estilos.horario}>{formatarHora(mensagem.criado_em)}</Text>
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  linhaContainer: {
    width: "100%",
    marginVertical: 4,
    paddingHorizontal: 12,
    flexDirection: "row",
  },
  linhaDireita: {
    justifyContent: "flex-end",
  },
  linhaEsquerda: {
    justifyContent: "flex-start",
  },
  bolha: {
    maxWidth: "86%",
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  bolhaUsuario: {
    backgroundColor: "#005c4b",
    borderBottomRightRadius: 4,
  },
  bolhaAssistente: {
    backgroundColor: "#202c33",
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: "#2a3942",
  },
  badgeAudio: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginBottom: 4,
  },
  textoBadgeAudio: {
    color: "#a7f3d0",
    fontSize: 11,
    fontWeight: "600",
  },
  textoMensagem: {
    color: "#f8fafc",
    fontSize: 15,
    lineHeight: 21,
  },
  horario: {
    color: "rgba(226, 232, 240, 0.65)",
    fontSize: 11,
    alignSelf: "flex-end",
    marginTop: 4,
  },
  cardInterno: {
    minWidth: 240,
  },
  cabecalhoCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    marginBottom: 6,
  },
  badgeCategoria: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(16, 185, 129, 0.14)",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    gap: 4,
  },
  textoBadgeCategoria: {
    color: "#34d399",
    fontSize: 12,
    fontWeight: "600",
  },
  idTransacao: {
    color: "#94a3b8",
    fontSize: 12,
    fontWeight: "700",
  },
  tituloTransacao: {
    color: "#f8fafc",
    fontSize: 16,
    fontWeight: "700",
    marginTop: 2,
  },
  valorGasto: {
    color: "#f87171",
    fontSize: 20,
    fontWeight: "800",
    marginVertical: 4,
  },
  valorSaldo: {
    color: "#34d399",
    fontSize: 24,
    fontWeight: "800",
    marginVertical: 6,
  },
  textoRiscado: {
    textDecorationLine: "line-through",
    opacity: 0.5,
  },
  metaLinha: {
    flexDirection: "row",
    gap: 6,
    marginTop: 2,
  },
  metaTexto: {
    color: "#94a3b8",
    fontSize: 12,
  },
  avisoExcluida: {
    color: "#fca5a5",
    fontSize: 12,
    fontWeight: "600",
    marginTop: 8,
  },
  acoesCard: {
    flexDirection: "row",
    gap: 8,
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#2a3942",
  },
  botaoAcaoCard: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    paddingVertical: 7,
    borderRadius: 8,
    backgroundColor: "#111b21",
  },
  botaoExcluirCard: {
    backgroundColor: "rgba(239, 68, 68, 0.12)",
  },
  textoBotaoAcao: {
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: "600",
  },
  tituloSecaoCard: {
    color: "#e2e8f0",
    fontSize: 14,
    fontWeight: "700",
    flex: 1,
  },
  dicaSecundaria: {
    color: "#94a3b8",
    fontSize: 12,
    marginTop: 4,
  },
  listaCategorias: {
    marginTop: 8,
    gap: 8,
  },
  itemCategoria: {
    gap: 4,
  },
  linhaCategoriaTexto: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  nomeCategoria: {
    color: "#e2e8f0",
    fontSize: 13,
    fontWeight: "600",
  },
  valorCategoria: {
    color: "#cbd5e1",
    fontSize: 12,
  },
  barraFundo: {
    height: 6,
    backgroundColor: "#111b21",
    borderRadius: 3,
    overflow: "hidden",
  },
  barraPreenchida: {
    height: "100%",
    backgroundColor: "#10b981",
  },
  boxVilao: {
    marginTop: 10,
    padding: 8,
    borderRadius: 8,
    backgroundColor: "rgba(245, 158, 11, 0.12)",
  },
  textoVilao: {
    color: "#fcd34d",
    fontSize: 12,
  },
  boxDicaIa: {
    marginTop: 8,
    padding: 8,
    borderRadius: 8,
    backgroundColor: "rgba(16, 185, 129, 0.1)",
  },
  textoDicaIa: {
    color: "#a7f3d0",
    fontSize: 12,
    lineHeight: 17,
  },
  itemListaTransacao: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: "#2a3942",
    gap: 10,
  },
  itemListaTitulo: {
    color: "#f8fafc",
    fontSize: 13,
    fontWeight: "600",
  },
  itemListaSub: {
    color: "#94a3b8",
    fontSize: 11,
    marginTop: 2,
  },
  itemListaValor: {
    color: "#f87171",
    fontSize: 13,
    fontWeight: "700",
  },
  itemListaBotoes: {
    flexDirection: "row",
    gap: 10,
    marginTop: 4,
  },
});
