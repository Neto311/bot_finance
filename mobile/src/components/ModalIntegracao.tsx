import React, { useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { apiFinancas } from "../services/api";

interface Props {
  visivel: boolean;
  provedorAtual: string | null;
  onFechar: () => void;
  onAtualizado: () => Promise<void>;
}

export function ModalIntegracao({
  visivel,
  provedorAtual,
  onFechar,
  onAtualizado,
}: Props) {
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const selecionar = async (provedor: "local" | "minhas_economias") => {
    setSalvando(true);
    setErro(null);
    try {
      await apiFinancas.selecionarIntegracao(provedor);
      await onAtualizado();
      onFechar();
    } catch (e: any) {
      setErro(e?.message || "Não foi possível alterar a integração.");
    } finally {
      setSalvando(false);
    }
  };

  const ativo = provedorAtual || "local";

  return (
    <Modal visible={visivel} transparent animationType="fade">
      <View style={estilos.overlay}>
        <View style={estilos.modalCard}>
          <Text style={estilos.titulo}>Modo de Armazenamento</Text>
          <Text style={estilos.subtitulo}>
            Escolha onde seus novos gastos serão registrados por padrão:
          </Text>

          {erro ? <Text style={estilos.erro}>{erro}</Text> : null}

          <Pressable
            style={[
              estilos.opcaoCard,
              ativo === "local" && estilos.opcaoSelecionada,
            ]}
            onPress={() => selecionar("local")}
            disabled={salvando}
          >
            <Ionicons
              name="phone-portrait-outline"
              size={24}
              color={ativo === "local" ? "#10b981" : "#94a3b8"}
            />
            <View style={{ flex: 1 }}>
              <Text style={estilos.opcaoTitulo}>Armazenamento Local (Padrão)</Text>
              <Text style={estilos.opcaoDesc}>
                Rápido e direto no banco de dados do Bot Finança.
              </Text>
            </View>
            {ativo === "local" ? (
              <Ionicons name="checkmark-circle" size={22} color="#10b981" />
            ) : null}
          </Pressable>

          <Pressable
            style={[
              estilos.opcaoCard,
              ativo === "minhas_economias" && estilos.opcaoSelecionada,
            ]}
            onPress={() => selecionar("minhas_economias")}
            disabled={salvando}
          >
            <Ionicons
              name="cloud-done-outline"
              size={24}
              color={ativo === "minhas_economias" ? "#10b981" : "#94a3b8"}
            />
            <View style={{ flex: 1 }}>
              <Text style={estilos.opcaoTitulo}>Minhas Economias</Text>
              <Text style={estilos.opcaoDesc}>
                Sincroniza automaticamente seus gastos com sua conta Minhas Economias.
              </Text>
            </View>
            {ativo === "minhas_economias" ? (
              <Ionicons name="checkmark-circle" size={22} color="#10b981" />
            ) : null}
          </Pressable>

          {salvando ? (
            <ActivityIndicator
              color="#10b981"
              style={{ marginVertical: 10 }}
            />
          ) : null}

          <Pressable style={estilos.botaoFechar} onPress={onFechar}>
            <Text style={estilos.textoFechar}>Fechar</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const estilos = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.65)",
    justifyContent: "center",
    padding: 20,
  },
  modalCard: {
    backgroundColor: "#111b21",
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: "#2a3942",
    maxWidth: 440,
    width: "100%",
    alignSelf: "center",
  },
  titulo: {
    color: "#f8fafc",
    fontSize: 18,
    fontWeight: "700",
  },
  subtitulo: {
    color: "#94a3b8",
    fontSize: 13,
    marginTop: 4,
    marginBottom: 14,
  },
  erro: {
    color: "#fca5a5",
    fontSize: 13,
    marginBottom: 10,
  },
  opcaoCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: 12,
    backgroundColor: "#202c33",
    borderWidth: 1,
    borderColor: "#2a3942",
    marginBottom: 10,
  },
  opcaoSelecionada: {
    borderColor: "#10b981",
    backgroundColor: "rgba(16, 185, 129, 0.1)",
  },
  opcaoTitulo: {
    color: "#f8fafc",
    fontSize: 14,
    fontWeight: "700",
  },
  opcaoDesc: {
    color: "#94a3b8",
    fontSize: 12,
    marginTop: 2,
  },
  botaoFechar: {
    marginTop: 8,
    paddingVertical: 11,
    borderRadius: 10,
    backgroundColor: "#202c33",
    alignItems: "center",
  },
  textoFechar: {
    color: "#cbd5e1",
    fontWeight: "600",
  },
});
