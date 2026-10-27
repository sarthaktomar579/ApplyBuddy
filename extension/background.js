// ApplyPilot Background Service Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log("ApplyPilot AI LinkedIn Extension installed.");
  // Initialize default settings
  chrome.storage.local.get(["userAnswers", "batchSize", "delaySeconds"], (res) => {
    if (!res.userAnswers) {
      chrome.storage.local.set({
        batchSize: 15,
        delaySeconds: 15,
        userAnswers: {
          phone: "+91-6377525805",
          experienceYears: 1,
          noticeDays: 7,
          noticeText: "Immediately Available",
          expectedSalaryLPA: 6,
          city: "Gurugram",
          authorizedInIndia: true,
          requireSponsorship: false,
          agreeTerms: true
        },
        blacklist: [
          "dexter", "thinknova", "recruitdiary", "talentrabbit",
          "techversant", "training institute", "placement fee", "pay after placement"
        ]
      });
    }
  });
});

// Relay messages if needed
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "syncApplicationToBackend") {
    fetch("http://localhost:8000/api/applications/record-manual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company: request.company,
        title: request.title,
        applied_via: "linkedin",
        status: "application_submitted",
        application_url: request.url,
        notes: "Live authentic application submitted via ApplyPilot Chrome Extension directly on LinkedIn."
      })
    })
      .then((res) => res.json())
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // async
  }
});
