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
import { CORES } from "../theme/colors";

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
      setErro(e?.message || "Erro ao alterar sincronização.");
    } finally {
      setSalvando(false);
    }
  };

  const ativo = provedorAtual || "local";

  return (
    <Modal visible={visivel} transparent animationType="slide">
      <Pressable style={estilos.overlay} onPress={onFechar}>
        <Pressable style={estilos.sheet} onPress={(e) => e.stopPropagation()}>
          <View style={estilos.barraArraste} />
          <Text style={estilos.titulo}>Sincronização</Text>

          {erro ? <Text style={estilos.erro}>{erro}</Text> : null}

          <Pressable
            style={estilos.opcaoRow}
            onPress={() => selecionar("local")}
            disabled={salvando}
          >
            <View style={{ flex: 1 }}>
              <Text style={estilos.opcaoTitulo}>Nuvem FinaceAi</Text>
              <Text style={estilos.opcaoDesc}>
                Armazenamento direto e instantâneo
              </Text>
            </View>
            {ativo === "local" ? (
              <Ionicons name="checkmark" size={22} color={CORES.verde} />
            ) : null}
          </Pressable>

          <Pressable
            style={estilos.opcaoRow}
            onPress={() => selecionar("minhas_economias")}
            disabled={salvando}
          >
            <View style={{ flex: 1 }}>
              <Text style={estilos.opcaoTitulo}>Minhas Economias</Text>
              <Text style={estilos.opcaoDesc}>
                Sincronizar com conta externa
              </Text>
            </View>
            {ativo === "minhas_economias" ? (
              <Ionicons name="checkmark" size={22} color={CORES.verde} />
            ) : null}
          </Pressable>

          {salvando ? (
            <ActivityIndicator
              color={CORES.verde}
              style={{ marginVertical: 8 }}
            />
          ) : null}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const estilos = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.65)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: CORES.fundoElevado,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
  },
  barraArraste: {
    width: 38,
    height: 4,
    borderRadius: 2,
    backgroundColor: CORES.bordaInput,
    alignSelf: "center",
    marginBottom: 16,
  },
  titulo: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
  },
  erro: {
    color: CORES.perigo,
    fontSize: 13,
    marginBottom: 10,
  },
  opcaoRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 0.5,
    borderBottomColor: CORES.divisor,
  },
  opcaoTitulo: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
  opcaoDesc: {
    color: CORES.textoSecundario,
    fontSize: 13,
    marginTop: 2,
  },
});
