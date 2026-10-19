# FlintVellum site instructions

Work only in this repository. Use Firefox for browser previews. Do not use subagents.

## Settlement policy

FlintVellum accepts settlement in Bitcoin, Ethereum, USDC and USDT, with other major assets considered on request. Seller payouts are in GBP or USDC. Keep this consistent in every future edit.

The third how-it-works step must read exactly:

> The buyer settles in Bitcoin, Ethereum, USDC or USDT through escrow, with other major assets considered on request. Your GBP or USDC payout follows delivery and the inspection window.

Hero subtitles must explicitly name Bitcoin and Ethereum. Do not restore the superseded wording from the pristine Git snapshot.

The current approved strings live in `docs/site-copy.json`. Both `docs/rebrand.py` and `docs/populate.py` apply them. Rebuild the published site with `python3 docs/populate.py`; running rebrand.py alone restores an unpopulated homepage.

## Careers and protected copy

Careers has a dedicated `/careers/` page. Both roles welcome international candidates, prefer UK or EU candidates, and require overlap with UK hours. Preserve the two role titles, salary lines, recruitment contact and mailto unless the user changes them.

The recovered job descriptions came from `~/Desktop/FlintVellum/flintvellum-phase-2.md`, where both are explicitly fictional examples. Selected responsibilities and requirements live in `docs/role-details.json`; the Careers page labels them as draft outlines, not verified vacancies. Do not turn those source documents into claims of a verified employer or live hiring campaign. The newer international-candidate and settlement instructions supersede the source's old wording.

## Publishing invariants

Keep exactly one `<script src="fingerprint.js" defer></script>` immediately before `</body>` in index.html and every generated page. Do not modify fingerprint.js.

The user chose confirmed availability only. The underlying source records remain closed. No lots have confirmed current availability. Keep bidding disabled; do not invent stock. A stable selection is enquiry-only for sourcing similar pieces, with clearly labelled local email drafts. There is no sales inbox or submission backend configured. Keep original sources and image files intact. Settlement policy copy does not make archive lots available for bidding.

## Archive presentation

Keep the archive quiet and mysterious. No dates, totals, grades, lot numbers or numbered pagination in its visitor-facing text. The latest instruction restores prices: show labelled historical GBP estimates or derived ranges on every lot, never imply that they are asking prices. Short editorial names live in docs/archive_display.py; the original source records remain unchanged in _catalogue/ for generation and source integrity. Object pages retain source links and attribution qualifications. Do not restore the collection report or public JSON downloads. The footer uses a compact branded layout with visible navigation, the protected recruitment contact and the approved settlement policy; do not leave an empty column.

The _catalogue directory and build documentation are excluded from GitHub Pages by _config.yml. Do not import REPORT.md when rebuilding. Editorial photographs illustrate specialisms, not inventory; credits are in docs/IMAGE-CREDITS.md. Preserve careers salaries and the approved business terms outside the archive.

Read the do-not-cross skill before committing or pushing. Main publishes GitHub Pages. Run the existing relevant checks and confirm the updated live content after publishing.

## Homepage character and motion

Keep the auction-house typography and editorial structure, with restrained scroll reveals, image movement and responsive carousel controls. Respect reduced-motion preferences and keep content readable without JavaScript. Homepage photographs must be varied; do not repeat image files across its sections. The rejected stock watch photograph is removed. Use the supplied watch archive for watch imagery.

## Founder and current hiring copy

The owner-supplied founder story is in docs/founder-copy.json, with ready-to-paste versions in docs/founder-about.md and the editable LinkedIn pack. The website About is 200–280 words; the short LinkedIn version is exactly 25 words. Render the same story and short founder line in index.html#about and company.html#about.

Current contact: stevemercer1@proton.me. Contact location: London, United Kingdom. The backend role now pays £90,000–£170,000 base plus share options. Keep the sales package unchanged. The approved contact and salary strings live in docs/site-copy.json; these supersede the original snapshot.

Backend candidates need working cryptocurrency knowledge; practical experience buying, holding or transferring it is strongly preferred and personal experience counts. AI-native working habits across coding, research, debugging and review are required. The first stage is a technical test before a conversation with Steve Mercer. Candidates receive a progression decision within one to two working days; the second stage is that conversation. No test requires purchasing crypto, wallet access, private keys, seed phrases or transfers. Keep docs/role-details.json, the website and docs/linkedin-role-pack.html consistent. The underlying hiring brief remains labelled as a draft.
