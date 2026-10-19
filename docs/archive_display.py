"""Editorial display names. Original catalogue records remain unchanged."""
import re

OVERRIDES={
 'w-0102':'Richard Mille · The Beast',
 'w-0103':'De Bethune JPS',
 'm-0054':'Allen Iverson · Philadelphia jersey',
 'w-0005':'David Candaux Embème Prototype',
 'w-0008':'Genus Dragon',
 'w-0010':'H. Moser & Cie x MB&F Endeavour Cylindrical Tourbillon',
 'w-0019':'Maîtres du Temps Reveal',
 'w-0035':'Grand Seiko wristwatch',
 'w-0040':'MB&F Space Pirate',
 'w-0041':'Omega Speedmaster Professional Moonwatch',
 'w-0062':'Omega Speedmaster Moonwatch Apollo-Soyuz',
 'w-0071':'Grand Seiko wristwatch',
 'w-0073':'Panerai Luminor Submersible Bronzo',
 'w-0074':'Patek Philippe Calatrava Cortina Watch',
 'w-0076':'Richard Mille wristwatch',
 'w-0098':'Omega wristwatch',
 'c-0001':'Bowman Chrome University Superfractor Paige Bueckers',
 'c-0002':'Topsun Blue Back Charizard',
 'c-0010':'Fleer Brilliants Gold Jason Kidd',
 'c-0011':'Topps MLB MVP Collection Foilfractor Shohei Ohtani',
 'c-0022':'Pokémon EX Delta Species Reverse Holo Latias & Latios',
 'c-0038':'Pokémon Japanese Corporate History Beta Chansey',
 'c-0049':'Playoff Contenders Gold Proof Tom Brady',
 'c-0051':'Pokémon Japanese Battle Carnival Victory Cup',
 'c-0053':'Pokémon Japanese XY Promo M Sachiko EX',
 'c-0064':'Pokémon Base Set Shadowless Holo Charizard',
 'c-0066':'Upper Deck The Cup Exquisite Tribute Wayne Gretzky',
 'c-0068':'Flair Showcase Legacy Collection Kobe Bryant',
 'c-0073':'Pokémon POP Series Umbreon Gold Star',
 'c-0086':'Pokémon POP Series Umbreon Gold Star',
 'c-0089':'Topps NBA Kobe Bryant',
 'm-0001':'Herbert Wilcox’s National Film Award',
 'm-0002':'Gladiator II · Glyceo hero costume',
 'm-0003':'Diamonds Are Forever · Poster and Ian Fleming novel',
 'm-0004':'The Living Daylights · Cello case sled',
 'm-0011':'No Time to Die · Barton Perreira Norton sunglasses',
 'm-0012':'No Time to Die · Globe-Trotter luggage',
 'm-0013':'No Time to Die · Moscot glasses',
 'm-0015':'New England Patriots · Team-signed football',
 'm-0032':'Super Bowl · Championship-clinching touchdown football',
 'm-0037':'Super Bowl · Signed football',
 'm-0045':'Allen Iverson · Philadelphia jersey',
 'm-0048':'Karl-Anthony Towns · Minnesota Timberwolves jersey',
 'm-0050':'Tom Brady · New England Patriots football',
}

def title(record):
    if record['id'] in OVERRIDES:return OVERRIDES[record['id']]
    text=record['title']
    if record['category']=='watches':
        text=re.sub(r'\s+Ref\..*',' wristwatch',text)
    if record['category']=='cards':
        text=re.sub(r'\s+(?:PSA|CGC|BGS|SGC)\b.*','',text)
        text=re.sub(r'\b(?:Series \d+|\d+st Edition|\d+th Edition)\b','',text)
        text=re.sub(r'#\S+|\b(?:ROOKIE|PROSPECT|AUTO|DNA|RC|PATCH|TAG|MBA)\b','',text)
        text=text.replace('Pokemon','Pokémon')
    text=re.sub(r'\S*\d\S*','',text)
    text=re.sub(r'\(\s*\)|[“\"]\s*[”\"]','',text)
    text=re.sub(r'\s+',' ',text).strip(' ·,-')
    if record['category']=='memorabilia' and text.upper()==text:text=text.title()
    return text if text!=record['maker'] else text+' wristwatch'
