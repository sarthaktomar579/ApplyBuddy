// ApplyPilot AI — Real LinkedIn Easy Apply & Recruiter Post Email Harvester
// Injected into https://www.linkedin.com/*

let isRunning = false;
let isHarvesting = false;
let appliedCount = 0;
let skippedCount = 0;
let harvestedCount = 0;
let maxBatch = 15;
let shieldedCompanies = new Set();
let postSeenEmails = new Set();
let blacklistedKeywords = [
  "dexter", "thinknova", "recruitdiary", "talentrabbit",
  "techversant", "training institute", "placement guarantee", "pay after placement",
  "pinnacle", "pinnacle u", "pinnacle infotech"
];

// Profile answers for Sarthak Singh Tomar
const profileAnswers = {
  phone: "6377525805",
  fullPhone: "+91-6377525805",
  experienceYears: "1",
  noticeDays: "7",
  noticeText: "Immediately Available",
  expectedSalaryNum: "600000",
  expectedSalaryLPA: "6",
  city: "Gurugram"
};

// Initialize UI
function initPanel() {
  if (document.getElementById("applypilot-floating-panel")) return;

  const panel = document.createElement("div");
  panel.id = "applypilot-floating-panel";
  panel.innerHTML = `
    <div class="applypilot-header">
      <div class="applypilot-title">
        <span>⚡ ApplyPilot AI</span>
        <span class="applypilot-badge">Direct Outreach</span>
      </div>
      <button id="applypilot-close-btn" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;">×</button>
    </div>

    <div class="applypilot-stats">
      <div class="applypilot-stat-box">
        <div id="applypilot-applied-count" class="applypilot-stat-val applied">0</div>
        <div class="applypilot-stat-lbl">Emails Delivered</div>
      </div>
      <div class="applypilot-stat-box">
        <div id="applypilot-skipped-count" class="applypilot-stat-val">0</div>
        <div class="applypilot-stat-lbl">15d Shielded / Safe</div>
      </div>
    </div>

    <div id="applypilot-status" class="applypilot-status-text">
      Ready. Auto-harvest real recruiter emails from posts or Easy Apply to jobs.
    </div>

    <div class="applypilot-actions" style="flex-direction:column; gap:6px;">
      <button id="applypilot-harvest-btn" class="applypilot-btn applypilot-btn-purple">
        ⚡ Auto-Harvest & Email Recruiters (Post Mode)
      </button>
      <button id="applypilot-stop-harvest-btn" class="applypilot-btn applypilot-btn-danger" style="display:none;">
        ⏹ Stop Post Harvester
      </button>
      <button id="applypilot-start-btn" class="applypilot-btn applypilot-btn-secondary">
        💼 Easy Apply Jobs (Batch 15)
      </button>
      <button id="applypilot-stop-btn" class="applypilot-btn applypilot-btn-danger" style="display:none;">
        ⏹ Stop Easy Apply
      </button>
    </div>

    <a href="https://www.linkedin.com/search/results/content/?keywords=hiring%20%28software%20engineer%20OR%20developer%29%20%28email%20OR%20mail%20OR%20cv%29&sortBy=%22date_posted%22" class="applypilot-quick-link" target="_self">
      🔍 Open Hiring Posts Feed (1-Click)
    </a>

    <div class="applypilot-guarantees">
      <div class="applypilot-guarantee-item">
        <div class="applypilot-guarantee-dot"></div>
        <span><strong>Verified Delivery:</strong> Direct to recruiter inbox with PDF resume</span>
      </div>
      <div class="applypilot-guarantee-item">
        <div class="applypilot-guarantee-dot"></div>
        <span><strong>15-Day Duplicate Shield:</strong> Checks Gmail Sent history</span>
      </div>
      <div class="applypilot-guarantee-item">
        <div class="applypilot-guarantee-dot"></div>
        <span><strong>Pinnacle Excluded:</strong> Protected active interview</span>
      </div>
    </div>
  `;

  document.body.appendChild(panel);

  document.getElementById("applypilot-harvest-btn").addEventListener("click", startHarvest);
  document.getElementById("applypilot-stop-harvest-btn").addEventListener("click", () => stopHarvest("Harvester stopped by user."));
  document.getElementById("applypilot-start-btn").addEventListener("click", startBatch);
  document.getElementById("applypilot-stop-btn").addEventListener("click", () => stopBatch("Easy Apply stopped by user."));
  document.getElementById("applypilot-close-btn").addEventListener("click", () => {
    panel.style.display = "none";
  });
}

// Fetch 30-day history from ApplyPilot backend
async function fetchShieldedCompanies() {
  try {
    const res = await fetch("http://localhost:8000/api/applications/past-30-days-history");
    if (res.ok) {
      const data = await res.json();
      if (data.companies && Array.isArray(data.companies)) {
        shieldedCompanies = new Set(data.companies.map((c) => c.toLowerCase().trim()));
        console.log(`[ApplyPilot] Loaded ${shieldedCompanies.size} shielded companies from backend.`);
      }
    }
  } catch (err) {
    console.warn("[ApplyPilot] Could not connect to localhost:8000. Operating in standalone mode.");
  }
}

function updateStatus(text) {
  const el = document.getElementById("applypilot-status");
  if (el) el.textContent = text;
  console.log(`[ApplyPilot] ${text}`);
}

function updateCounts() {
  const appEl = document.getElementById("applypilot-applied-count");
  const skipEl = document.getElementById("applypilot-skipped-count");
  if (appEl) appEl.textContent = appliedCount + harvestedCount;
  if (skipEl) skipEl.textContent = skippedCount;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// --- RECRUITER POST EMAIL HARVESTER MODE ---
async function startHarvest() {
  if (isHarvesting) return;
  isHarvesting = true;
  harvestedCount = 0;
  updateCounts();

  document.getElementById("applypilot-harvest-btn").style.display = "none";
  document.getElementById("applypilot-stop-harvest-btn").style.display = "flex";

  updateStatus("Scanning LinkedIn feed & posts for recruiter emails...");
  await runPostHarvesterLoop();
}

function stopHarvest(reason = "Harvester stopped.") {
  isHarvesting = false;
  const startBtn = document.getElementById("applypilot-harvest-btn");
  const stopBtn = document.getElementById("applypilot-stop-harvest-btn");
  if (startBtn) startBtn.style.display = "flex";
  if (stopBtn) stopBtn.style.display = "none";
  updateStatus(reason);
}

async function runPostHarvesterLoop() {
  const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;

  while (isHarvesting) {
    // 1. Expand all "...see more" buttons currently visible
    const seeMoreBtns = document.querySelectorAll(
      "button.feed-shared-inline-show-more-text__see-more-less-toggle, button[aria-label*='see more'], button.see-more"
    );
    for (const btn of seeMoreBtns) {
      if (btn && btn.offsetParent !== null) {
        try {
          btn.click();
        } catch (e) {}
      }
    }
    await sleep(400);

    // 2. Locate post elements
    const postCards = Array.from(document.querySelectorAll(
      "div.feed-shared-update-v2, div[data-chameleon-result-urn], div.update-components-text, .search-results-container .artdeco-card, li.reusable-search__result-container"
    ));

    let foundNewInPass = false;

    for (const post of postCards) {
      if (!isHarvesting) break;

      const text = post.innerText || "";
      const matches = text.match(emailRegex);

      if (matches && matches.length > 0) {
        for (const rawEmail of matches) {
          const cleanEmail = rawEmail.toLowerCase().trim();
          if (postSeenEmails.has(cleanEmail)) continue;
          postSeenEmails.add(cleanEmail);

          // Local anti-scam & exclusion checks
          const isBlacklisted = blacklistedKeywords.some(
            (kw) => cleanEmail.includes(kw) || text.toLowerCase().includes(kw)
          );
          if (isBlacklisted) {
            console.log(`[ApplyPilot] Filtered excluded/blacklisted email: ${cleanEmail}`);
            skippedCount++;
            updateCounts();
            continue;
          }

          // Extract author info
          let authorName = "Recruiter / Hiring Lead";
          let authorTitle = "Talent Acquisition Specialist";
          const actorNameEl = post.querySelector(
            ".update-components-actor__name, .feed-shared-actor__name, .entity-result__title-text, span[dir='ltr']"
          );
          if (actorNameEl) {
            authorName = actorNameEl.innerText.split("\n")[0].trim();
          }

          const actorDescEl = post.querySelector(
            ".update-components-actor__description, .feed-shared-actor__description, .entity-result__primary-subtitle"
          );
          if (actorDescEl) {
            authorTitle = actorDescEl.innerText.split("\n")[0].trim();
          }

          // Infer company
          let company = "";
          const compMatch = authorTitle.match(/at\s+([A-Za-z0-9\s]+?)(?:\||—|-|\.|\n|$)/i);
          if (compMatch) {
            company = compMatch[1].trim();
          }

          updateStatus(`Found recruiter: ${authorName} <${cleanEmail}>. Dispatching application via Gmail...`);

          try {
            const resp = await fetch("http://localhost:8000/api/jobs/harvest-from-linkedin", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                author_name: authorName,
                author_title: authorTitle,
                company: company || undefined,
                recipient_email: cleanEmail,
                post_text: text.slice(0, 3000),
                post_url: window.location.href,
                auto_send: true
              })
            });

            if (resp.ok) {
              const resJson = await resp.json();
              if (resJson.status === "success" && resJson.delivery === "sent") {
                harvestedCount++;
                updateCounts();
                updateStatus(`✅ Delivered application to ${authorName} (${cleanEmail}) with Resume attached!`);
              } else if (resJson.status === "skipped") {
                skippedCount++;
                updateCounts();
                updateStatus(`🛡️ Shielded: ${resJson.reason}`);
              } else {
                updateStatus(`Notice: ${resJson.reason || resJson.status}`);
              }
            } else {
              console.warn("[ApplyPilot] Harvest POST failed:", resp.status);
            }
          } catch (err) {
            console.error("[ApplyPilot] Harvest POST network error:", err);
          }

          foundNewInPass = true;
          // Pacing delay between applications
          await sleep(3000);
        }
      }
    }

    if (!foundNewInPass) {
      updateStatus("Scrolling to discover more recruiter posts...");
    }

    // Smooth scroll down to trigger LinkedIn lazy loading
    window.scrollBy({ top: 750, behavior: "smooth" });
    await sleep(2500);
  }

  stopHarvest("Post Harvester complete.");
}

async function startBatch() {
  if (isRunning) return;
  isRunning = true;
  appliedCount = 0;
  skippedCount = 0;
  updateCounts();

  document.getElementById("applypilot-start-btn").style.display = "none";
  document.getElementById("applypilot-stop-btn").style.display = "flex";

  updateStatus("Scanning active LinkedIn jobs list...");
  await fetchShieldedCompanies();

  await runAutoApplyLoop();
}

function stopBatch(reason = "Stopped.") {
  isRunning = false;
  const startBtn = document.getElementById("applypilot-start-btn");
  const stopBtn = document.getElementById("applypilot-stop-btn");
  if (startBtn) startBtn.style.display = "flex";
  if (stopBtn) stopBtn.style.display = "none";
  updateStatus(reason);
}

function getLinkedInJobCards() {
  // Strategy 1: Data attributes on list items (Modern LinkedIn)
  let cards = Array.from(document.querySelectorAll("li[data-occludable-job-id], li[data-job-id], [data-occludable-entity-urn*='jobPosting']"));
  if (cards.length > 0) return cards;

  // Strategy 2: Job card containers or list items
  cards = Array.from(document.querySelectorAll(".job-card-container, .jobs-search-results__list-item, ul.scaffold-layout__list-container > li, .jobs-search-results-list li"));
  if (cards.length > 0) return cards;

  // Strategy 3: Target links with /jobs/view/ in the left sidebar
  const links = Array.from(document.querySelectorAll("a[href*='/jobs/view/'], a[href*='currentJobId=']"));
  const cardSet = new Set();
  links.forEach((l) => {
    const parent = l.closest("li") || l.closest("div[data-view-name]") || l.closest(".job-card-container");
    if (parent) cardSet.add(parent);
  });
  if (cardSet.size > 0) return Array.from(cardSet);

  return [];
}

function getExpectedCTCForLocation(jobLocation = "") {
  const loc = (jobLocation || "").toLowerCase();

  // 1. Remote -> 4.5 LPA
  if (loc.includes("remote") || loc.includes("work from home") || loc.includes("wfh")) {
    return { lpa: "4.5", num: "450000", text: "4.5 LPA" };
  }

  // 2. Bangalore / Bengaluru, Pune, Hyderabad -> 6 LPA
  if (
    loc.includes("bangalore") ||
    loc.includes("bengaluru") ||
    loc.includes("pune") ||
    loc.includes("hyderabad")
  ) {
    return { lpa: "6", num: "600000", text: "6 LPA" };
  }

  // 3. Delhi NCR (Delhi, Gurugram, Gurgaon, Noida, Ghaziabad, Faridabad) -> 5 LPA
  if (
    loc.includes("delhi") ||
    loc.includes("gurgaon") ||
    loc.includes("gurugram") ||
    loc.includes("noida") ||
    loc.includes("ncr") ||
    loc.includes("ghaziabad") ||
    loc.includes("faridabad")
  ) {
    return { lpa: "5", num: "500000", text: "5 LPA" };
  }

  // Fallback: 5 LPA
  return { lpa: "5", num: "500000", text: "5 LPA" };
}

async function runAutoApplyLoop() {
  // 0. If an Easy Apply modal is ALREADY OPEN on screen, finish and submit it right now!
  const openModal = document.querySelector(".jobs-easy-apply-modal, div[role='dialog']");
  if (openModal) {
    const modalHeading = (openModal.querySelector("h2, h1")?.innerText || "").replace(/apply to/i, "").trim() || "Current Job";
    updateStatus(`Found open application modal for [${modalHeading}]. Progressing form...`);
    const success = await handleEasyApplyModal(modalHeading, "Software Developer", "");
    if (success) {
      appliedCount++;
      updateCounts();
      updateStatus(`✅ Applied to ${modalHeading}! LinkedIn sent confirmation email.`);
      chrome.runtime.sendMessage({
        action: "syncApplicationToBackend",
        company: modalHeading,
        title: "Software Developer",
        url: window.location.href
      });
      await sleep(10000);
    }
  }

  // Check if current open job in right pane already has Easy Apply visible
  const activeEasyApply = findEasyApplyButton();
  if (activeEasyApply) {
    const activeTitle = (document.querySelector(".job-details-jobs-unified-top-card__job-title, h1, h2")?.innerText || "Software Developer").trim();
    const activeCompany = (document.querySelector(".job-details-jobs-unified-top-card__company-name, .job-details-jobs-unified-top-card__primary-description a")?.innerText || "").trim();
    const activeLocation = (document.querySelector(".job-details-jobs-unified-top-card__primary-description, .jobs-unified-top-card__bullet, .job-details-jobs-unified-top-card__workplace-type")?.innerText || "").trim();
    
    updateStatus(`Found active job [${activeTitle} at ${activeCompany} (${activeLocation})]. Applying...`);
    const compKey = activeCompany.toLowerCase().trim();

    if (!shieldedCompanies.has(compKey)) {
      activeEasyApply.click();
      await sleep(2000);
      const success = await handleEasyApplyModal(activeCompany, activeTitle, activeLocation);
      if (success) {
        appliedCount++;
        shieldedCompanies.add(compKey);
        updateCounts();
        updateStatus(`✅ Applied to ${activeCompany}! LinkedIn sent confirmation email.`);
        chrome.runtime.sendMessage({
          action: "syncApplicationToBackend",
          company: activeCompany,
          title: activeTitle,
          url: window.location.href
        });
        await sleep(15000);
      }
    }
  }

  // Scroll left job list to ensure items render
  const listContainer = document.querySelector(".jobs-search-results-list, .scaffold-layout__list-container, div[tabindex='-1']");
  if (listContainer) {
    listContainer.scrollBy({ top: 300, behavior: "smooth" });
    await sleep(800);
  }

  // Find job items in LinkedIn list
  const jobCards = getLinkedInJobCards();

  if (jobCards.length === 0) {
    updateStatus("Searching for jobs... Click on any job card in the left list to start.");
    stopBatch("Ready. Click any job to begin.");
    return;
  }

  updateStatus(`Found ${jobCards.length} listings. Running batch...`);

  for (let i = 0; i < jobCards.length; i++) {
    if (!isRunning) break;
    if (appliedCount >= maxBatch) {
      stopBatch(`Safe batch complete! Applied to ${appliedCount} positions.`);
      break;
    }

    const card = jobCards[i];
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    await sleep(800);

    // Extract title, company & location
    const titleEl = card.querySelector(".job-card-list__title, a.job-card-container__link, strong, h3, a[href*='/jobs/view/']");
    const companyEl = card.querySelector(".job-card-container__primary-description, .artdeco-entity-lockup__subtitle, .job-card-container__company-name, span.job-card-container__primary-description");
    const locationEl = card.querySelector(".job-card-container__metadata-item, ul.job-card-container__metadata-wrapper li, span.job-card-container__primary-description ~ ul li");

    const jobTitle = titleEl ? titleEl.innerText.trim() : "Software Developer";
    const company = companyEl ? companyEl.innerText.trim() : "";
    const jobLocation = locationEl ? locationEl.innerText.trim() : "";
    const compKey = company.toLowerCase().trim();

    // 1. Anti-Scam filter
    const isScam = blacklistedKeywords.some((w) => compKey.includes(w) || jobTitle.toLowerCase().includes(w));
    if (isScam) {
      skippedCount++;
      updateCounts();
      updateStatus(`Skipping [${company}]: Scam/Training institute blacklisted.`);
      await sleep(800);
      continue;
    }

    // 2. 30-Day Duplicate Shield
    if (shieldedCompanies.has(compKey)) {
      skippedCount++;
      updateCounts();
      updateStatus(`Skipping [${company}]: Already applied in past 30 days.`);
      await sleep(800);
      continue;
    }

    // Click job card to view details
    if (titleEl) {
      titleEl.click();
    } else {
      card.click();
    }
    await sleep(2000);

    // Look for Easy Apply button
    const applyButton = findEasyApplyButton();
    if (!applyButton) {
      skippedCount++;
      updateCounts();
      updateStatus(`[${company}] External portal (not Easy Apply). Skipped.`);
      await sleep(1000);
      continue;
    }

    const ctcConfig = getExpectedCTCForLocation(jobLocation);
    updateStatus(`Clicking Easy Apply for [${jobTitle} at ${company}] (Target CTC: ${ctcConfig.text})...`);
    applyButton.click();
    await sleep(2000);

    // Solve the Easy Apply modal
    const success = await handleEasyApplyModal(company, jobTitle, jobLocation);
    if (success) {
      appliedCount++;
      shieldedCompanies.add(compKey);
      updateCounts();
      updateStatus(`✅ Applied to ${company}! LinkedIn sent confirmation email.`);

      // Sync to ApplyPilot backend
      chrome.runtime.sendMessage({
        action: "syncApplicationToBackend",
        company: company,
        title: jobTitle,
        url: window.location.href
      });

      // Human-like safety pause (15s)
      if (appliedCount < maxBatch && isRunning) {
        for (let s = 15; s > 0; s--) {
          if (!isRunning) break;
          updateStatus(`Applied ${appliedCount}/${maxBatch}. Safety cooldown: ${s}s...`);
          await sleep(1000);
        }
      }
    } else {
      skippedCount++;
      updateCounts();
      updateStatus(`[${company}] Requires manual review or custom questions. Skipped safely.`);
    }
  }

  if (isRunning) {
    stopBatch(`Batch complete! Applied: ${appliedCount}, Skipped: ${skippedCount}.`);
  }
}

function findEasyApplyButton() {
  const buttons = Array.from(document.querySelectorAll("button"));
  return buttons.find((btn) => {
    const text = btn.innerText || "";
    return (
      text.includes("Easy Apply") &&
      !text.includes("Applied") &&
      btn.offsetParent !== null // is visible
    );
  });
}

function clickBtn(btn) {
  if (!btn) return;
  btn.focus();
  btn.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true, view: window }));
  btn.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, view: window }));
  btn.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true, view: window }));
  btn.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true, view: window }));
  btn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
  if (typeof btn.click === "function") btn.click();
}

function findPrimaryFooterButton(modal) {
  const allButtons = Array.from(modal.querySelectorAll("button"));

  // Check 1: Submit button
  const submitBtn = allButtons.find((b) => {
    const t = (b.innerText || "").trim().toLowerCase();
    const aria = (b.getAttribute("aria-label") || "").toLowerCase();
    return t.includes("submit") || aria.includes("submit");
  });
  if (submitBtn) return { btn: submitBtn, action: "submit" };

  // Check 2: Review button
  const reviewBtn = allButtons.find((b) => {
    const t = (b.innerText || "").trim().toLowerCase();
    const aria = (b.getAttribute("aria-label") || "").toLowerCase();
    return t.includes("review") || aria.includes("review");
  });
  if (reviewBtn) return { btn: reviewBtn, action: "review" };

  // Check 3: Next button
  const nextBtn = allButtons.find((b) => {
    const t = (b.innerText || "").trim().toLowerCase();
    const aria = (b.getAttribute("aria-label") || "").toLowerCase();
    const isNext = t === "next" || t.includes("next") || aria.includes("continue") || aria.includes("next") || b.hasAttribute("data-easy-apply-next-button");
    return isNext && !t.includes("previous") && !aria.includes("previous");
  });
  if (nextBtn) return { btn: nextBtn, action: "next" };

  // Check 4: Primary button in footer
  const primaryBtn = modal.querySelector(
    "footer button.artdeco-button--primary, .jobs-easy-apply-footer button.artdeco-button--primary, button.artdeco-button--primary"
  );
  if (primaryBtn) {
    const t = (primaryBtn.innerText || "").trim().toLowerCase();
    return { btn: primaryBtn, action: t.includes("submit") ? "submit" : (t.includes("review") ? "review" : "next") };
  }

  return null;
}

async function handleEasyApplyModal(company, jobTitle, jobLocation = "") {
  let modal = null;
  for (let m = 0; m < 6; m++) {
    modal = document.querySelector(".jobs-easy-apply-modal, div[role='dialog']");
    if (modal) break;
    await sleep(500);
  }
  if (!modal) {
    console.warn("[ApplyPilot] Modal not found after click.");
    return false;
  }

  let steps = 0;
  const maxSteps = 10;

  while (steps < maxSteps) {
    steps++;
    await sleep(1000);

    modal = document.querySelector(".jobs-easy-apply-modal, div[role='dialog']");
    if (!modal) break;

    // Fill all form inputs on current step safely
    try {
      fillFormFields(modal, jobLocation);
    } catch (err) {
      console.warn("[ApplyPilot] Error filling form fields:", err);
    }
    await sleep(800);

    // Find the action button
    const target = findPrimaryFooterButton(modal);
    if (!target) {
      console.warn("[ApplyPilot] No footer button found on step", steps);
      break;
    }

    if (target.action === "submit") {
      console.log("[ApplyPilot] Submitting application via target button...");
      updateStatus(`Submitting real application for [${company}]...`);
      clickBtn(target.btn);
      await sleep(3500);
      dismissModal();
      return true;
    }

    console.log(`[ApplyPilot] Step ${steps}: Clicking '${target.action.toUpperCase()}' button...`);
    updateStatus(`Progressing form: Step ${steps} (${target.action.toUpperCase()})...`);
    clickBtn(target.btn);
    await sleep(1800);
  }

  dismissModal();
  return false;
}

function fillFormFields(modal, jobLocation = "") {
  const ctc = getExpectedCTCForLocation(jobLocation);

  // 1. Text & Numeric Inputs
  const textInputs = Array.from(modal.querySelectorAll("input[type='text'], input[type='number'], input:not([type])"));
  textInputs.forEach((input) => {
    const label = getLabelText(input).toLowerCase();
    const val = input.value;

    if (!val || val === "") {
      if (label.includes("phone") || label.includes("mobile")) {
        setInputVal(input, profileAnswers.phone);
      } else if (label.includes("experience") || label.includes("year")) {
        setInputVal(input, profileAnswers.experienceYears);
      } else if (label.includes("notice")) {
        setInputVal(input, input.type === "number" ? profileAnswers.noticeDays : profileAnswers.noticeText);
      } else if (label.includes("salary") || label.includes("ctc") || label.includes("compensation")) {
        setInputVal(input, input.type === "number" ? ctc.num : ctc.lpa);
      } else if (label.includes("city") || label.includes("location")) {
        setInputVal(input, profileAnswers.city);
      } else {
        // Fallback numeric or default
        if (input.type === "number") setInputVal(input, "1");
      }
    }
  });

  // 2. Radio Buttons
  const radioGroups = modal.querySelectorAll("fieldset, div[role='radiogroup']");
  radioGroups.forEach((group) => {
    const legend = (group.querySelector("legend, label, span")?.innerText || "").toLowerCase();
    const radios = Array.from(group.querySelectorAll("input[type='radio']"));

    if (radios.length >= 2) {
      const yesRadio = radios.find((r) => {
        const lbl = (r.closest("label")?.innerText || "").toLowerCase();
        return lbl.includes("yes") || lbl === "y";
      });
      const noRadio = radios.find((r) => {
        const lbl = (r.closest("label")?.innerText || "").toLowerCase();
        return lbl.includes("no") || lbl === "n";
      });

      if (legend.includes("sponsorship") || legend.includes("visa")) {
        if (noRadio && !noRadio.checked) noRadio.click();
      } else {
        // Most questions (authorized in India, commute, background check) are "Yes"
        if (yesRadio && !yesRadio.checked) yesRadio.click();
      }
    }
  });

  // 3. Dropdowns
  const selects = Array.from(modal.querySelectorAll("select"));
  selects.forEach((sel) => {
    if (!sel.value || sel.value === "Select an option") {
      const options = Array.from(sel.options);
      const yesOpt = options.find((o) => o.text.toLowerCase().includes("yes"));
      if (yesOpt) {
        sel.value = yesOpt.value;
        sel.dispatchEvent(new Event("change", { bubbles: true }));
      } else if (options.length > 1) {
        sel.selectedIndex = 1;
        sel.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
  });

  // 4. Resume selection (Page 2 or 3)
  const resumeCards = modal.querySelectorAll(".jobs-document-upload__title, [data-test-document-item], input[type='radio'][name*='resume']");
  if (resumeCards.length > 0) {
    const firstResume = resumeCards[0];
    if (firstResume.tagName === "INPUT" && !firstResume.checked) {
      firstResume.click();
    } else if (firstResume.closest && firstResume.closest("label")) {
      firstResume.closest("label").click();
    }
  }

  // 5. Checkboxes (terms / agreement)
  const checkboxes = Array.from(modal.querySelectorAll("input[type='checkbox']"));
  checkboxes.forEach((cb) => {
    // Uncheck "Follow company" on review page, but check terms agreements
    const lbl = (cb.closest("label")?.innerText || "").toLowerCase();
    if (lbl.includes("follow")) {
      if (cb.checked) cb.click();
    } else {
      if (!cb.checked) cb.click();
    }
  });
}

function setInputVal(input, val) {
  input.focus();
  input.value = val;
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function getLabelText(input) {
  const label = input.closest("label");
  if (label) return label.innerText;
  const prev = input.previousElementSibling;
  if (prev) return prev.innerText;
  const parentText = input.parentElement ? input.parentElement.innerText : "";
  return parentText;
}

function dismissModal() {
  const dismissBtn = document.querySelector(
    "button[aria-label='Dismiss'], button[data-control-name='overlay.close_padding'], .artdeco-modal__dismiss"
  );
  if (dismissBtn) {
    dismissBtn.click();
    setTimeout(() => {
      // If "Save draft / Discard" prompt appears
      const discardBtn = document.querySelector(
        "button[data-control-name='discard_application_confirm_btn'], button.artdeco-button--primary"
      );
      if (discardBtn && discardBtn.innerText.toLowerCase().includes("discard")) {
        discardBtn.click();
      }
    }, 500);
  }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "startAutoApply") {
    initPanel();
    const panel = document.getElementById("applypilot-floating-panel");
    if (panel) panel.style.display = "block";
    startBatch();
    sendResponse({ status: "started" });
  } else if (request.action === "startHarvest") {
    initPanel();
    const panel = document.getElementById("applypilot-floating-panel");
    if (panel) panel.style.display = "block";
    startHarvest();
    sendResponse({ status: "harvest_started" });
  }
});

// Auto-inject on load
if (document.readyState === "complete" || document.readyState === "interactive") {
  initPanel();
} else {
  window.addEventListener("DOMContentLoaded", initPanel);
}
setTimeout(initPanel, 1500);
