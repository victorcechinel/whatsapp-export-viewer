let messages = [], summary = {}, translations = {}, filtered = [], rendered = 0, lastDate = "", view = "chat", mediaKind = "";
let selectedParticipant = "", selectedType = "all", currentResult = -1;
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
  viewer_all_types: "All types",
  viewer_type_messages: "Messages",
  viewer_type_media: "Media",
  viewer_type_events: "Events",
  viewer_type_deleted: "Deleted messages",
  viewer_type_calls: "Calls",
  viewer_type_view_once: "View once",
  viewer_call_voice: "Voice call",
  viewer_call_video: "Video call",
  viewer_call_missed: "missed",
  viewer_call_completed: "completed",
  viewer_deleted_message: "Deleted message",
  viewer_view_once_message: "View once media",
  viewer_edited: "edited",
  viewer_missing_attachment: "Attachment not found in the export: {name}",
  viewer_no_search: "Type to search messages",
  viewer_search_results: "{count} search results",
  viewer_clear_filters: "Clear filters",
  viewer_invalid_date: "Invalid date",
};
const typeOptions = [
  ["all", "viewer_all_types"],
  ["messages", "viewer_type_messages"],
  ["media", "viewer_type_media"],
  ["events", "viewer_type_events"],
  ["deleted", "viewer_type_deleted"],
  ["calls", "viewer_type_calls"],
  ["view_once", "viewer_type_view_once"],
];
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
  document.body.classList.toggle("compact", localStorage.getItem("compactMode") === "true");
  $("#compactMode").setAttribute("aria-pressed", String(document.body.classList.contains("compact")));
  $("#total").textContent = summary.total_messages || 0;
  $("#images").textContent = summary.media?.images || 0;
  $("#videos").textContent = summary.media?.videos || 0;
  $("#audios").textContent = summary.media?.audios || 0;
  $("#docs").textContent = summary.media?.documents || 0;
  $("#participantOptions").innerHTML = [
    `<button type="button" role="option" aria-selected="true" data-participant="">${esc(t("viewer_all_participants"))}</button>`,
    ...Object.keys(summary.participants || {}).map((name) => `<button type="button" role="option" aria-selected="false" data-participant="${esc(name)}">${esc(name)}</button>`),
  ].join("");
  $("#typeOptions").innerHTML = typeOptions.map(([value, label], index) => `<button type="button" role="option" aria-selected="${index === 0}" data-type="${value}">${esc(t(label))}</button>`).join("");
  $("#participants").innerHTML = Object.entries(summary.participants || {}).map(([name, count]) => `<button class="pill" data-part="${esc(name)}"><span>${esc(name)}</span><b>${count}</b></button>`).join("");
  $("#dates").innerHTML = Object.entries(summary.dates || {}).map(([date, count]) => `<button class="pill" data-date="${esc(date)}"><span>${esc(date)}</span><b>${count}</b></button>`).join("");
  setActiveMedia("");
}

function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function isEnglishLocale() {
  return String(translations.viewer_lang || "").toLowerCase().startsWith("en");
}

function parseDateInput(value, order = isEnglishLocale() ? "mdy" : "dmy") {
  const text = value.trim();
  if (!text) return null;
  const matched = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!matched) return null;
  const first = Number(matched[1]);
  const second = Number(matched[2]);
  const day = order === "mdy" ? second : first;
  const month = order === "mdy" ? first : second;
  const year = Number(matched[3]);
  const parsed = new Date(year, month - 1, day);
  if (parsed.getFullYear() !== year || parsed.getMonth() !== month - 1 || parsed.getDate() !== day) return null;
  return parsed;
}

function validateDateInputs() {
  for (const input of [$("#dateFrom"), $("#dateTo")]) {
    const invalid = input.value.trim() && !parseDateInput(input.value);
    input.classList.toggle("invalid", Boolean(invalid));
    input.title = invalid ? t("viewer_invalid_date") : "";
  }
}

function messageDay(message) {
  if (!message.date) return null;
  return parseDateInput(message.date, "dmy");
}

function matchesDateRange(message) {
  const current = messageDay(message);
  if (!current) return true;
  const from = parseDateInput($("#dateFrom").value);
  const to = parseDateInput($("#dateTo").value);
  if (from && current < from) return false;
  if (to && current > to) return false;
  return true;
}

function matchesType(message) {
  if (selectedType === "all") return true;
  if (selectedType === "messages") return message.type === "message";
  if (selectedType === "media") return (message.attachments || []).length > 0 || (message.missing_attachments || []).length > 0;
  if (selectedType === "events") return !["message", "system"].includes(message.type);
  if (selectedType === "deleted") return message.type === "deleted";
  if (selectedType === "calls") return message.type === "call";
  if (selectedType === "view_once") return message.type === "view_once";
  return true;
}

function matchesQuery(message, query) {
  if (!query) return true;
  const terms = normalizeText(query).split(/\s+/).filter(Boolean);
  const haystack = normalizeText([message.text, message.sender, message.type, ...(message.attachments || []).map((attachment) => attachment.name), ...(message.missing_attachments || [])].join(" "));
  return terms.every((term) => haystack.includes(term));
}

function applyFilters() {
  validateDateInputs();
  const query = $("#search").value.trim();
  filtered = messages.filter((message) => (
    (!selectedParticipant || message.sender === selectedParticipant) &&
    matchesType(message) &&
    matchesDateRange(message) &&
    matchesQuery(message, query)
  ));
  currentResult = -1;
  if (view === "chat") renderChat();
  else renderMedia();
  updateSearchStatus();
}

function setParticipant(name) {
  selectedParticipant = name || "";
  $("#participantDropdown").dataset.value = selectedParticipant;
  $("#participantButton").textContent = selectedParticipant || t("viewer_all_participants");
  document.querySelectorAll("#participantOptions [data-participant]").forEach((option) => {
    option.setAttribute("aria-selected", String(option.dataset.participant === selectedParticipant));
  });
  closeDropdown("participant");
  applyFilters();
}

function setType(value) {
  selectedType = value || "all";
  const selected = typeOptions.find(([optionValue]) => optionValue === selectedType);
  $("#typeDropdown").dataset.value = selectedType;
  $("#typeButton").textContent = selected ? t(selected[1]) : t("viewer_all_types");
  document.querySelectorAll("#typeOptions [data-type]").forEach((option) => {
    option.setAttribute("aria-selected", String(option.dataset.type === selectedType));
  });
  closeDropdown("type");
  applyFilters();
}

function toggleDropdown(name) {
  const dropdown = $(`#${name}Dropdown`);
  const open = dropdown.classList.toggle("open");
  $(`#${name}Button`).setAttribute("aria-expanded", String(open));
}

function closeDropdown(name) {
  $(`#${name}Dropdown`).classList.remove("open");
  $(`#${name}Button`).setAttribute("aria-expanded", "false");
}

function closeAllDropdowns() {
  closeDropdown("participant");
  closeDropdown("type");
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

function highlightText(value) {
  const query = $("#search").value.trim();
  const text = String(value ?? "");
  if (!query) return esc(text);
  const normalizedChars = [];
  const originalIndex = [];
  Array.from(text).forEach((char, index) => {
    const normalized = normalizeText(char);
    Array.from(normalized).forEach((normalizedChar) => {
      normalizedChars.push(normalizedChar);
      originalIndex.push(index);
    });
  });
  const normalizedText = normalizedChars.join("");
  const ranges = [];
  for (const term of normalizeText(query).split(/\s+/).filter(Boolean)) {
    let from = 0;
    while (from < normalizedText.length) {
      const found = normalizedText.indexOf(term, from);
      if (found === -1) break;
      ranges.push([originalIndex[found], originalIndex[found + term.length - 1] + 1]);
      from = found + term.length;
    }
  }
  if (!ranges.length) return esc(text);
  ranges.sort((a, b) => a[0] - b[0]);
  const merged = [];
  for (const range of ranges) {
    const last = merged[merged.length - 1];
    if (last && range[0] <= last[1]) last[1] = Math.max(last[1], range[1]);
    else merged.push(range);
  }
  let html = "", cursor = 0;
  for (const [start, end] of merged) {
    html += esc(text.slice(cursor, start));
    html += `<mark>${esc(text.slice(start, end))}</mark>`;
    cursor = end;
  }
  return html + esc(text.slice(cursor));
}

function updateSearchStatus() {
  const query = $("#search").value.trim();
  if (!query) {
    $("#searchStatus").textContent = t("viewer_no_search");
    return;
  }
  const count = renderedSearchResults().length || filtered.length;
  $("#searchStatus").textContent = t("viewer_search_results", { count });
}

function eventLabel(message) {
  if (message.type === "deleted") return t("viewer_deleted_message");
  if (message.type === "view_once") return t("viewer_view_once_message");
  if (message.type === "call") {
    const kind = t(message.call_kind === "video" ? "viewer_call_video" : "viewer_call_voice");
    const status = t(message.call_status === "missed" ? "viewer_call_missed" : "viewer_call_completed");
    return `${kind} · ${status}`;
  }
  return message.text || t("viewer_system");
}

function messageHtml(message) {
  const sender = message.sender ? `<div class="sender">${esc(message.sender)}</div>` : "";
  const text = (message.text || "").trim();
  const event = !["message"].includes(message.type);
  const textHtml = event ? `<div class="event-text">${esc(eventLabel(message))}</div>` : (text ? `<div class="text">${highlightText(text)}</div>` : "");
  const edited = message.edited ? `<span class="edited">${esc(t("viewer_edited"))}</span>` : "";
  const missing = (message.missing_attachments || []).map((name) => `<div class="missing">${esc(t("viewer_missing_attachment", { name }))}</div>`).join("");
  const attachments = (message.attachments || []).map(attachmentHtml).join("");
  const only = !text && attachments;
  return `<div class="msg ${message.side || "in"} ${event ? `event ${esc(message.type)}` : ""}" data-id="${message.id}"><div class="bubble ${only ? "attachment-only" : ""}">${sender}${textHtml}${attachments}${missing}<div class="meta">${edited}${esc(message.time || "")}</div></div></div>`;
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

function renderedSearchResults() {
  return Array.from(new Set(Array.from(document.querySelectorAll(".msg mark")).map((mark) => mark.closest(".msg")).filter(Boolean)));
}

function goToResult(direction) {
  if (view !== "chat") showChat();
  while (rendered < filtered.length) renderMore();
  const results = renderedSearchResults();
  if (!results.length) return;
  currentResult = (currentResult + direction + results.length) % results.length;
  document.querySelectorAll(".msg.current-result").forEach((item) => item.classList.remove("current-result"));
  results[currentResult].classList.add("current-result");
  results[currentResult].scrollIntoView({ behavior: "smooth", block: "center" });
  $("#searchStatus").textContent = `${currentResult + 1}/${results.length} · ${t("viewer_search_results", { count: results.length })}`;
}

function clearFilters() {
  $("#search").value = "";
  $("#dateFrom").value = "";
  $("#dateTo").value = "";
  setParticipant("");
  setType("all");
  showChat();
}

document.addEventListener("input", (event) => {
  if (event.target.matches("#search, #dateFrom, #dateTo")) applyFilters();
});

document.addEventListener("keydown", (event) => {
  if (!event.target.matches("#search")) return;
  if (event.key === "Enter") {
    event.preventDefault();
    goToResult(event.shiftKey ? -1 : 1);
  }
  if (event.key === "Escape") {
    event.target.value = "";
    applyFilters();
  }
});

document.addEventListener("click", (event) => {
  if (event.target.matches("#participantButton")) {
    toggleDropdown("participant");
    return;
  }
  if (event.target.matches("#typeButton")) {
    toggleDropdown("type");
    return;
  }
  const participantOption = event.target.closest("#participantOptions [data-participant]");
  if (participantOption) {
    setParticipant(participantOption.dataset.participant);
    return;
  }
  const typeOption = event.target.closest("#typeOptions [data-type]");
  if (typeOption) {
    setType(typeOption.dataset.type);
    return;
  }
  if (!event.target.closest(".custom-select")) closeAllDropdowns();

  const participant = event.target.closest("[data-part]");
  if (participant) setParticipant(participant.dataset.part);

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
  if (event.target.matches("#prevResult")) goToResult(-1);
  if (event.target.matches("#nextResult")) goToResult(1);
  if (event.target.matches("#clearFilters")) clearFilters();
  if (event.target.matches("#compactMode")) {
    document.body.classList.toggle("compact");
    event.target.setAttribute("aria-pressed", String(document.body.classList.contains("compact")));
    localStorage.setItem("compactMode", String(document.body.classList.contains("compact")));
  }
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
