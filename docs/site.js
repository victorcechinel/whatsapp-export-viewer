const translations = {
  en: {
    nav_downloads: "Downloads",
    nav_how: "How to use",
    nav_privacy: "Privacy",
    language: "Language",
    eyebrow: "Private WhatsApp archive for every desktop",
    headline: "Convert WhatsApp chat exports into beautiful offline HTML",
    subheadline: "Open a WhatsApp ZIP export, keep messages and media on your computer, and generate a searchable website that works on Windows, macOS, and Linux.",
    download_latest: "Download latest release",
    view_github: "View on GitHub",
    preview_gallery: "Media gallery",
    downloads_eyebrow: "Downloads",
    downloads_title: "Install or run it on your platform",
    downloads_text: "Use the desktop app when you do not want the terminal, or use the command line for automation and batch exports.",
    windows_text: "Download the Windows package, extract it, and run the viewer application.",
    mac_text: "Download the Apple Silicon or Intel build, extract it, and open the app or CLI.",
    linux_text: "Download the Linux archive, make the binary executable if needed, and run it locally.",
    how_eyebrow: "How it works",
    how_title: "From WhatsApp ZIP to offline website",
    step1: "Export a WhatsApp chat with media included.",
    step2: "Open the app and select the ZIP file.",
    step3: "Choose the output folder and your participant name.",
    step4: "Generate the archive and open index.html.",
    cli_title: "CLI automation",
    privacy_eyebrow: "Privacy",
    privacy_title: "Your conversations stay on your computer",
    privacy_text: "The converter does not upload your messages, does not use a backend, and does not add tracking scripts to the generated archive.",
    offline_title: "Offline HTML",
    offline_text: "The generated folder opens directly in your browser.",
    media_title: "Media galleries",
    media_text: "Browse images, videos, audio messages, and documents by date and sender.",
    opensource_title: "Open source",
    opensource_text: "Review the code, contribute fixes, and help support more WhatsApp export formats."
  },
  "pt-BR": {
    nav_downloads: "Downloads",
    nav_how: "Como usar",
    nav_privacy: "Privacidade",
    language: "Idioma",
    eyebrow: "Arquivo privado do WhatsApp para qualquer computador",
    headline: "Converta conversas exportadas do WhatsApp em HTML offline",
    subheadline: "Abra um ZIP exportado do WhatsApp, mantenha mensagens e mídias no seu computador e gere um site pesquisável que funciona no Windows, macOS e Linux.",
    download_latest: "Baixar versão mais recente",
    view_github: "Ver no GitHub",
    preview_gallery: "Galeria de mídias",
    downloads_eyebrow: "Downloads",
    downloads_title: "Instale ou execute na sua plataforma",
    downloads_text: "Use o app desktop quando não quiser terminal, ou use a linha de comando para automação e conversões em lote.",
    windows_text: "Baixe o pacote Windows, extraia e execute o aplicativo.",
    mac_text: "Baixe a versão Apple Silicon ou Intel, extraia e abra o app ou CLI.",
    linux_text: "Baixe o arquivo Linux, marque o binário como executável se necessário e rode localmente.",
    how_eyebrow: "Como funciona",
    how_title: "Do ZIP do WhatsApp para um site offline",
    step1: "Exporte uma conversa do WhatsApp com mídias incluídas.",
    step2: "Abra o app e selecione o arquivo ZIP.",
    step3: "Escolha a pasta de saída e seu nome na conversa.",
    step4: "Gere o arquivo e abra o index.html.",
    cli_title: "Automação por CLI",
    privacy_eyebrow: "Privacidade",
    privacy_title: "Suas conversas ficam no seu computador",
    privacy_text: "O conversor não envia mensagens, não usa backend e não adiciona scripts de rastreamento ao arquivo gerado.",
    offline_title: "HTML offline",
    offline_text: "A pasta gerada abre diretamente no navegador.",
    media_title: "Galerias de mídia",
    media_text: "Navegue por imagens, vídeos, áudios e documentos por data e remetente.",
    opensource_title: "Código aberto",
    opensource_text: "Revise o código, contribua com correções e ajude a suportar mais formatos de exportação do WhatsApp."
  },
  es: {
    nav_downloads: "Descargas",
    nav_how: "Cómo usar",
    nav_privacy: "Privacidad",
    language: "Idioma",
    eyebrow: "Archivo privado de WhatsApp para cualquier escritorio",
    headline: "Convierte chats exportados de WhatsApp en HTML offline",
    subheadline: "Abre un ZIP exportado de WhatsApp, mantén mensajes y medios en tu computadora y genera un sitio buscable para Windows, macOS y Linux.",
    download_latest: "Descargar última versión",
    view_github: "Ver en GitHub",
    preview_gallery: "Galería de medios",
    downloads_eyebrow: "Descargas",
    downloads_title: "Instala o ejecútalo en tu plataforma",
    downloads_text: "Usa la app de escritorio si no quieres terminal, o la línea de comandos para automatización y lotes.",
    windows_text: "Descarga el paquete de Windows, extráelo y ejecuta la aplicación.",
    mac_text: "Descarga la versión Apple Silicon o Intel, extráela y abre la app o CLI.",
    linux_text: "Descarga el archivo de Linux, marca el binario como ejecutable si hace falta y ejecútalo localmente.",
    how_eyebrow: "Cómo funciona",
    how_title: "Del ZIP de WhatsApp a un sitio offline",
    step1: "Exporta un chat de WhatsApp con medios incluidos.",
    step2: "Abre la app y selecciona el archivo ZIP.",
    step3: "Elige la carpeta de salida y tu nombre en el chat.",
    step4: "Genera el archivo y abre index.html.",
    cli_title: "Automatización por CLI",
    privacy_eyebrow: "Privacidad",
    privacy_title: "Tus conversaciones se quedan en tu computadora",
    privacy_text: "El conversor no sube mensajes, no usa backend y no añade scripts de rastreo al archivo generado.",
    offline_title: "HTML offline",
    offline_text: "La carpeta generada abre directamente en tu navegador.",
    media_title: "Galerías de medios",
    media_text: "Explora imágenes, videos, audios y documentos por fecha y remitente.",
    opensource_title: "Código abierto",
    opensource_text: "Revisa el código, contribuye correcciones y ayuda a soportar más formatos de exportación de WhatsApp."
  }
};

function normalizeLanguage(value) {
  const lang = String(value || "").toLowerCase();
  if (lang.startsWith("pt")) return "pt-BR";
  if (lang.startsWith("es")) return "es";
  return "en";
}

function selectedLanguage() {
  const params = new URLSearchParams(window.location.search);
  return normalizeLanguage(params.get("lang") || localStorage.getItem("language") || navigator.language);
}

function applyLanguage(language) {
  const normalized = normalizeLanguage(language);
  document.documentElement.lang = normalized;
  document.querySelector("#language").value = normalized;
  localStorage.setItem("language", normalized);
  const dictionary = translations[normalized] || translations.en;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.getAttribute("data-i18n");
    element.textContent = dictionary[key] || translations.en[key] || key;
  });
}

document.querySelector("#language").addEventListener("change", (event) => {
  applyLanguage(event.target.value);
});

applyLanguage(selectedLanguage());

