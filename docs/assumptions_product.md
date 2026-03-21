# Product Assumptions — Restaurant Intelligence Platform

These are the key assumptions about the market, users, and product behaviour that guide design decisions. They should be validated through real usage.

---

## User Assumptions

### A1. Owners prefer daily summaries over real-time dashboards
**Assumption:** Restaurant owners don't have time to monitor a dashboard throughout the day. A daily report delivered at 7:00 AM is more valuable than real-time alerts.  
**Implication:** Daily email report is the primary engagement mechanism, not push notifications.  
**Risk:** Some users may want real-time alerts for critical issues.

---

### A2. Simple actions beat complex insights
**Assumption:** "Add one waiter on Friday evening" is more useful than "your service time percentile is in the 3rd quartile".  
**Implication:** All AI outputs are formatted as plain-language, actionable Italian sentences.  
**Risk:** Power users (e.g., multi-location chain managers) may want more granular data.

---

### A3. CSV upload is sufficient for the MVP
**Assumption:** Most independent restaurants can export or manually create CSV files from their existing POS or spreadsheets.  
**Implication:** No POS integration is required for initial validation.  
**Risk:** Friction in data entry may reduce adoption. Real-time sync becomes critical in Phase 6.

---

### A4. Italian market is the primary target
**Assumption:** Initial users will be Italian restaurant owners; Italian language in the UI and AI outputs is mandatory.  
**Implication:** All review analysis, suggestions, alert messages, and reports are in Italian.  
**Risk:** Limits initial market size; localization needed for international expansion.

---

### A5. Reviews are the primary feedback signal
**Assumption:** Customer reviews on Google/TripAdvisor are a reliable proxy for operational quality.  
**Implication:** The review analysis pipeline is the core intelligence layer.  
**Risk:** Reviews may lag reality by days or weeks; some issues may not be reported online.

---

## Business Assumptions

### B1. Willingness to pay is driven by ROI on staff decisions
**Assumption:** The highest perceived value is avoiding a surprise busy Saturday with insufficient staff. If the platform prevents one bad service even once per month, the subscription pays for itself.  
**Implication:** Forecasting and staffing suggestions should be the most prominent features.

---

### B2. The trial converts if the owner sees one useful insight
**Assumption:** A 7-day trial is enough time to import some data, run an analysis, and see a specific suggestion.  
**Implication:** The onboarding flow (setup page) must lead to the first useful insight within 5 minutes.

---

### B3. Starter plan (49€/month) is price-sensitive threshold
**Assumption:** Independent restaurant owners are comfortable with 49€/month but may hesitate at higher tiers.  
**Implication:** Core value (forecasting + daily report) is available on Starter. Advanced features (alerts, LLM correlations, menu optimizer) require Pro/Premium.

---

## Data Assumptions

### D1. Minimum viable dataset for forecasting
**Assumption:** 7+ days of sales data produces a meaningful forecast. 14+ days produces a good forecast.  
**Implication:** Forecasting engine returns zero predictions if fewer than 7 records exist. Onboarding encourages uploading at least 2 weeks of history.

---

### D2. Review platform doesn't matter for sentiment analysis
**Assumption:** Reviews from Google and TripAdvisor are sufficiently similar in language and format for a unified analysis pipeline.  
**Implication:** Platform field is stored but not used for separate analysis logic.

---

### D3. Product names in sales data are consistent
**Assumption:** The restaurant uses consistent product names across their sales records (e.g., always "Pizza Margherita", not sometimes "Margherita", sometimes "pizza marg").  
**Implication:** No name normalization is implemented. Users are responsible for consistency.  
**Risk:** Inconsistent names fragment forecasts and purchase orders.

---

## AI / LLM Assumptions

### L1. GPT-4o-mini is accurate enough for operational suggestions
**Assumption:** The model's Italian-language operational suggestions are specific enough to be actionable without hallucinating critical details.  
**Implication:** LLM is used for correlation analysis and insights. Temperature is set to 0.3 for consistency.

---

### L2. Rule-based fallback covers 80% of cases
**Assumption:** The 7 correlation rules and 4 insight rules cover the most common restaurant operational patterns.  
**Implication:** The platform delivers value even without an OpenAI API key.

---

### L3. Keyword-based sentiment analysis is sufficient for v1
**Assumption:** The keyword matching approach correctly classifies 70%+ of reviews.  
**Implication:** No ML model needed for review analysis in the MVP; replace with LLM in a future iteration.
