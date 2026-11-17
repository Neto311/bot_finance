import React, { useState } from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { CORES } from "../theme/colors";

interface Props {
  visivel: boolean;
  motivo?: string | null;
  onFechar: () => void;
}

const BENEFICIOS_PRO = [
  "Mensagens ilimitadas no chat financeiro",
  "Lançamentos rápidos por voz (áudio)",
  "Consultor Financeiro IA com análise completa",
  "Assinaturas e parcelamentos sem limites",
];

export function ModalPaywall({ visivel, motivo, onFechar }: Props) {
  const [avisoCheckout, setAvisoCheckout] = useState(false);

  return (
    <Modal visible={visivel} transparent animationType="fade">
      <Pressable style={estilos.overlay} onPress={onFechar}>
        <Pressable style={estilos.sheet} onPress={(e) => e.stopPropagation()}>
          <View style={estilos.topoRow}>
            <View style={estilos.badgePro}>
              <Ionicons name="sparkles" size={14} color="#04131E" />
              <Text style={estilos.badgeProTexto}>FINACEAI PRO</Text>
            </View>
            <Pressable onPress={onFechar} hitSlop={10}>
              <Ionicons
                name="close"
                size={22}
                color={CORES.textoSecundario}
              />
            </Pressable>
          </View>

          <Text style={estilos.titulo}>Desbloqueie todo o poder da IA</Text>
          {motivo ? <Text style={estilos.motivo}>{motivo}</Text> : null}

          <View style={estilos.listaBeneficios}>
            {BENEFICIOS_PRO.map((item) => (
              <View key={item} style={estilos.beneficioRow}>
                <Ionicons
                  name="checkmark-circle"
                  size={18}
                  color={CORES.verde}
                />
                <Text style={estilos.beneficioTexto}>{item}</Text>
              </View>
            ))}
          </View>

          <View style={estilos.cardPreco}>
            <Text style={estilos.precoValor}>
              R$ 19,90<Text style={estilos.precoPeriodo}>/mês</Text>
            </Text>
            <Text style={estilos.precoSub}>
              Cancele quando quiser • Pix ou Cartão
            </Text>
          </View>

          {avisoCheckout ? (
            <Text style={estilos.avisoCheckout}>
              Integração de pagamento (Pix e Cartão) será ativada no próximo
              passo!
            </Text>
          ) : null}

          <Pressable
            style={({ pressed }) => [
              estilos.botaoAssinar,
              pressed && { opacity: 0.85 },
            ]}
            onPress={() => setAvisoCheckout(true)}
          >
            <Text style={estilos.textoBotaoAssinar}>Assinar FinaceAi Pro</Text>
          </Pressable>

          <Pressable onPress={onFechar} style={estilos.botaoDepois}>
            <Text style={estilos.textoBotaoDepois}>Continuar no plano Free</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const estilos = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.75)",
    justifyContent: "center",
    padding: 20,
  },
  sheet: {
    backgroundColor: CORES.fundoElevado,
    borderRadius: 22,
    padding: 22,
    gap: 14,
    borderWidth: 1,
    borderColor: "rgba(243, 199, 95, 0.25)",
  },
  topoRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  badgePro: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: CORES.dourado,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
  },
  badgeProTexto: {
    color: "#04131E",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  titulo: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "800",
  },
  motivo: {
    color: CORES.dourado,
    fontSize: 13,
    lineHeight: 19,
  },
  listaBeneficios: {
    gap: 10,
    marginVertical: 4,
  },
  beneficioRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  beneficioTexto: {
    color: "#FFFFFF",
    fontSize: 14,
    flex: 1,
  },
  cardPreco: {
    backgroundColor: CORES.superficie,
    borderRadius: 14,
    padding: 14,
    alignItems: "center",
  },
  precoValor: {
    color: "#FFFFFF",
    fontSize: 26,
    fontWeight: "800",
  },
  precoPeriodo: {
    fontSize: 14,
    fontWeight: "500",
    color: CORES.textoSecundario,
  },
  precoSub: {
    color: CORES.textoSecundario,
    fontSize: 12,
    marginTop: 2,
  },
  avisoCheckout: {
    color: CORES.verde,
    fontSize: 12,
    textAlign: "center",
  },
  botaoAssinar: {
    height: 48,
    borderRadius: 24,
    backgroundColor: CORES.verde,
    alignItems: "center",
    justifyContent: "center",
  },
  textoBotaoAssinar: {
    color: "#04131E",
    fontSize: 15,
    fontWeight: "800",
  },
  botaoDepois: {
    alignItems: "center",
    paddingVertical: 4,
  },
  textoBotaoDepois: {
    color: CORES.textoSecundario,
    fontSize: 13,
  },
});
