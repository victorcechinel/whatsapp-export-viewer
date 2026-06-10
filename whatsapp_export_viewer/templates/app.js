let messages = [], summary = {}, translations = {}, filtered = [], rendered = 0, lastDate = "", view = "chat", mediaKind = "";
let selectedParticipant = "";
const pageSize = 140;
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[char]));
const fallbackTranslations = {
  viewer_chat: "Conversation",
  viewer_messages: "messages",
  viewer_images: "images",
  viewer_videos: "videos",
  viewer_audios: "audio",
  viewer_documents: "documents",
  viewer_download_original: "Download original",
  viewer_download_video: "Download video",
  viewer_download_audio: "Download original audio",
  viewer_open_pdf: "Open PDF",
  viewer_no_items: "No items found in this category.",
  viewer_error_loading: "Error loading data: {message}",
  viewer_at: "at",
  viewer_system: "System",
  viewer_enlarged_image: "Enlarged image",
};
const t = (key, values = {}) => String((translations && translations[key]) || fallbackTranslations[key] || key).replace(/\{(\w+)\}/g, (_match, name) => values[name] ?? "");

async function load() {
  if (window.WHATSAPP_EXPORT_DATA) {
    messages = window.WHATSAPP_EXPORT_DATA.messages || [];
    summary = window.WHATSAPP_EXPORT_DATA.summary || {};
    translations = window.WHATSAPP_EXPORT_DATA.translations || {};
  } else {
    [messages, summary, translations] = await Promise.all([
      fetch("data/messages.json").then((response) => response.json()),
      fetch("data/summary.json").then((response) => response.json()),
      fetch("data/translations.json").then((response) => response.json()),
    ]);
  }
  hydrate();
  applyFilters();
}

function hydrate() {
  $("#total").textContent = summary.total_messages || 0;
  $("#images").textContent = summary.media?.images || 0;
  $("#videos").textContent = summary.media?.videos || 0;
  $("#audios").textContent = summary.media?.audios || 0;
  $("#docs").textContent = summary.media?.documents || 0;
  $("#participantOptions").innerHTML = [
    `<button type="button" role="option" aria-selected="true" data-participant="">${esc(t("viewer_all_participants"))}</button>`,
    ...Object.keys(summary.participants || {}).map((name) => `<button type="button" role="option" aria-selected="false" data-participant="${esc(name)}">${esc(name)}</button>`),
  ].join("");
  $("#participants").innerHTML = Object.entries(summary.participants || {}).map(([name, count]) => `<button class="pill" data-part="${esc(name)}"><span>${esc(name)}</span><b>${count}</b></button>`).join("");
  $("#dates").innerHTML = Object.entries(summary.dates || {}).map(([date, count]) => `<button class="pill" data-date="${esc(date)}"><span>${esc(date)}</span><b>${count}</b></button>`).join("");
  setActiveMedia("");
}

function matchesQuery(message, query) {
  if (!query) return true;
  const haystack = [message.text, message.sender, ...(message.attachments || []).map((attachment) => attachment.name)].join(" ").toLowerCase();
  return haystack.includes(query);
}

function applyFilters() {
  const query = $("#search").value.trim().toLowerCase();
  filtered = messages.filter((message) => (!selectedParticipant || message.sender === selectedParticipant) && matchesQuery(message, query));
  if (view === "chat") renderChat();
  else renderMedia();
}

function setParticipant(name) {
  selectedParticipant = name || "";
  $("#participantDropdown").dataset.value = selectedParticipant;
  $("#participantButton").textContent = selectedParticipant || t("viewer_all_participants");
  document.querySelectorAll("#participantOptions [data-participant]").forEach((option) => {
    option.setAttribute("aria-selected", String(option.dataset.participant === selectedParticipant));
  });
  closeParticipantDropdown();
  applyFilters();
}

function toggleParticipantDropdown() {
  const dropdown = $("#participantDropdown");
  const open = dropdown.classList.toggle("open");
  $("#participantButton").setAttribute("aria-expanded", String(open));
}

function closeParticipantDropdown() {
  $("#participantDropdown").classList.remove("open");
  $("#participantButton").setAttribute("aria-expanded", "false");
}

function setTopbar(title, shown) {
  $("#viewTitle").textContent = title;
  $("#shown").textContent = shown;
  $("#backToChat").classList.toggle("visible", view !== "chat");
  $("#more").classList.toggle("visible", view === "chat" && rendered < filtered.length);
}

function setActiveMedia(kind) {
  document.querySelectorAll(".stats .stat").forEach((button) => {
    const active = kind ? button.dataset.kind === kind : button.dataset.view === "chat";
    button.classList.toggle("active", active);
  });
}

function showChat() {
  view = "chat";
  mediaKind = "";
  setActiveMedia("");
  applyFilters();
}

function showMediaView(kind) {
  view = "media";
  mediaKind = kind;
  setActiveMedia(kind);
  applyFilters();
}

function renderChat() {
  rendered = 0;
  lastDate = "";
  $("#messages").className = "messages";
  $("#messages").innerHTML = "";
  setTopbar(t("viewer_chat"), `${filtered.length} ${t("viewer_messages")}`);
  renderMore();
}

function renderMore() {
  if (view !== "chat") return;
  const target = Math.min(rendered + pageSize, filtered.length);
  let html = "";
  for (let index = rendered; index < target; index += 1) {
    const message = filtered[index];
    if (message.date && message.date !== lastDate) {
      html += `<div class="date-divider" id="date-${message.date.replaceAll("/", "-")}">${message.date}</div>`;
      lastDate = message.date;
    }
    html += messageHtml(message);
  }
  $("#messages").insertAdjacentHTML("beforeend", html);
  rendered = target;
  $("#more").classList.toggle("visible", rendered < filtered.length);
}

function scrollChatToBottom() {
  const main = $(".main");
  requestAnimationFrame(() => {
    main.scrollTop = main.scrollHeight;
  });
}

function renderUntilDate(date) {
  if (view === "media") {
    document.getElementById(`media-date-${date.replaceAll("/", "-")}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  let pages = 0;
  const maxPages = Math.ceil(filtered.length / pageSize);
  while (rendered < filtered.length && !document.getElementById(`date-${date.replaceAll("/", "-")}`) && pages < maxPages) {
    renderMore();
    pages += 1;
  }
}

function messageHtml(message) {
  const sender = message.sender ? `<div class="sender">${esc(message.sender)}</div>` : "";
  const text = (message.text || "").trim();
  const textHtml = text ? `<div class="text">${esc(text)}</div>` : "";
  const attachments = (message.attachments || []).map(attachmentHtml).join("");
  const only = !text && attachments;
  return `<div class="msg ${message.side || "in"}" data-id="${message.id}"><div class="bubble ${only ? "attachment-only" : ""}">${sender}${textHtml}${attachments}<div class="meta">${esc(message.time || "")}</div></div></div>`;
}

function isPdf(attachment) {
  return /\.pdf$/i.test(attachment.name || attachment.path || "");
}

function attachmentHtml(attachment) {
  if (attachment.kind === "images") return `<div class="attachment"><img loading="lazy" src="${esc(attachment.path)}" alt="${esc(attachment.name)}" data-full="${esc(attachment.path)}"><a class="download" href="${esc(attachment.original_path)}" download>${esc(t("viewer_download_original"))}</a></div>`;
  if (attachment.kind === "videos") return `<div class="attachment"><video controls preload="metadata" src="${esc(attachment.path)}"></video><a class="download" href="${esc(attachment.original_path)}" download>${esc(t("viewer_download_video"))}</a></div>`;
  if (attachment.kind === "audios") {
    const src = attachment.mp3_path || attachment.path;
    const duration = attachment.duration ? `<span class="duration">${attachment.duration}s</span>` : "";
    return `<div class="attachment"><audio controls preload="metadata" src="${esc(src)}"></audio>${duration}<a class="download" href="${esc(attachment.original_path)}" download>${esc(t("viewer_download_audio"))}</a></div>`;
  }
  const attrs = isPdf(attachment) ? `target="_blank" rel="noopener"` : `download`;
  const label = isPdf(attachment) ? esc(t("viewer_open_pdf")) : esc(attachment.name);
  return `<div class="attachment"><a class="download" href="${esc(attachment.path)}" ${attrs}>${label}</a></div>`;
}

function mediaItems() {
  const items = [];
  for (const message of filtered) {
    for (const attachment of message.attachments || []) {
      if (attachment.kind === mediaKind) items.push({ message, attachment });
    }
  }
  return items;
}

function renderMedia() {
  const items = mediaItems();
  $("#messages").className = "media-screen";
  setTopbar(t(`viewer_${mediaKind}`), `${items.length} ${t(`viewer_${mediaKind}`)}`);
  $("#more").classList.remove("visible");
  let html = "", currentDate = "";
  items.forEach((item, index) => {
    const message = item.message;
    if (message.date !== currentDate) {
      if (index > 0) html += "</div>";
      currentDate = message.date;
      html += `<section class="media-date" id="media-date-${message.date.replaceAll("/", "-")}"><div class="date-divider">${esc(message.date)}</div></section><div class="media-grid">`;
    }
    html += mediaCard(item);
  });
  if (items.length) html += "</div>";
  $("#messages").innerHTML = html || `<div class="empty">${esc(t("viewer_no_items"))}</div>`;
}

function mediaCard({ message, attachment }) {
  let preview = "";
  if (attachment.kind === "images") preview = `<button class="media-preview" type="button" data-full="${esc(attachment.path)}"><img loading="lazy" src="${esc(attachment.path)}" alt="${esc(attachment.name)}"></button>`;
  else if (attachment.kind === "videos") preview = `<video controls preload="metadata" src="${esc(attachment.path)}"></video>`;
  else if (attachment.kind === "audios") preview = `<audio controls preload="metadata" src="${esc(attachment.mp3_path || attachment.path)}"></audio>`;
  else {
    const attrs = isPdf(attachment) ? `target="_blank" rel="noopener"` : `download`;
    preview = `<a class="file-link" href="${esc(attachment.path)}" ${attrs}>${isPdf(attachment) ? esc(t("viewer_open_pdf")) : esc(attachment.name)}</a>`;
  }
  return `<article class="media-card ${esc(message.side || "in")}">${preview}<div class="media-info"><strong>${esc(message.sender || t("viewer_system"))}</strong><span>${esc(message.date)} ${esc(t("viewer_at"))} ${esc(message.time || "")}</span><span>${esc(attachment.name)}</span></div></article>`;
}

document.addEventListener("input", (event) => {
  if (event.target.matches("#search")) applyFilters();
});

document.addEventListener("click", (event) => {
  if (event.target.matches("#participantButton")) {
    toggleParticipantDropdown();
    return;
  }
  const participantOption = event.target.closest("#participantOptions [data-participant]");
  if (participantOption) {
    setParticipant(participantOption.dataset.participant);
    return;
  }
  if (!event.target.closest("#participantDropdown")) closeParticipantDropdown();

  const participant = event.target.closest("[data-part]");
  if (participant) {
    setParticipant(participant.dataset.part);
  }
  const date = event.target.closest("[data-date]");
  if (date) {
    renderUntilDate(date.dataset.date);
    const id = `${view === "media" ? "media-date-" : "date-"}${date.dataset.date.replaceAll("/", "-")}`;
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  const full = event.target.closest("[data-full]");
  if (full) {
    $("#lightboxImg").src = full.dataset.full;
    $("#lightboxImg").alt = full.querySelector("img")?.alt || full.getAttribute("aria-label") || t("viewer_enlarged_image");
    $("#lightbox").classList.add("open");
  }
  if (event.target.matches("#more")) {
    renderMore();
    scrollChatToBottom();
  }
  if (event.target.matches("#backToChat")) showChat();
  const stat = event.target.closest(".stats .stat");
  if (stat?.dataset.view === "chat") showChat();
  if (stat?.dataset.kind) showMediaView(stat.dataset.kind);
  if (event.target.matches("#closeLightbox") || event.target.matches("#lightbox")) $("#lightbox").classList.remove("open");
});

$(".main").addEventListener("scroll", (event) => {
  const element = event.currentTarget;
  if (view === "chat" && element.scrollTop + element.clientHeight > element.scrollHeight - 900) renderMore();
});

load().catch((error) => {
  $("#messages").innerHTML = `<div class="empty">${esc(t("viewer_error_loading", { message: error.message }))}</div>`;
});
