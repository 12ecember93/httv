const urls = {
  chatgpt: "https://chatgpt.com/?q=",
  gemini: "https://gemini.google.com/app?query=",
  grok: "https://grok.x.ai/?q=",
  perplexity: "https://www.perplexity.ai/search?q="
};

document.getElementById('send').addEventListener('click', sendToAIs);
document.getElementById('query').addEventListener('keypress', e => {
  if (e.key === 'Enter') sendToAIs();
});

async function sendToAIs() {
  const query = encodeURIComponent(document.getElementById('query').value.trim());
  if (!query) return;

  const activeAIs = [];
  for (const [id, baseUrl] of Object.entries(urls)) {
    if (document.getElementById(id).checked) {
      activeAIs.push(baseUrl + query);
    }
  }

  for (const url of activeAIs) {
    await browser.tabs.create({ url });
  }

  // Tùy chọn: đóng popup sau khi gửi
  window.close();
}
