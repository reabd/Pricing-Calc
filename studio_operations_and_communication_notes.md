# The Print House — Operations & Client-Communication Notes

Compiled from a sampled read of ~6 months (Feb–Aug 2026) of the `info@theprinthouse.co.il` Gmail
mailbox (~40 threads read in full via `get_thread`, plus triage of ~250+ thread snippets across
~10 targeted searches: order-number subjects, `הצעת מחיר`/`מחיר`/quote/price, deposit/payment,
rush/urgent, inbound vs. outbound). Goal: capture how staff actually write client quote replies and
how the studio really operates, as input for an automated/assisted quote-reply workflow. Cross-checked
against `studio_knowledge.json` and `business_rules.py` — new findings are flagged in Section 5.

Staff first names seen signing emails: **רע** (Rea — the owner and primary correspondent, signs "רע"),
**אמיתי** (Amit), **גל** (Gal), **איה** (Aya), **עינב** (Einav — mentioned as handling walk-in/rush
jobs). Internal notification CCs: `rea@`, `harel@`, `ido@theprinthouse.co.il`, plus an external
bookkeeping contact `tamir.davidoff@gmail.com`. There's also a separate `framing@theprinthouse.co.il`
mailbox for the framing workshop, and the owner uses `info@reastudio.co.il` for some internal/gallery
bookkeeping notes (see Okapics, §3).

---

## 1. Quote-reply template & style guide

### Structure
A typical price-quote reply is **short, conversational, and itemized**, not a formal document:

1. **Greeting** — casual, first-name, often with "מה נשמע?" (how's it going?) or "מה שלומך?" tacked
   on, even for institutional clients. No "Dear Sir/Madam" register in Hebrew threads.
2. **Direct itemized pricing** — one line per item/size, in the body text (not always a PDF
   attachment — plenty of quotes are just typed inline). Format is usually:
   `<size/description> - <price> שח` or `<size> - <price> שח ליח'` (per unit) when there are multiples.
3. **VAT disclaimer** — almost every quote says **"המחירים לא כוללים מע"מ"** / **"לפני מע"מ"**
   (prices exclude VAT) or, less often, explicitly **"כולל מע"מ"** (VAT included) — this is stated
   every single time, never assumed.
4. **Sign-off** — "תודה" (thanks) + first name, or "בברכה, <name>" for slightly more formal/institutional
   threads.
5. **Auto-signature block** (Gmail signature, appears on nearly every outbound message):
   ```
   The Print House
   Hazerem 1, Tel Aviv
   Israel, 6816839
   tel: +972-3-6855362
   Open: Sunday - Thursday, 10:00 - 18:00
   Visit our website! www.theprinthouse.co.il
   ```
   A minority of messages (from `info@reastudio.co.il`, used for gallery/consignment admin) use a
   shorter variant: "Rea Photography House / www.theprinthouse.co.il / tel: 03-6855362 / fax: 03-6859411".
6. **Follow-up ask** — quotes almost always end with **"עדכני/עדכנו אותנו"** (let us know / update us)
   rather than a hard CTA — confirmation is conversational, not a formal "accept quote" button.

### Tone/register
- Informal, second-person Hebrew, heavy use of "אז ככה" (so, here's the thing) to open a price
  breakdown, "מה נשמע?" as a check-in opener, and "תודה!" / "מעולה" / "אחלה" / "סבבה" as casual
  acknowledgments.
- Emoji usage is light but real — 🙏, :), 🤍 — mostly from clients, occasionally echoed by staff.
- English is used fluidly with international/gallery/museum clients (Christie's, Braverman Gallery,
  Sommer Gallery, Marge Goldwater/Schusterman Foundation) — same brevity and directness carries over,
  e.g. *"Hi Ella, Thank you for your email. Below are the prices based on the specifications used for
  the last time you printed the Red Skies series with us in 2024."*
- Multi-item quotes are frequently just a numbered list with a **total line** at the end:
  *"סה"כ 9,568 ש"ח לפני מע"מ"* (Total: 9,568 NIS before VAT).
- Corrections/negotiations are handled matter-of-factly, no apologetic hedging — e.g. when a gallery
  disputed a price ("Wasn't the original price quote for 1200 each work and not 1500?"), staff simply
  re-sent the original itemized breakdown showing which item was which price, no discount was implied.

### Verbatim example excerpts (anonymized to first name / gallery name only)

**1. Simple two-line quote, walk-in style (scan + print):**
> "מה נשמע יפעת ? סריקה תעלה 250 שח, הדפסה לגודל איי 5 - 24 שח ליח'. המחירים לא כוללים מעמ. עדכני
> אותנו תודה רע"
> *(Hows it going Yifat? Scan costs 250 NIS, A5 print is 24 NIS/unit. Prices exclude VAT. Let us know, thanks, Rea)*

**2. Multi-option quote for a gallery client (glass upgrade tiers):**
> "מה נשמע ? אז ככה, לגבי מה שהוא הביא, לגודל הגדול - עם פרספקס רגיל - 3800 שח ליח' ואם רוצים עם
> זכוכית אנטירפלקטיבית זה יוצא 4800 שח ליח'. לגודל הקטן - או 1000 שח או 1500 שח (זכוכית רגילה לעומת
> אנטי). המחירים לפני מעמ עדכנו אותנו. ** המסגרת שלך - 550 שח + מעמ. תודה, רע"
> *(How's it going? So, for what he brought in — large size with regular acrylic is 3800/unit, with
> anti-reflective glass 4800/unit. Small size 1000 or 1500 depending on glass. Prices before VAT.
> ** your frame — 550 + VAT. Thanks, Rea)*

**3. Itemized institutional quote with running total (museum/curator client):**
> "1. 137X69 עם תוספת פספרטו של 10 ס"מ בכל צד עולה 3,969 ש"ח / 2. 29X69 עם תוספת של 5 ס"מ פספרטו
> בכל צד עולה 1,439 ש"ח / 3. 22X24 עם תוספת של 3 ס"מ פספרטו בכל צד עולה 826 ש"ח / 4. 101X69 עם
> תוספת של 10 ס"מ פספרטו בכל צד עולה 3,334 ש"ח. המחירים אינם כוללים מע"מ (הכל עם זכוכית מוזיאלית).
> סה"כ 9,568 ש"ח לפני מע"מ. תודה, גל"

**4. English quote to an international client, referencing order history:**
> "Hi Ella, Thank you for your email. Below are the prices based on the specifications used for the
> last time you printed the Red Skies series with us in 2024. Specifications: Floating frame, 3 mm
> white [Dibond]... "

**5. Repeat-client price lookup by memory, no re-measuring needed:**
> "כן, הנתונים שמורים אצלנו. מוזמנת לשלוח לי תמונה או מספר הזמנה כפי שמופיע על המדבקה שלנו מאחור"
> *(Yes, we keep the data on file. Feel free to send a photo or the order number as it appears on
> our sticker on the back [of the framed piece])*

### What's always included in a quote reply
- Itemized price per size/option (rarely a single lump sum for multi-item requests)
- Explicit VAT statement (included or excluded) — **never omitted**
- A closing ask for confirmation ("עדכני/עדכנו")
- No explicit "quote valid until" expiration date was observed in any sampled thread — validity
  period is informal/undocumented (see §5, new finding).
- No boilerplate "terms and conditions" footer beyond the standard signature block.

---

## 2. Order numbering & workflow facts

Two parallel numbering systems were observed:

- **W2P (web-to-print) order numbers**, e.g. `#27857` — 5-digit, generated by the website's online
  ordering system (subject line pattern: `<number> הזמנה <client name>`, e.g. "27857 הזמנה עדי
  מילר"). These come with auto emails: **"W2P - New Order Details: #NNNNN"** (internal, sent to staff)
  and **"W2P - ההזמנה שלך מהאתר The Print House התקבלה!"** (client-facing order confirmation).
- **POS/invoice order numbers**, e.g. `#55863` — a different, higher 5-digit range used for
  point-of-sale/in-person orders, with automated **"ההזמנה נכשלה: מס' NNNNN"** (payment failed) and
  presumably success emails when a card payment on an in-person order goes through or fails.
- Clients do reference the order number in follow-ups, and staff also reference **the number printed
  on a sticker on the back of the finished/framed piece** as the lookup key for repeat orders/history
  — this sticker-based lookup is a real, working practice for identifying a client's past specs
  without re-measuring or re-asking.
- Invoices are numbered separately (e.g. "חשבונית מס 53303", "חשבונית מס/קבלה 10959") and sent as
  their own follow-up email, distinct from the quote email — invoicing is a separate step, always
  triggered after the client confirms the quote ("שלחנו חשבונית לתשלום במייל נפרד" — "we sent the
  invoice for payment in a separate email" is a stock phrase).

### Order lifecycle (as observed across threads)
1. Client inquiry (email, sometimes referencing a prior in-person meeting/phone call) →
2. Itemized price reply (same day to ~2 business days) →
3. Client confirms ("מאשרת את ההצעה" / "מאשר") →
4. Staff replies "מכניסים לעבודה" (we're putting it into production) and asks for invoice details
   (billing name + ת.ז./ח.פ — Israeli ID/company number required for invoices) →
5. Invoice sent in a **separate email** →
6. Payment via bank transfer, credit card link (Cardcom-hosted payment page,
   `outgoing@out.cardcom.co.il`), or in-person card at pickup →
7. Automated "מוכנה לאיסוף" (ready for pickup) email once production is done →
8. Client picks up, or courier/self-arranged delivery is coordinated by reply-thread.

---

## 3. Operational policies & practices

- **Hours**: Sunday–Thursday, 10:00–18:00 (studio closed Fri/Sat, consistent with Israeli work week).
  Confirmed both in the signature block and in the automated pickup-ready email.
- **Location**: Hazerem 1, Tel Aviv-Yafo (workshop/pickup address); phone 03-6855362, fax 03-6859411.
- **Pickup vs. delivery**: Self-pickup from the studio is the default/preferred method
  ("איסוף מהסטודיו" appears constantly in W2P order metadata). Delivery is arranged ad hoc by
  courier (client's own courier, e.g. ShippingToGo, or staff bringing pieces directly to a gallery/
  hotel/client) — there is no fixed in-house delivery fleet; "יוני" appears repeatedly as the person
  who personally drives finished pieces to galleries/clients.
- **International shipping / export**: The studio works with a logistics/customs partner
  (BHM Logistics, `amit@bhm-logistics.com` / `airexport@bhm-logistics.com`) for international
  freight (DAP terms observed, ~3450 NIS quoted for one large shipment to Canada), and separately
  uses FedEx for smaller international parcels, including customs/duty invoices the studio pays
  directly. Damaged-shipment handling: when a shipment arrived damaged, the studio simply forwarded
  photos to the logistics contact and asked "מה אפשר לעשות?" (what can be done) — claims are handled
  informally through the forwarder, no documented formal claims process.
- **Payment methods**: Bank transfer (העברה בנקאית), credit card via a hosted payment link
  (Cardcom), or in-person card at pickup. Automated payment reminder emails exist
  ("תזכורת: תשלום עבור הזמנה מספר NNNNN") — a soft nudge template:
  *"הי שוב :) תזכורת קטנה לגבי התשלום עבור הזמנה NNNNN (סה"כ X ש"ח), בלחיצה כאן. דקה אחת וזה
  מאחוריך :) תודה!"* (Hey again :) small reminder about payment for order NNNNN (total X NIS),
  click here. One minute and it's behind you :) Thanks!) — these are automated/templated, not
  hand-written per client.
- **Deposits**: 50% deposit ("מקדמה") was explicitly used for at least one large hotel commission
  (~103k NIS total, 51,448 NIS balance due after 50% deposit). Deposit terms are negotiated case-by-
  case for large/institutional jobs, not a universal policy applied to every quote (most quotes shown
  have no deposit mentioned at all, payment is simply due before/at pickup).
- **Net terms**: Institutional/gallery clients sometimes get net terms on invoices — one client
  explicitly confirmed "שוטף + 30" (net 30) as their payment term after receiving an invoice; this
  was accepted without pushback.
- **Repeat/exhibition discounts**: Ad hoc percentage discounts are given, not fixed-rule: 10% off
  for a student's finals project ("אפשר לעשות לך 10% הנחה"), 5% off referenced by a returning
  exhibition client as their known rate ("ויש הנחה של 5 אחוז כמו בהזמנה לתערוכה?" — confirmed "כן"),
  and informal exhibition-related price breaks acknowledged directly ("המחירים היו זולים יותר בגלל
  שהייתה תערוכה ועשינו לך הנחה יפה" — prices were lower before because there was an exhibition and we
  gave you a nice discount, but that concession is not automatic for future one-off orders).
- **Rush/urgent orders**: No fixed rush fee was observed anywhere in the sample. Rush requests
  (very common — "דחוף", "צריך את זה דחוף") are handled case-by-case: sometimes accommodated
  ("ההדפסה תהיה מוכנה לאיסוף ביום ראשון:)"), sometimes declined honestly with a reason (e.g. paper
  out of stock until a specific date, offering an alternative paper stock instead), sometimes
  accommodated with an implicit "we'll make an effort" ("נעשה מאמץ").
- **Revisions/reprints/defects**: Handled without friction or blame language. When a gallery
  reported two defective/misprinted pieces in one email, staff simply agreed to reprint
  ("נעשה שוב, הדפסה ישירה על דיבונד ומבנה אחורי") and separately negotiated a small price
  adjustment on an unrelated line item in the same thread, without disputing the defect claim.
  There is no formal complaint/RMA process — defects are reported informally over email/WhatsApp
  (photos sent via WhatsApp were referenced multiple times as the norm for showing a problem) and
  resolved conversationally.
- **File/design handling**: Clients frequently send files via WeTransfer/JUMBOmail/Google Drive
  links rather than as email attachments. For institutional clients, the studio proactively asks
  about DPI/resolution and vector cut files when relevant (e.g. wall decal jobs needing a vector
  cutline separate from the full-bleed image file).
- **Repeat client history**: The studio keeps files/specs from past jobs and reuses them on request
  ("הקבצים שמורים אצלנו" — files are saved with us), including for limited-edition reprints, so a
  returning client doesn't need to resend files or re-specify framing choices — only needs to
  reference the file number or provide a photo of the sticker on the back of the original piece.
- **Turnaround time**: No universal fixed SLA. Verbally quoted per job when asked — examples
  observed: "עוד בערך עשרה ימים" (~10 days), "תוך שבועיים" (~2 weeks), "מוכן תוך כמה ימים" (a few
  days) for a simple reprint. Institutional/exhibition jobs get a specific promised date tied to
  the client's own deadline (e.g. "זה יהיה מוכן ל-11.8" matching an exhibition open date).
- **Gallery/artist consignment tracking ("Okapics")**: A separate internal workflow, not mentioned
  anywhere in `studio_knowledge.json`. When a W2P order for a recognized artist/gallery client is
  confirmed, the owner's `info@reastudio.co.il` address sends a short internal-style note (to
  `info@theprinthouse.co.il` itself, cc'ing "Amit / Adi") along the lines of: *"<Artist name> — Hey
  Amit / Adi, Order number NNNNN is confirmed. Please log in to Okapics and update the payment
  details—check if an invoice has been issued, if payment has been made, and collect payment as
  necessary."* This indicates the studio (or its gallery-facing side, "Rea Photography House") uses
  a third-party platform called **Okapics** to track consignment-style art sales and payment
  collection status, separate from the print-shop's own invoicing.

---

## 4. Client FAQ patterns

Recurring question types seen from clients, with how staff typically answered:

- **"Do you print on canvas?"** → Answered with a flat no: "אנחנו לא מדפיסים על קנבס" — the studio
  does not offer canvas printing (this is a hard capability boundary worth encoding).
- **"Do you install wallpaper/vinyl?"** → No, studio prints only; refers client to an external
  installer by name and phone number ("קובי, מדביק טפטים 0545799096") — a recurring outsourced-
  installer referral for wallpaper/decal jobs.
- **"What's the difference between regular and anti-reflective/museum glass, and price?"** →
  Recurring question; staff give a flat price delta per glazing tier ("400 שח" standard AR glass
  vs. "550 שח" for higher-UV-protection AR glass in one example) and note there's an additional
  ~200 NIS charge for opening/closing an existing frame to swap glass.
- **"Can I use the price/specs from my last order?"** → Yes — repeat clients routinely ask this and
  staff pull historical pricing/specs from memory or records rather than re-quoting from scratch.
- **"Do you have ready-made frame sizes, would that be cheaper?"** → Staff proactively offer this as
  a budget option to price-sensitive/student clients: "יש לך גם אופציה לקנות מסגרות מוכנות בגודל
  הזה. וזה ייצא לך הכי זול" (you also have the option to buy ready-made frames in this size, and
  that comes out cheapest — but the client then assembles it themselves).
- **"Is this quote actually final/should I get a formal PO?"** → Institutional buyers (museums,
  academic institutions) sometimes explicitly request a **formal written quote document** separate
  from the inline email price, in order to process a purchase order/vendor setup — the studio
  accommodates this on request but the default is the casual inline-email quote. Clients from
  institutions frequently need to supply a ת.ז./ח.פ (ID/company number) before an invoice can be
  issued.
- **"Can you frame in the exact same style as last time (from a photo of the back sticker)?"** →
  Handled as a straightforward repeat-order lookup, described above under order numbering.
- **International client "which glazing/finish should I use, what's the cost difference"** → Staff
  proactively simplify choices and quote clear price deltas per option (regular vs. anti-reflective
  vs. museum glass; direct-print-on-acrylic vs. laminate) rather than making the client guess.

---

## 5. New findings not already captured in studio_knowledge.json / business_rules.py

These are operational/communication facts discovered in the mailbox that are **not** currently
encoded anywhere in the pricing engine's knowledge files, and should be considered for merging in
if/when an automated quote-reply workflow is built:

1. **VAT phrasing is a hard requirement on every quote** — currently nothing in the pricing engine
   or studio_knowledge.json enforces or templates a VAT disclaimer, but 100% of sampled human quotes
   include one ("לא כולל מע"מ" / "כולל מע"מ"). An auto-reply generator must always state whether
   the number is pre- or post-VAT.
2. **No canvas printing** — a flat, unconditional capability limit ("אנחנו לא מדפיסים על קנבס")
   that isn't represented in the pricing catalog/business rules at all.
3. **Ready-made frame upsell/downsell option** — for budget-conscious clients, staff proactively
   suggest buying a ready-made frame in a standard size instead of custom framing, as the cheapest
   option. Not modeled in the pricing engine (which appears to only handle custom preset-based
   pricing).
4. **Glass-swap-only service and its added labor fee** — replacing glass in an *existing* frame
   (not a new build) is a distinct, common service ("תיקון מסגרת" / "החלפת זכוכית"), priced as glass
   cost + ~200 NIS open/close labor fee. This is a different SKU/scenario than a new frame build and
   doesn't appear to exist as a concept in the pricing engine.
5. **Sticker-based order lookup on the back of finished pieces** — an actual physical/operational
   mechanism for repeat-order identification, not documented anywhere.
6. **Okapics integration for gallery/artist consignment payment tracking** — a real, recurring
   internal workflow (distinct system from the studio's own invoicing) with no mention anywhere in
   the pricing app.
7. **Deposit policy is case-by-case, not systematic** — 50% deposits appear only for large
   institutional/hotel commissions; small-to-mid orders are paid in full before/at pickup. No
   deposit percentage or threshold is currently codified anywhere.
8. **Discounts are negotiated per-client/per-project, not rule-based** — 5%, 10%, and informal
   "exhibition discount" concessions were observed, all decided conversationally rather than from a
   fixed discount table. If an automated system offers discounts, it will need either a lookup of
   negotiated per-client rates or explicit human approval before quoting a discount.
9. **No fixed rush fee** — rush requests are accommodated or declined based on real capacity/stock
   constraints, never priced as a rush surcharge. An auto-reply system should not invent a rush fee
   unless the studio decides to formalize one.
10. **Quote validity period is undocumented/informal** — no "valid for N days" language was found in
    any sampled quote; if the new workflow wants to add an expiration, that would be a new policy,
    not a codification of an existing one.
11. **Standard signature block content** (address, hours, phone, website) is worth hard-coding into
    any auto-reply template verbatim, since it appears unchanged on virtually every outbound email.
12. **Institutional clients sometimes need a separate formal quote document** — the default is an
    inline-email price list, but on request (mainly museums/academic institutions) a distinct
    "official" quote document is produced — an auto-reply system should support an "upgrade to
    formal PDF quote" path, not assume email text is always sufficient.
