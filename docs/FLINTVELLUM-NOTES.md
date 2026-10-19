# FlintVellum site

The captured Christie’s layout, typography, header and footer remain, with FlintVellum’s supplied branding. Online-sourced watch, trading-card and cinema photography now fills the hero and specialism sections. Credits and source links are in IMAGE-CREDITS.md. These editorial photographs illustrate collecting categories, not available inventory.

The archive has short editorial names and no dates, prices, totals, grades, lot numbers or numbered page controls. The former report page is now a quiet invitation into the collection. The third footer column is empty. The collection report and public data-download paths have been removed.

The original 250 closed records and their source evidence remain unchanged in _catalogue/, excluded from GitHub Pages by _config.yml. All 947 original lot photographs remain under img/. Each object page keeps its gallery, original catalogue link, closed status and source-attribution qualification. Nothing in the archive is offered for bidding or represented as independently inspected by FlintVellum. Full source descriptions, condition, provenance, corrections and price evidence remain in the build records.

The catalogue supports keyword, category, maker and saved-object filters, with Previous and Next controls. Saved selections stay in the visitor’s browser. Galleries support enlarged views, keyboard navigation and touch. Account registration, live bidding and payments have no backend in this static site.

Careers has a dedicated page at careers/. Both roles prefer UK or EU candidates, welcome international candidates and require UK-hours overlap. Their titles, salary lines, recruitment contact and mailto are unchanged.

The full job descriptions were recovered from ~/Desktop/FlintVellum/flintvellum-phase-2.md. That source and PHASE-1.md explicitly identify the employer and vacancies as fictional examples. The website therefore labels the expanded responsibilities and requirements as draft role outlines, with proposed pay packages. Public copy is stored in role-details.json; no private assessment answers or installer material were imported.

Approved settlement copy lives in site-copy.json and AGENTS.md. Buyers settle in Bitcoin, Ethereum, USDC or USDT through escrow, with other major assets considered on request. Seller payouts are in GBP or USDC. The homepage and company page share the exact approved consignment step. Business terms and salaries outside the archive keep their figures.

FlintVellum’s fingerprint.js is unchanged, with exactly one hook immediately before the closing body tag on every generated page. The original publisher’s trackers remain detached.

Rebuild with `python3 docs/populate.py`. Import replacement supplied records with `python3 docs/populate.py ../auction-data`; the importer does not copy the report. This first runs rebrand.py against the saved christies-pristine tag, then applies the current content. Do not run rebrand.py alone for publishing.

`python3 docs/verify-data.py` checks every generated route, local asset, original photograph hash, attribution, protected copy and analytics hook. `node docs/verify.cjs` exercises the site in Firefox, including search, filters, saving, galleries, navigation and narrow layouts. The `--company` mode checks the careers and settlement routes. Screenshots stay in ignored docs/verify-shots/.
