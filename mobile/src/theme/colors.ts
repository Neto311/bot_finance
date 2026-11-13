export const CORES = {
  // Fundo profundo estilo Spotify/Netflix puxado para o Azul Petróleo da logo FinaceAi
  fundo: "#04131E",
  fundoElevado: "#081F30",
  superficie: "#0D2B42",
  superficieInput: "#10324C",

  // Cores vivas da logo FinaceAi
  verde: "#1ED760", // Verde vibrante estilo Spotify / barras da logo
  verdeEscuro: "#159E47",
  dourado: "#F3C75F", // Dourado da seta e moeda da logo

  // Tipografia limpa
  textoPrincipal: "#FFFFFF",
  textoSecundario: "#8BA3B8",
  textoSuave: "#56728A",

  // Divisores sutis (quase invisíveis, sem caixas pesadas)
  divisor: "rgba(255, 255, 255, 0.07)",
  bordaInput: "rgba(255, 255, 255, 0.1)",

  perigo: "#FF4D4D",
};

export function iconePorCategoria(categoria?: string): string {
  const nome = (categoria || "").toLowerCase();
  if (nome.includes("alimenta") || nome.includes("mercado")) {
    return "restaurant";
  }
  if (nome.includes("transporte") || nome.includes("uber")) {
    return "car";
  }
  if (nome.includes("moradia") || nome.includes("casa")) {
    return "home";
  }
  if (nome.includes("saúde") || nome.includes("saude") || nome.includes("farm")) {
    return "fitness";
  }
  if (nome.includes("lazer")) {
    return "Ticket" in {} ? "film" : "play";
  }
  if (nome.includes("educa")) {
    return "book";
  }
  return "bag-handle";
}
