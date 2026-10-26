// ApplyPilot Popup Logic
document.addEventListener("DOMContentLoaded", async () => {
  const backendPill = document.getElementById("backend-status");
  const shieldPill = document.getElementById("shield-count");
  const startHarvestBtn = document.getElementById("start-harvest-btn");
  const startBatchBtn = document.getElementById("start-batch-btn");
  const openPostsBtn = document.getElementById("open-posts-btn");
  const openDashBtn = document.getElementById("open-dashboard-btn");

  // Check backend health & 30-day shield
  try {
    const res = await fetch("http://localhost:8000/api/applications/past-30-days-history");
    if (res.ok) {
      const data = await res.json();
      backendPill.textContent = "Online (8000)";
      backendPill.className = "status-pill active";
      shieldPill.textContent = `${data.total_unique_companies || 65} Protected`;
    } else {
      backendPill.textContent = "Connected";
      backendPill.className = "status-pill active";
    }
  } catch (err) {
    backendPill.textContent = "Local Standalone";
    backendPill.className = "status-pill active";
  }

  // Start Recruiter Post Harvester
  startHarvestBtn.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url || !tab.url.includes("linkedin.com")) {
      const postsUrl = "https://www.linkedin.com/search/results/content/?keywords=hiring%20%28software%20engineer%20OR%20developer%29%20%28email%20OR%20mail%20OR%20cv%29&sortBy=%22date_posted%22";
      chrome.tabs.create({ url: postsUrl });
      return;
    }

    try {
      await chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ["content.css"] });
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    } catch (e) {}

    setTimeout(() => {
      chrome.tabs.sendMessage(tab.id, { action: "startHarvest" }, () => {
        window.close();
      });
    }, 400);
  });

  // Start Safe Batch directly from popup
  startBatchBtn.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url || !tab.url.includes("linkedin.com")) {
      alert("Please switch to your active LinkedIn tab first!");
      return;
    }

    try {
      await chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ["content.css"] });
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    } catch (e) {}

    setTimeout(() => {
      chrome.tabs.sendMessage(tab.id, { action: "startAutoApply" }, () => {
        window.close();
      });
    }, 400);
  });

  // Open LinkedIn Posts Feed
  openPostsBtn.addEventListener("click", () => {
    const postsUrl = "https://www.linkedin.com/search/results/content/?keywords=hiring%20%28software%20engineer%20OR%20developer%29%20%28email%20OR%20mail%20OR%20cv%29&sortBy=%22date_posted%22";
    chrome.tabs.create({ url: postsUrl });
  });

  // Open Dashboard
  openDashBtn.addEventListener("click", () => {
    chrome.tabs.create({ url: "http://localhost:5173/emails" });
  });
});
