# FlintVellum clone

The homepage is a static mirror of https://www.christies.com/ captured on 19 October 2026, using the framer-clone skill's mirror, detach and staticise approach. Its original HTML, component styles, Arizona fonts, photographs, video and header/footer markup are stored locally. The source is not a Framer site, so the scripts were adapted to its rendered components and shadow roots.

The new header and footer use the supplied FV monogram and tracked wordmark from ~/Desktop/FlintVellum-logos/. DM Serif Display is loaded for the wordmark. The original FlintVellum company copy, consignment process, categories, roles and salary lines are preserved in company.html. About, Careers and consignment links open that page. The original recruitment contact and mailto are also retained in the homepage footer.

The mirrored auction lots, estimates, articles, events and imagery remain Christie’s source content. They are not represented as FlintVellum inventory. Their links still open the original destination pages. This is a clone of the public homepage, not a copy of every Christie’s destination page or its private systems.

Local interactions cover the hero and catalogue carousels, mobile swiping, dropdown navigation, mobile menu, auction filters, saved follows, catalogue search and footer accordions. Saved follows stay in the visitor's browser. Sign-in, newsletter subscriptions and bidding need real services to become FlintVellum features; the interface identifies the source service instead of collecting credentials or claiming a successful transaction.

The source publisher's trackers and cookie manager were detached. Empty personalised advertising slots were removed. FlintVellum's existing fingerprint.js is unchanged and its hook remains immediately before the closing body tag in both pages.

The photographic and font files came from the source's public asset URLs, recorded in clone.json. No rights or licences have been established for FlintVellum; confirm permission before using these source assets commercially. No new auction results, estimates, dates or business claims were invented.

Rebuild branding with `python3 docs/rebrand.py`. It starts from the local `christies-pristine` Git tag. `docs/mirror.py` can reconstruct the original mirror when the ignored .mirror-cache capture files are available. `node docs/verify.cjs` uses Firefox and writes local screenshots under ignored docs/verify-shots/.
