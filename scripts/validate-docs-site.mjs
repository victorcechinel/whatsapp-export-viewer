import { readFileSync, existsSync } from "node:fs";
import { join, dirname, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const docs = join(root, "docs");
const pages = ["en", "pt-BR", "es"];
const errors = [];

function read(relativePath) {
  return readFileSync(join(docs, relativePath), "utf8");
}

function fail(message) {
  errors.push(message);
}

function attrs(tag) {
  const result = {};
  for (const match of tag.matchAll(/([a-zA-Z:-]+)=["']([^"']*)["']/g)) {
    result[match[1]] = match[2];
  }
  return result;
}

function ids(html) {
  return new Set([...html.matchAll(/\sid=["']([^"']+)["']/g)].map((match) => match[1]));
}

function ensureLocalTarget(page, href) {
  if (!href || href.startsWith("http") || href.startsWith("mailto:") || href.startsWith("#")) {
    return;
  }
  const withoutHash = href.split("#")[0];
  const currentDir = dirname(join(docs, page));
  const resolved = normalize(join(currentDir, withoutHash));
  const htmlTarget = withoutHash.endsWith("/") ? join(resolved, "index.html") : resolved;
  if (!htmlTarget.startsWith(docs) || !existsSync(htmlTarget)) {
    fail(`${page}: local link does not resolve: ${href}`);
  }
}

function validateLocalizedPage(lang) {
  const page = `${lang}/index.html`;
  const html = read(page);
  const pageIds = ids(html);

  if (!html.includes(`<html lang="${lang}"`)) fail(`${page}: missing html lang`);
  if (!/<title>[^<]{30,}<\/title>/.test(html)) fail(`${page}: title is missing or too short`);
  if (!/<meta name="description" content="[^"]{80,}">/.test(html)) fail(`${page}: meta description is missing or too short`);
  if (!/<h1>[^<]+WhatsApp[^<]+<\/h1>/i.test(html)) fail(`${page}: h1 should describe WhatsApp use case`);
  if (!html.includes('<script type="application/ld+json">')) fail(`${page}: missing SoftwareApplication JSON-LD`);
  if (!html.includes('rel="canonical"')) fail(`${page}: missing canonical link`);

  for (const expectedLang of [...pages, "x-default"]) {
    if (!html.includes(`hreflang="${expectedLang}"`)) {
      fail(`${page}: missing hreflang ${expectedLang}`);
    }
  }

  const languageMenu = html.match(/<div class="language-menu"[\s\S]*?<\/div><\/div>/);
  if (!languageMenu) {
    fail(`${page}: missing custom language menu`);
  } else {
    const links = [...languageMenu[0].matchAll(/<a\s+([^>]+)>/g)].map((match) => attrs(match[0]));
    if (links.length !== 2) fail(`${page}: language menu should link to the other two languages`);
    for (const link of links) {
      if (!pages.includes(link["data-lang"])) fail(`${page}: language option missing valid data-lang`);
      ensureLocalTarget(page, link.href);
      const hostedUrl = new URL(link.href, `https://victorcechinel.github.io/whatsapp-export-viewer/${lang}/`);
      if (!hostedUrl.pathname.startsWith("/whatsapp-export-viewer/")) {
        fail(`${page}: language link escapes project path on GitHub Pages: ${link.href}`);
      }
    }
  }

  for (const match of html.matchAll(/<a\s+([^>]+)>/g)) {
    const linkAttrs = attrs(match[0]);
    const href = linkAttrs.href;
    if (href?.startsWith("#") && !pageIds.has(href.slice(1))) {
      fail(`${page}: hash link has no target: ${href}`);
    }
    ensureLocalTarget(page, href);
  }

  for (const match of html.matchAll(/<(?:script|link)\s+([^>]+)>/g)) {
    const tagAttrs = attrs(match[0]);
    ensureLocalTarget(page, tagAttrs.src || tagAttrs.href);
  }
}

function validateRootPage() {
  const html = read("index.html");
  if (!html.includes("navigator.language")) fail("index.html: missing browser language detection");
  for (const lang of pages) {
    if (!html.includes(`${lang}/`)) fail(`index.html: missing ${lang} route`);
  }
}

validateRootPage();
for (const lang of pages) validateLocalizedPage(lang);

const siteJs = read("site.js");
if (!siteJs.includes("data-lang") || !siteJs.includes("data-site-base")) {
  fail("site.js: language selector should use explicit language metadata");
}

if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log("Docs site validation passed");
