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

## Publishing invariants

Keep exactly one `<script src="fingerprint.js" defer></script>` immediately before `</body>` in index.html and every generated page. Do not modify fingerprint.js.

All 250 archive lots remain closed, with their original sources, images and qualifications. Settlement policy copy does not make archive lots available for bidding.

Read the do-not-cross skill before committing or pushing. Main publishes GitHub Pages. Run the existing relevant checks and confirm the updated live content after publishing.
