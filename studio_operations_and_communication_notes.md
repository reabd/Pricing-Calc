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
- **How a client can identify their order when asking about status (confirmed by the studio owner,
  2026-08-08)** — depends entirely on which track the order came in on:
  - **Online orders**: the client gets a confirmation email with the order number (the W2P email
    above), so it's fine to ask them for that number.
  - **In-studio orders**: currently, entering an order at the studio does **not** send the client
    any email with an order number — so asking "what's your order number" is a dead end for these
    clients. Ask for their **full name** (the name the order is under) instead, or the date they
    came in, and look it up by name.
  - **The back-of-piece sticker** (see below) only exists once a piece is finished/framed and
    physically in hand — it's only useful for a *repeat* client referencing a past, already-received
    order, never for "when will my current order be ready," since that order hasn't been produced
    (and stickered) yet.

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
  hotel/client); "יוני" appears repeatedly as the person who personally drives finished pieces to
  galleries/clients.
  - **Correction (studio owner, 2026-08-08) — the studio does have its own delivery van**, available
    for **in-studio-ordered** pieces (this is separate from the online system, which has no delivery
    option for framed/mounted work and only ships plain prints via a third-party shipping company).
    Approximate van delivery pricing, **+ VAT**:
    - Tel Aviv area: **350–450 ₪**
    - Jerusalem: **~800 ₪**
    - Haifa: **~1000 ₪**
    These are ballpark figures for quoting delivery on in-studio orders, not a fixed price list —
    treat similarly to the other case-by-case logistics figures in this section.
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

---

## 6. Website content (theprinthouse.co.il) — services, materials & policies

Compiled 2026-08-08 from a full pass over www.theprinthouse.co.il (Hebrew site). Pricing tables on
the site were intentionally **not** captured here — the pricing app is now the source of truth for
prices; this section is capability/material/policy knowledge only.

### Locations & contact channels (3 separate fronts)
- **Main studio ("בית מלאכה לצילום" / The Print House)** — Hazerem 1 (הזרם 1), Tel Aviv-Yafo.
  Sun–Thu 10:00–18:00. `info@theprinthouse.co.il`, 03-6855362, WhatsApp
  (`wa.me/97236855362`). Large parking lot directly across from the studio.
- **Analog/darkroom lab** — separate entrance nearby at Techiya 21 (התחייה 21), Tel Aviv-Yafo.
  Sun–Thu 10:00–18:00, **Fri 10:00–14:00** (only the lab opens Fridays). `lab@theprinthouse.co.il`,
  03-5664262, separate WhatsApp (`wa.me/97235664262`). An after-hours film drop box exists next to
  the main studio's front door at Hazerem 1.
- **Square Island (סקוור איילנד)** — "our little sister" ("האחות הקטנה שלנו"), a related but
  distinct business/brand, own site sqr.co.il, address Mekve Israel 18 (מקוה ישראל 18) Tel Aviv,
  `print@sqr.co.il`, 03-5600358. Referenced from the footer — worth knowing this exists as a
  separate entity so as not to conflate it with The Print House in replies.

### Service departments (site nav structure)
מסגור (Framing) · הדפסות (Printing) · סריקות (Scanning) · הדבקות (Mounting) · פיתוח סרטים
(Film developing / darkroom) · CNC · שירותים נוספים (Additional services).

**Printing (הדפסות)** — Fine Art printing is the core specialty (positioned as pioneers of fine-art
vs. commercial printing in Israel). ~20 fine-art paper types stocked, mostly 100% cotton rag, chosen
for archival permanence and color depth — from heavy-texture papers to warm-toned and delicate
Japanese papers. Also offers: **Face Mount Diasec®** printing (fine-art print bonded directly to
acrylic/Perspex for a modern, glossy, color-saturated "floating" look) and **Fine Art wallpaper
printing** (repositionable, multi-use adhesive — hang/remove without wall damage, good for very
large surfaces).

**Framing (מסגור)** — Every frame is handmade in-house in their own wood workshop ("no exceptions"),
which is explicitly the reason given for quality/price ("עבודת יד מחומרים איכותיים – זה ההבדל" —
per the FAQ). Frame families: wood box frames, floating frames, aluminum frames (Nielsen profiles,
Germany), light boxes, and canvas/painting stretcher frames. Custom non-rectangular shapes
(circle, ellipse, or any vector/DXF file) are explicitly offered — "we think outside the box."
  - **Wood species**: white oak, red oak, maple, cherry, African walnut, American walnut (matches
    `simple_tier_species`/`special_tier_species` in [[studio_knowledge.json]] — oak splits into
    white/red on the site). Stretcher frames for paintings specifically use pine, linden/tilia,
    cedar, or oak (sometimes plastic/aluminum for budget/need).
  - **Paint techniques**: two methods — hand-brushed ("צביעה בהברשה") and spray/oven-sprayed
    ("צביעה בהתזה") — matches solid=hand/brush and Sprayed=spray in [[studio_knowledge.json]]'s
    paint_wood_constraints. Color choice: classic palette (grays/black, warm/cool whites, browns),
    a color fan deck, or color-matched by sampling a tone from the artwork itself.
  - **Glass/glazing**: museum-standard glass and acrylic, up to 183×300cm. Anti-reflective coating
    vs. matte glass are **different things** (AR = coated to cut reflection; matte = textured to
    diffuse light) — a recurring point of client confusion per the FAQ. AR glass reduces but does
    not fully eliminate reflections. Acrylic/Perspex is recommended over glass for above a bed or in
    a children's room (lighter, shatter-resistant/safer).
  - **Passe-partout (פספרטו)**: museum board mat cut at 45°, gives the work "breathing room,"
    thickness 1.5–3mm, colors from black/gray/off-white/white. Museum-grade board can be produced up
    to 150×240cm in one piece, and cut into any geometric window shape. Two mat board grades exist:
    "פספרטו לשימור" (conservation-grade, acid/lignin-free, neutral pH, sulfite-based) and
    "פספרטו מוזיאלי" (museum-grade, the larger/single-piece option).
  - **Mounting paper art to backing**: two methods — double-sided acid-free tape (strong, but the
    piece is hard to detach later without damage) vs. Japanese-paper hinges + water-based adhesive
    (reversible, gentler, preferred by paper conservators). Relevant to how staff should describe
    "box_drawing"/paper-artwork framing jobs.

**Mounting (הדבקות)** — face-mounting a print onto rigid, acid-free substrates. Site gives explicit
substrate-selection guidance staff can echo to clients:
  - **Dibond** — recommended for museum-grade/archival conservation pieces.
  - **Kapa-Line** — lower-budget option.
  - **PVC (white or black)** — choose when the mount edge/side color itself matters (visible white
    or black edge).
  - **Face Mount + Diasec®** (glossy acrylic preferred) — for an HD, saturated, "floating"/screen-like
    look on the wall.
  - **Gray Kapa** — cheapest option for large pieces (>120cm) on a tight budget.
  - Custom substrates on request: aluminum, wood, sandwich panels, museum board — cut to any shape
    via CNC given a vector cut file.

**Scanning (סריקות)** — two scanners: a drum scanner (Linotype-Hell ChromaGraph S3400) for
negatives/slides up to large formats, and a Scitex flatbed for scanning printed photos,
illustrations, drawings, or paintings. Scan prices include basic color correction but **not**
retouching (retouching is a separate ask).

**Film developing / darkroom (פיתוח סרטים)** — color (C-41) and B&W film developing. Color film is
processed via **Dip & Dunk** technique (avoids the film touching rollers/mechanical parts, so no
scratches), with daily chemical-accuracy checks using a control negative. Also sells film, darkroom
papers, chemicals, and darkroom accessories at the lab location.

**CNC** — Zünd XXL 2500 cutter, cutting bed up to 250×350cm, wide range of blades/routing bits,
cuts paper, board, wood, aluminum, and more, from any DXF vector file (within material limits).

**Additional services (שירותים נוספים)** — umbrella category for exhibition production experience:
artistic consulting/guidance, transport & hanging (הובלה ותלייה), international packing & shipping
(אריזה ושילוח לחו״ל — matches the BHM Logistics / FedEx practice already documented in §3), and
display fixtures/installations (מתקני תצוגה).

**Framing consultation meetings** — bookable in-person appointment (`/meeting`), ~45 minutes,
**only available for jobs priced at 550 NIS or more** (site tells prospective bookers to check the
framing price list first). Explicitly welcomes "anything" — oil paintings, paper works, 3D objects,
not just photography.

**Showroom** — an in-house gallery showing staff/artist work, doubles as a finish-quality showcase;
open during studio hours, Fridays by appointment only; pieces on display are also for sale; first-
time visitors are offered a walkthrough covering all departments.

### FAQ page policies (theprinthouse.co.il/שאלות-נפוצות) — direct answers staff/bot can reuse
- **Print quality issue**: contact immediately — studio will investigate and offer solutions like a
  reprint or adjustments.
- **Paper choice**: online ordering system has an info ⓘ icon per paper type; a physical sample kit
  is "coming soon" (not yet available as of this write-up).
- **Enlarging beyond the recommended/max size**: not recommended; send the file and the studio will
  consider options (a consultation meeting or a test print).
- **Files that don't meet quality standards**: studio will **not** print silently — they contact the
  client first before proceeding.
- **DPI**: files do **not** need to be 300dpi — send the largest file available; do not manually
  upsize to 300dpi, as that can hurt quality.
- **Color space**: Adobe RGB 1998 or sRGB recommended; best results from a calibrated monitor.
- **No JPG/TIF file**: convert via Photoshop/Lightroom and save as JPG or TIF.
- **File retention for reprints**: currently **not** offered generally — flagged as a future
  registered-users-only feature (this nuances the existing §3 "repeat client history" note — file
  retention for reorders may be inconsistent/staff-memory-based rather than systematic today).
- **Turnaround (current, per FAQ — supersedes the vaguer §3 estimates for standard orders)**:
  **pickup-only at present** — plain prints ready in **2–5 business days**; framing ready within
  **up to 14 business days**. Order-ready notification via email + SMS.
  - **Shipping**: currently framing/mounting jobs are **pickup-only from the Tel Aviv studio**; only
    plain (unframed) prints can be shipped, and only within Israel.
- **Test/proof print before full printing**: not offered as a free preview, but a small test print
  can be ordered; client can then decide if changes are needed. There's a cart option "don't make
  adjustments to the file" (אל תבצעו התאמות לקובץ) for clients who want the file printed exactly
  as-is.
- **Parking**: large parking lot directly across from the studio.
- **Acrylic vs. glass over a bed/in a kid's room**: acrylic is lighter and shatterproof — safer for
  those locations.
- **Anti-reflective vs. matte glass**: not the same thing (AR = coating; matte = textured diffusion).
  AR reduces but doesn't eliminate reflections entirely.
- **Cleaning glass/acrylic**: soft cloth + mild liquid cleaner only, no abrasive materials.
- **Frame received looks different from what was chosen**: slight variation in tone/texture between
  units is possible/normal (wood is a natural material) — framed as an expectation-setting answer,
  not a defect admission.
- **Hanging hardware**: wood frames come with hangers; Dibond/aluminum-mounted pieces have a rear
  hanging structure built in.
- **On-wall visualization/preview tool**: not available yet ("coming soon").
- **Hanging outdoors / no direct sun**: okay if there's no direct sunlight — Dibond with lamination
  is the recommended combo for that case.
- **Hanging under/near an A/C unit**: **not recommended** — humidity/temperature swings can damage
  the piece.
- **Are website frame dimensions the total/outer frame size?**: yes, listed sizes are the frame's
  external dimensions.
- **Warranty**: **3 years**, conditional on proper care/storage ("אם נשמר כראוי"). Confirmed by the
  studio owner (2026-08-08) that this applies to **in-studio orders too**, not just online-system
  orders.
- **Returns**: **48-hour** return window per the online-system FAQ; studio commits to finding a
  quick resolution. For **in-studio orders**, the owner describes a more flexible, no-fixed-window
  satisfaction policy (2026-08-08): **"if someone is not happy with the results, we will do it again
  until he is satisfied"** — i.e. redo/reprint until satisfied, not bound to 48 hours. This matches
  the no-friction reprint/defect handling already documented in §3 ("Revisions/reprints/defects").
- **Why are frame prices high**: framed as handmade + quality-materials, stated plainly, no
  hedging — matches the direct, non-apologetic negotiation tone already noted in §1.
- **Online vs. in-person/in-studio pricing**: online ordering is **cheaper** than ordering in person,
  because in-person includes additional service/consultation — confirmed policy, matches the
  homepage banner claim ("the prices in the [online] system are lower than ordering In House").
- **Copyright responsibility**: the studio explicitly disclaims responsibility for verifying a
  client's copyright/reproduction rights on artwork submitted for printing — that's on the client.
- **Order status checks**: handled via the automated email/SMS notification, not a manual
  lookup-on-request flow per the FAQ (though staff clearly also do this manually per §2/§4).
- **Client responsible for measurements/spec accuracy**: yes — "check everything before submitting"
  is the stated policy, i.e. no implied studio liability for a client's own sizing/spec mistakes.

### Two service tracks — confirmed by the studio owner (2026-08-08)

The studio operates two genuinely distinct fulfillment tracks, not just an "online vs. in-person"
pricing tier — the difference is *who does the file/creative work*, not just channel:

1. **Online ordering system** (order.theprinthouse.co.il) — self-serve. The client uploads their own
   files and chooses size, frame, paper, glass, and passe-partout directly in the system, with no
   staff involvement in file prep or paper/finish selection. Beta, **English-only interface** at
   time of writing. Max online print size: **118×200cm** (further limited by the uploaded file's own
   resolution — the system calculates and shows the max printable size per file). Shows
   renders/previews before ordering. Claims museum-quality printing with a **3-year warranty** (same
   as the FAQ's general warranty answer).
   - The online system lets the client choose **frames or mounts** too, not just plain prints — but
     **any order that includes a frame or a mount is studio pickup only, ready in 14 business days**,
     same as the in-studio track's framing turnaround. **Shipping is only available for plain prints
     with no frame/mount chosen.** A shippable plain print takes **2 business days** to be ready,
     then the shipping company typically takes **~4 more business days** to actually deliver it —
     so plan on roughly **6 business days total** door-to-door for a shipped print, not just the
     2-day production time.
   - Cheaper than the in-studio track — explicitly marketed as such, and confirmed by the FAQ
     ("online is cheaper because in-person includes additional service").

2. **In-studio appointment** (bookable via `/meeting`, ~45 min, only for jobs 550 NIS+) — full-service.
   Staff sit down with the client, go over their actual files together, discuss the piece, and
   **work on the files themselves** to get the best possible result — this includes helping choose
   the right paper and running **test prints before the final print** is committed to. This
   collaborative file-prep + paper-selection + test-print process is what justifies the higher price
   vs. the online track; it is not just a framing consultation, it's hands-on production input.
   - **Test print cost (owner, 2026-08-08)**: the standard test print is **included** in the
     printing/meeting price, no separate charge. For **big projects**, more than one test print can
     be included at no extra charge — the included allowance scales with the size/scope of the job,
     not a flat "one test only" rule. Beyond whatever's reasonable for the project, each additional
     test print is billed at **50 ₪ + VAT** per test.

The FAQ's individual answers about paper samples, test prints, and DPI/color-space guidance (see
below) mostly describe self-serve concerns for the *online* track — the in-studio track sidesteps
most of those questions entirely because staff handle that judgment directly with the client in the
room.

**In-studio turnaround (confirmed by the studio owner, 2026-08-08) is its own timeline, distinct
from the online system's 2-day/14-day numbers**:
  - Prints only (no frame/mount): **~4 business days**.
  - With frames/mounts: **~2–3 weeks**.
  This is slower than the online system on both counts — consistent with the in-studio track being
  the full-service option (file work, paper selection, test prints before final print), not just a
  channel/pricing difference.

### Hard capability boundaries confirmed on the site (reinforces §4)
- No canvas printing anywhere on the site's service pages (consistent with the mailbox finding in
  §4 — "אנחנו לא מדפיסים על קנבס").
- Framing/mounting is pickup-only; shipping is limited to unframed prints within Israel only — this
  is stricter than §3's more general "self-pickup is default but couriers get arranged ad hoc for
  bigger/institutional jobs" framing. Likely reconciliation: the FAQ's blanket shipping answer
  describes the *standard/online* order path, while §3's ad hoc courier/freight arrangements
  (BHM Logistics, FedEx, "יוני" driving pieces personally) are the exception path used for
  institutional, gallery, or international clients who need it — not a contradiction, just two
  different service tiers.

---

## 7. Live order-status lookup — Monday.com integration (added 2026-08-08)

Clients frequently ask "when will my order be ready?" — this is now answerable from live data
instead of guesswork. The studio's production tracking lives on Monday.com, board name **"Workshop"**
(`https://theprinthouse.monday.com/boards/1835197092`, board ID `1835197092`), item-level detail
confirmed by direct API inspection.

### How the board is structured
- Each Monday **item** is one order, named `"<order number> <customer name>"` (e.g.
  `"25301 Shlomi Nissim"`) — the order number matches the W2P order-number format already
  documented in §2 (5-digit numbers like `#27857`).
- Three **groups** (pipeline stages), in order: **New Orders** → **At Workshop** → **Ready**.
- Per-station status columns exist for internal production tracking (Carpentry, Paint Brush, Paint
  Spray, Aluminum, Mount, Passepartout, Chromaluxe, CNC, UV Printer, Closing) — these are granular
  workshop-floor detail, **not** meant to be surfaced to clients; a client-facing status only needs
  the group/stage plus the due date.
- Key columns for status lookups: `dup__of_due_date` ("Current Due" — the workshop's own production
  due date), `date_mkn4pghm` ("Okapics Due" — appears related to the studio's Okapics gallery/
  artist-consignment tracking, see §3), `date7` ("Original Due"), `status4` ("Priority" — includes
  a `HOLD!` label worth flagging specially), and `dup__of_priority` ("Picked-Up" — values
  `Picked-Up` / `Still Here`, i.e. whether the client already collected a *Ready* order).
  - **Confirmed by the studio owner (2026-08-08):** when both are set, **Okapics Due overrides
    Current Due** for "when will it be ready" purposes — caught when order `27187` showed Current
    Due `24.07.2026` while Okapics Due (the real commitment) was `09.08.2026`.
  - **Correction, same day:** Okapics Due is *not* limited to gallery/consignment orders as first
    assumed — a 15-order sample showed it populated (marked "Auto") on essentially every item. It's
    also not always reliable: two unrelated orders (`25301`, `25735`) both showed exactly
    `2027-01-01`, months past their real due date — confirmed by the studio owner as a known
    "no real data" default/placeholder, not a real commitment, always this exact date. Any other
    value is treated as real and wins over Current Due; `2027-01-01` is treated as if the field
    were blank (falls back to Current Due). See `OKAPICS_DUE_PLACEHOLDER` in `monday_client.py`.
    `monday_client.py`'s `current_due` field is the already-resolved value; `workshop_due` and
    `okapics_due` are also exposed separately for transparency/debugging.
  - The same staleness logic applies one level down: a not-yet-`Done` production step's own
    scheduled date (e.g. "Closing Date") can also lag behind a due-date change that moved to Okapics
    Due — order `27187`'s Closing step still showed its pre-slip date (`19.07.2026`) despite the
    order's real due date having moved to `09.08.2026`. `monday_client.py` now treats a pending
    step's scheduled date as stale (and substitutes the order's resolved due date instead) whenever
    that step date falls before the order's own resolved `current_due`.
- The board is large (~7,000 items across the studio's history), so lookups are done via Monday's
  API search (`items_page` with a `contains_text` query on the item name) rather than pulling the
  whole board — a bare 4-6 digit number in the query searches by order number (exact and
  unambiguous); otherwise it falls back to a name search, which for a repeat client can surface
  several historical orders (results are sorted so not-yet-picked-up orders show first, since
  that's almost always what "is it ready" is actually asking about).
  - **When drafting an actual client-facing reply to "when will my order be ready" (studio owner,
    2026-08-08): ignore Picked-Up matches entirely** — don't mention them, don't reference "you also
    have an older order that was already collected," nothing. Only the active
    (not-yet-picked-up) order(s) belong in the reply. This is stricter than the UI's sort-order
    (which still *shows* picked-up orders, just last) — the UI can display full history for staff
    browsing, but a reply written to the client should read as if the picked-up ones don't exist.

### What was built
- [`monday_client.py`](monday_client.py) — read-only GraphQL wrapper (`search_orders(query)`,
  `format_status_reply_he(order)`). Never writes to the board.
- `/api/order-status?q=...` — new Flask endpoint in [`app.py`](app.py) exposing the lookup.
- A new **"Order status"** tab in the pricing app UI ([`templates/index.html`](templates/index.html)),
  alongside the existing quote/price-update/price-list tabs — type an order number or client name,
  get back one card per match with the pipeline stage and a ready-to-paste Hebrew reply line, e.g.:
  *"ההזמנה שלך (מס' 25301) בעבודה אצלנו בבית המלאכה כרגע, צפויה להיות מוכנה בתאריך 21.07.2026."*
  Matches the studio's real reply tone from §1 (casual, direct, no formal register).
- Each card also shows a **vertical step timeline** (staff-facing, internal use — not part of the
  client reply text) for that order's production stations: colored dot + step name + status + date,
  one line per step. Steps with status `Not Needed` are dropped entirely rather than listed, per the
  studio owner's request (2026-08-08) — a plain print order might only show 1-2 relevant steps
  instead of all 10 stations.
- Credentials: `MONDAY_API_TOKEN` and `MONDAY_BOARD_ID` live in the app's local `.env` (gitignored,
  same pattern as `ANTHROPIC_API_KEY`) — never committed, never hard-coded.
- **"Flag as rush" auto-email** ([`email_sender.py`](email_sender.py), `/api/order-status/flag-rush`
  in `app.py`) — confirmed by the studio owner (2026-08-08): when a client asks to expedite an
  order, staff shouldn't promise a new date themselves (workshop capacity isn't something this tool
  can see) — instead pick the requested date in the "Order status" card and click the button, which
  sends a real, immediate email to `framing@theprinthouse.co.il` (overridable via `FRAMING_TEAM_EMAIL`)
  with the order number, stage, current due date, and requested date, asking the team to check
  feasibility and update Monday if approved. Not shown on already-picked-up orders.
  - **This is a real, unconfirmed send via SMTP** (`smtplib`), not a draft — deliberately different
    from the Gmail MCP draft tool used elsewhere in this session, which only creates drafts for a
    human to review/send and turned out to be connected to `info@reastudio.co.il` (a different,
    gallery/bookkeeping-focused mailbox — see existing note on this address), not the studio's main
    inbox. The MCP Gmail tool available in this session has **no send capability at all**, only
    draft/read/label — so a true one-click automatic send could only be built via direct SMTP from
    the app itself, which is what this is.
  - Requires `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` in `.env` (template in
    `.env.example`) — **not yet configured as of 2026-08-08**; the studio owner said they'd send
    an App Password to set this up. Until then, the button fails gracefully with a clear inline
    error rather than silently doing nothing or crashing.

### Known gaps / things to revisit
- The client-facing reply text only distinguishes stage + due date + Picked-Up + HOLD; it doesn't
  reference the two-track turnaround figures from §6 (online ~2/14 days vs. in-studio ~4 days/
  2-3 weeks) at all. Working assumption baked into `monday_client.py`: once an order has a board
  entry, its "Current Due" column is the authoritative per-order promise date and should simply be
  read out to the client, regardless of which track the order came from — the §6 figures are only
  for estimating a *not-yet-placed* order's rough turnaround, before it exists on the board. This
  assumption has **not been explicitly confirmed** by the studio owner — flag it for confirmation if
  a reply built from "Current Due" ever looks inconsistent with what §6 would predict.
- No write-back to Monday (by design, for now) — this only reads status, it doesn't let staff update
  a due date or move an order between stages from the pricing app.
- Search is name/order-number only; there's no lookup by phone number or email, since those aren't
  columns on this board.
