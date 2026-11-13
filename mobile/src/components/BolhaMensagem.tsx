import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import {
  DadosResumoCard,
  DadosTransacaoCard,
  MensagemChat,
} from "../types/api";
import { CORES, iconePorCategoria } from "../theme/colors";

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

export function BolhaMensagem({
  mensagem,
  onEditarTransacao,
  onExcluirTransacao,
}: Props) {
  const ehUsuario = mensagem.remetente === "usuario";
  const extras = mensagem.dados_extras || {};

  // Mensagem simples do usuário (estilo Instagram DM)
  if (ehUsuario) {
    return (
      <View style={[estilos.linha, estilos.linhaDireita]}>
        <View style={estilos.bolhaUsuario}>
          {mensagem.tipo === "audio" ? (
            <View style={estilos.tagAudio}>
              <Ionicons name="mic" size={13} color="#04131E" />
              <Text style={estilos.textoTagAudio}>
                Voz{extras.duracao_segundos ? ` • ${extras.duracao_segundos}s` : ""}
              </Text>
            </View>
          ) : null}
          <Text style={estilos.textoUsuario}>{mensagem.conteudo}</Text>
        </View>
      </View>
    );
  }

  // Card de Transação minimalista (estilo Apple Pay / Revolut)
  if (mensagem.tipo === "card_transacao" && extras.numero_usuario) {
    const transacao = extras as DadosTransacaoCard;
    const excluida = Boolean((extras as any).excluida);
    const ehGanho = transacao.tipo === "GANHO";

    return (
      <View style={[estilos.linha, estilos.linhaEsquerda]}>
        <View style={estilos.cardRecibo}>
          <View style={estilos.topoRecibo}>
            <View style={estilos.circuloIcone}>
              <Ionicons
                name={
                  ehGanho
                    ? "trending-up"
                    : (iconePorCategoria(transacao.categoria) as any)
                }
                size={18}
                color={CORES.verde}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text
                style={[
                  estilos.tituloRecibo,
                  excluida && estilos.textoRiscado,
                ]}
              >
                {transacao.descricao}
              </Text>
              <Text style={estilos.subRecibo}>
                {ehGanho ? "Entrada" : transacao.categoria} • {transacao.data}
              </Text>
            </View>
            <Text
              style={[
                estilos.valorRecibo,
                ehGanho && { color: CORES.verde },
                excluida && estilos.textoRiscado,
              ]}
            >
              {ehGanho ? "+" : "-"}
              {formatarMoeda(transacao.valor)}
            </Text>
          </View>

          {excluida ? (
            <Text style={estilos.textoRemovido}>Removido</Text>
          ) : (
            <View style={estilos.rodapeRecibo}>
              <Pressable
                onPress={() => onEditarTransacao(transacao)}
                hitSlop={8}
              >
                <Text style={estilos.linkRecibo}>Editar</Text>
              </Pressable>
              <Text style={estilos.pontoSeparador}>•</Text>
              <Pressable
                onPress={() => onExcluirTransacao(transacao.numero_usuario)}
                hitSlop={8}
              >
                <Text style={[estilos.linkRecibo, { color: CORES.perigo }]}>
                  Excluir
                </Text>
              </Pressable>
            </View>
          )}
        </View>
      </View>
    );
  }

  // Card de Saldo minimalista
  if (mensagem.tipo === "card_saldo") {
    const saldo = Number(extras.saldo ?? 0);
    return (
      <View style={[estilos.linha, estilos.linhaEsquerda]}>
        <View style={estilos.cardRecibo}>
          <Text style={estilos.labelPequena}>SALDO DISPONÍVEL</Text>
          <Text style={estilos.valorGrandeSaldo}>{formatarMoeda(saldo)}</Text>
        </View>
      </View>
    );
  }

  // Card de Resumo Mensal
  if (mensagem.tipo === "card_resumo") {
    const resumo = extras as DadosResumoCard & {
      categorias?: Record<string, number>;
      ganho_total?: number;
    };
    const mapa = resumo.categorias || resumo.total_por_categoria || {};
    const categorias = Object.entries(mapa);
    const total = Number(resumo.gasto_total || 0);
    const ganhoTotal = Number(resumo.ganho_total || 0);

    return (
      <View style={[estilos.linha, estilos.linhaEsquerda]}>
        <View style={estilos.cardRecibo}>
          <Text style={estilos.labelPequena}>GASTOS NO MÊS</Text>
          <Text style={estilos.valorGrandeGasto}>{formatarMoeda(total)}</Text>
          {ganhoTotal > 0 ? (
            <Text style={estilos.subResumoGanho}>
              Entradas:{" "}
              <Text style={{ color: CORES.verde, fontWeight: "700" }}>
                +{formatarMoeda(ganhoTotal)}
              </Text>
            </Text>
          ) : null}

          {categorias.length > 0 ? (
            <View style={{ marginTop: 12, gap: 10 }}>
              {categorias.map(([cat, valorCat]) => {
                const pct =
                  total > 0
                    ? Math.min(100, Math.round((valorCat / total) * 100))
                    : 0;
                return (
                  <View key={cat} style={{ gap: 4 }}>
                    <View style={estilos.linhaCatResumo}>
                      <Text style={estilos.nomeCat}>{cat}</Text>
                      <Text style={estilos.valorCat}>
                        {formatarMoeda(valorCat)}
                      </Text>
                    </View>
                    <View style={estilos.trilho}>
                      <View
                        style={[estilos.barra, { width: `${pct}%` }]}
                      />
                    </View>
                  </View>
                );
              })}
            </View>
          ) : null}
        </View>
      </View>
    );
  }

  // Card de Lista de Lançamentos
  if (mensagem.tipo === "card_lista") {
    const itens: DadosTransacaoCard[] = Array.isArray(extras.itens)
      ? extras.itens
      : [];

    return (
      <View style={[estilos.linha, estilos.linhaEsquerda]}>
        <View style={estilos.cardRecibo}>
          <Text style={estilos.labelPequena}>{mensagem.conteudo}</Text>
          {itens.map((item) => (
            <Pressable
              key={item.id || item.numero_usuario}
              style={estilos.itemLista}
              onPress={() => onEditarTransacao(item)}
            >
              <View style={{ flex: 1 }}>
                <Text style={estilos.tituloRecibo}>{item.descricao}</Text>
                <Text style={estilos.subRecibo}>
                  {item.categoria} • {item.data}
                </Text>
              </View>
              <Text
                style={[
                  estilos.valorRecibo,
                  item.tipo === "GANHO" && { color: CORES.verde },
                ]}
              >
                {item.tipo === "GANHO" ? "+" : "-"}
                {formatarMoeda(item.valor)}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>
    );
  }

  // Mensagem de texto do assistente
  return (
    <View style={[estilos.linha, estilos.linhaEsquerda]}>
      <View style={estilos.bolhaAssistente}>
        <Text style={estilos.textoAssistente}>{mensagem.conteudo}</Text>
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  linha: {
    width: "100%",
    paddingHorizontal: 16,
    marginVertical: 4,
    flexDirection: "row",
  },
  linhaDireita: {
    justifyContent: "flex-end",
  },
  linhaEsquerda: {
    justifyContent: "flex-start",
  },
  bolhaUsuario: {
    maxWidth: "78%",
    backgroundColor: CORES.verde,
    borderRadius: 22,
    borderBottomRightRadius: 6,
    paddingHorizontal: 16,
    paddingVertical: 11,
  },
  tagAudio: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginBottom: 2,
  },
  textoTagAudio: {
    color: "#04131E",
    fontSize: 11,
    fontWeight: "700",
    opacity: 0.75,
  },
  textoUsuario: {
    color: "#04131E",
    fontSize: 15,
    fontWeight: "600",
    lineHeight: 20,
  },
  bolhaAssistente: {
    maxWidth: "80%",
    backgroundColor: CORES.fundoElevado,
    borderRadius: 22,
    borderBottomLeftRadius: 6,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  textoAssistente: {
    color: CORES.textoPrincipal,
    fontSize: 15,
    lineHeight: 21,
  },
  cardRecibo: {
    width: 280,
    backgroundColor: CORES.fundoElevado,
    borderRadius: 20,
    padding: 16,
  },
  topoRecibo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  circuloIcone: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: CORES.superficie,
    alignItems: "center",
    justifyContent: "center",
  },
  tituloRecibo: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
  subRecibo: {
    color: CORES.textoSecundario,
    fontSize: 12,
    marginTop: 2,
  },
  valorRecibo: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
  textoRiscado: {
    textDecorationLine: "line-through",
    opacity: 0.4,
  },
  rodapeRecibo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 0.5,
    borderTopColor: CORES.divisor,
  },
  linkRecibo: {
    color: CORES.textoSecundario,
    fontSize: 12,
    fontWeight: "600",
  },
  pontoSeparador: {
    color: CORES.textoSuave,
    fontSize: 12,
  },
  textoRemovido: {
    color: CORES.perigo,
    fontSize: 12,
    marginTop: 10,
  },
  labelPequena: {
    color: CORES.textoSecundario,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  valorGrandeSaldo: {
    color: CORES.verde,
    fontSize: 26,
    fontWeight: "800",
    marginTop: 4,
  },
  valorGrandeGasto: {
    color: "#FFFFFF",
    fontSize: 24,
    fontWeight: "800",
    marginTop: 4,
  },
  subResumoGanho: {
    color: CORES.textoSecundario,
    fontSize: 13,
    marginTop: 4,
  },
  linhaCatResumo: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  nomeCat: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  valorCat: {
    color: CORES.textoSecundario,
    fontSize: 13,
  },
  trilho: {
    height: 4,
    backgroundColor: CORES.superficie,
    borderRadius: 2,
    overflow: "hidden",
  },
  barra: {
    height: "100%",
    backgroundColor: CORES.dourado,
  },
  itemLista: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderTopWidth: 0.5,
    borderTopColor: CORES.divisor,
    marginTop: 6,
  },
});
