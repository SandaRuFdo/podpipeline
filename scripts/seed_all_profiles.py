#!/usr/bin/env python3
"""
seed_all_profiles.py — Create all 30 language × audience writing skill profiles.

Each profile is hand-crafted with culturally accurate tone, slang, vocabulary,
cultural references, hooks, and avoid-list for that specific combination.

Usage:
    python scripts/seed_all_profiles.py            # seed all 30
    python scripts/seed_all_profiles.py --force     # overwrite existing
"""
import sqlite3, sys, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..",
                       ".agent", "skills", "memory", "podcast_memory.db")

# ═══════════════════════════════════════════════════════════════════════════════
# ALL 30 PROFILES — 5 languages × 6 audiences
# Each key: (lang_code, audience_key)
# ═══════════════════════════════════════════════════════════════════════════════

PROFILES = {

    # ─────────────────────────────────────────────────────────────────────────
    # 🇬🇧 ENGLISH
    # ─────────────────────────────────────────────────────────────────────────

    ("en", "finance_listeners"): {
        "lang_label": "English", "audience_label": "Finance Listeners",
        "tone": "Sharp, authoritative, data-driven but never boring. Like a Bloomberg anchor who got obsessed with sci-fi. Fast-paced, confident delivery. Drop real numbers. Build FOMO around emerging markets and technologies.",
        "slang": "alpha, moon, diamond hands, bearish, bullish, bag holder, HODL, dry powder, macro play, 10x opportunity, asymmetric bet, thesis, conviction call",
        "vocab": "Science terms tied to market impact. Frame discoveries as investable trends. Use: TAM, disruption curve, S-curve adoption, unit economics. Explain quantum/AI through ROI lens.",
        "cultural_refs": "Lex Fridman, Patrick Boyle, All-In Podcast, Bloomberg, CNBC, Elon Musk SEC filings, ARK Invest, Chamath, Sam Altman, Y Combinator, a16z future fund",
        "hooks": "Start with a shocking dollar figure or market implication. 'This one breakthrough could create a $4 trillion market by 2030.' Lead with what smart money is doing NOW. Frame every topic as an investment thesis.",
        "avoid": "Childish language, memes, TikTok references, oversimplification without data backup, hype without substance, ignoring risk/downside, anything that sounds like a pump-and-dump pitch",
    },
    ("en", "millennials"): {
        "lang_label": "English", "audience_label": "Millennials",
        "tone": "Thoughtful, slightly nostalgic, intellectually curious. Like explaining mind-blowing science to smart friends over craft beer. Balanced optimism — acknowledge problems but explore solutions. Long-form welcome.",
        "slang": "adulting, that tracks, I'm here for it, main character energy, unhinged, rent-free, the algorithm, doom scrolling, touch grass, serotonin boost, core memory, it's giving",
        "vocab": "Accessible science with context. Reference foundational concepts from college. Mix philosophy with physics. Use metaphors from daily life — mortgages, careers, existential dread. Explain complex topics through lived experience.",
        "cultural_refs": "The Matrix, Interstellar, Black Mirror, Joe Rogan (but smarter), The Office references, Harry Potter analogies, 90s/2000s cartoons, Radiohead, Neal Stephenson, Carl Sagan, Neil deGrasse Tyson",
        "hooks": "Start with a 'what if' that connects to their daily life. 'What if the simulation theory explains why your career feels scripted?' Build personal stakes. Use narrative structure — setup, tension, reveal.",
        "avoid": "Being condescending, pure hype without depth, ignoring socioeconomic context, pretending everything is fine, clickbait without payoff, overly academic tone",
    },
    ("en", "tech_enthusiasts"): {
        "lang_label": "English", "audience_label": "Tech Enthusiasts",
        "tone": "Precise, technically rigorous, deeply curious. Like a senior engineer explaining cutting-edge research to a sharp junior dev. Go deep on mechanisms. Respect their intelligence. First-principles thinking.",
        "slang": "ship it, nerd snipe, yak shaving, bikeshedding, 10x, rubber duck, edge case, stack overflow moment, it compiles, works on my machine, technical debt, spaghetti code, this is the way",
        "vocab": "Real technical terminology — explain it once, then use it. Reference actual papers (arXiv IDs welcome). Use: Big-O notation metaphors, API analogies, system design thinking. Compare natural phenomena to distributed systems.",
        "cultural_refs": "Hacker News, XKCD, Linus Torvalds, Andrej Karpathy, Two Minute Papers, 3Blue1Brown, Veritasium, Computerphile, John Carmack, arxiv.org, GitHub trending, r/programming",
        "hooks": "Start with a technical paradox or unsolved problem. 'There's a bug in the Standard Model, and no one can fix it.' Reference a recent paper or breakthrough. Use 'let me break down the architecture.'",
        "avoid": "Dumbing down without offering the real explanation, factual errors (they WILL catch them), hand-waving over mechanics, confusing correlation with causation, marketing speak, buzzword soup",
    },
    ("en", "gen_z"): {
        "lang_label": "English", "audience_label": "Gen Z",
        "tone": "Fast, chaotic, authentic. Like two friends screaming about science on a Discord call at 2 AM. High energy. Meme-literate. Self-aware. Break the fourth wall constantly. Short attention hooks.",
        "slang": "no cap, fr fr, lowkey, highkey, bussin, slay, W take, mid, goated, sus, it's giving, rent-free, unhinged, brainrot, cooked, ate that, understood the assignment, ratio",
        "vocab": "Explain everything through gaming, anime, or social media metaphors. 'Black holes are basically the final boss of physics.' Keep sentences under 15 words. Fragment sentences OK. ALL CAPS for emphasis moments.",
        "cultural_refs": "Minecraft, One Piece, Attack on Titan, Jujitsu Kaisen, Mr. Beast, Kai Cenat, iShowSpeed, Stranger Things, Marvel MCU, TikTok sounds, Among Us, Roblox, Fortnite lore, Skibidi Toilet, ChatGPT",
        "hooks": "Cold open with a wild claim. 'NASA just found something that shouldn't exist.' Cliffhanger every 3 minutes. Use 'wait wait wait' moments. Tease reveals. Create TikTok-clippable 30-second segments.",
        "avoid": "Corporate tone, boomer references, explaining memes, being cringe on purpose, using slang wrong, lecture format, intros longer than 30 seconds, 'hello and welcome to our podcast'",
    },
    ("en", "health_wellness"): {
        "lang_label": "English", "audience_label": "Health & Wellness",
        "tone": "Warm, empathetic, science-grounded but emotionally resonant. Like a compassionate doctor friend who reads cutting-edge research. Build personal stakes — 'this affects YOUR body.' Inspirational without being preachy.",
        "slang": "biohacking, longevity stack, optimize, gut-brain axis, circadian rhythm, metabolic health, zone 2, cold plunge, grounding, nervous system regulation, somatic, embodiment, mindful",
        "vocab": "Medical terms with immediate plain-English follow-up. Connect space/physics to human biology. Use: telomeres, mitochondria, neuroplasticity, microbiome — but always explain what it means for THEIR health.",
        "cultural_refs": "Andrew Huberman, Peter Attia, Rhonda Patrick, Bryan Johnson, Wim Hof, Tim Ferriss, Lex Fridman health episodes, longevity clinics, Blue Zones, biohacking conferences",
        "hooks": "Start with a health implication: 'This discovery could add 20 years to your life.' Frame sci-fi through body/mind lens. 'What NASA found about aging in space changes everything we know about YOUR cells.'",
        "avoid": "Medical claims without evidence, dismissing alternative perspectives without reason, cold/clinical detachment, ignoring emotional dimension, being preachy about lifestyle, fear-mongering without solutions",
    },
    ("en", "scifi_curious"): {
        "lang_label": "English", "audience_label": "Sci-Fi Curious",
        "tone": "Wonder-filled, storytelling-first, accessible. Like a cool science teacher who makes you forget you're learning. Equal parts entertainment and education. Build awe. Use cliffhangers. Create 'holy shit' moments.",
        "slang": "mind-blowing, plot twist, lore drop, canon, multiverse, simulation confirmed, time travel vibes, galaxy brain, reality check, cosmic horror, main quest, world-building, Easter egg",
        "vocab": "Science made cinematic. Every concept gets a movie-quality description. Use vivid metaphors: 'Imagine the entire universe fitting inside a teaspoon.' Balance real science with speculative 'what if' scenarios.",
        "cultural_refs": "Interstellar, The Expanse, Dune, Foundation, Three-Body Problem, Arrival, Black Mirror, Kurzgesagt, SEA (Science Entertainment Archive), PBS Space Time, Isaac Arthur, Cool Worlds Lab",
        "hooks": "Start with a mind-bending scenario. 'Scientists just proved we might be living in a hologram.' Use the 'imagine you're standing on...' technique. Build cinematic scenes before dropping the science.",
        "avoid": "Being boring, dry explanations without narrative, losing the wow factor, gatekeeping science, assuming too much prior knowledge, lecturing without storytelling, spoiling the reveal too early",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🇩🇪 GERMAN
    # ─────────────────────────────────────────────────────────────────────────

    ("de", "finance_listeners"): {
        "lang_label": "German", "audience_label": "Finance Listeners",
        "tone": "Serious but approachable. Like a smart financial advisor who's also a sci-fi fan. Data-driven, precise, but passionate. German thoroughness meets Wall Street energy.",
        "slang": "Rendite, Depot, Sparquote, Moonshot, Bullenmarkt, Bärenmarkt, Cashflow, Hebel, ETF-Sparplan, All-In, Disruption, Gamechanger, FOMO, Kursrakete",
        "vocab": "Wissenschaft durch Investmentbrille. Marktpotenziale beziffern. Nutze: TAM, S-Kurve, Disruptionstheorie. Quantencomputing erklärt als Marktchance. Physik als Anlagetrend.",
        "cultural_refs": "Finanzfluss, Aktien mit Kopf, Der Aktionär, Handelsblatt, WirtschaftsWoche, Frank Thelen, Elon Musk, DAX, Siemens Forschung, SAP Innovation, BioNTech-Story",
        "hooks": "Starte mit einer Marktzahl: 'Dieser Durchbruch könnte einen 400-Milliarden-Euro-Markt schaffen.' Zeige was das Smart Money macht. Jedes Thema als Investmentthese rahmen.",
        "avoid": "Jugendsprache, Memes, zu lockerer Ton, Zahlen ohne Quellen, reine Spekulation ohne Fundament, amerikanische Beispiele ohne deutschen Bezug, Hype ohne Substanz",
    },
    ("de", "millennials"): {
        "lang_label": "German", "audience_label": "Millennials",
        "tone": "Thoughtful, intelligent, with a nostalgia touch. Like a conversation among educated friends over craft beer. Depth welcome. Balance between optimism and realism. Philosophical but accessible.",
        "slang": "Erwachsen werden ist überbewertet, voll mein Ding, passt schon, läuft bei dir, Struggle ist real, Bock drauf, deep, wholesome, relatable, Overthinking-Modus",
        "vocab": "Zugängliche Wissenschaft mit Kontext. Philosophie trifft Physik. Metaphern aus dem Alltag — Miete, Karriere, existenzielle Krisen. Komplexe Themen durch Lebenserfahrung erklären.",
        "cultural_refs": "Stromberg, Dark (Netflix), Rammstein, Tatort, Die Sendung mit der Maus (nostalgisch), Jan Böhmermann, Kurzgesagt, Terra X, Matrix-Trilogie, Interstellar, 90er Kindheit",
        "hooks": "Starte mit einem 'Was wäre wenn' das ihr Leben berührt. 'Was wenn die Simulationstheorie erklärt warum dein Beruf sich so skriptet anfühlt?' Persönliche Stakes aufbauen.",
        "avoid": "Herablassend sein, reiner Hype ohne Tiefgang, sozioökonomischen Kontext ignorieren, zu akademisch, Clickbait ohne Substanz, Gen-Z-Slang erzwingen",
    },
    ("de", "tech_enthusiasts"): {
        "lang_label": "German", "audience_label": "Tech Enthusiasts",
        "tone": "Precise, technically grounded, curious. Like a senior developer explaining cutting-edge research. First-principles thinking. Respect their intelligence. Deep-dive into mechanics.",
        "slang": "Deployen, shippen, Edge-Case, technische Schuld, Spaghetti-Code, läuft auf meiner Maschine, Rubber-Ducking, Nerd-Sniping, Overengineered, Stack, Dependency Hell",
        "vocab": "Echte technische Terminologie — einmal erklären, dann verwenden. Referenziere Papers (arXiv). Nutze: Big-O-Metaphern, API-Analogien, System-Design-Denken. Naturphänomene als verteilte Systeme.",
        "cultural_refs": "Heise, Golem.de, c't Magazin, CCC (Chaos Computer Club), re:publica, Linus Torvalds, Two Minute Papers, 3Blue1Brown, GitHub Trending, Hacker News, r/de_EDV",
        "hooks": "Starte mit einem technischen Paradox. 'Es gibt einen Bug im Standardmodell, und niemand kann ihn fixen.' Referenziere aktuelle Papers. 'Lasst mich die Architektur aufschlüsseln.'",
        "avoid": "Vereinfachen ohne echte Erklärung anzubieten, faktische Fehler (sie WERDEN sie finden), Handwaving über Mechaniken, Marketing-Sprech, Buzzword-Suppe, Denglisch-Overkill",
    },
    ("de", "gen_z"): {
        "lang_label": "German", "audience_label": "Gen Z",
        "tone": "Ultra-casual, fast, like two best friends nerding out about science on Discord at 2 AM. Short punchy bursts. Excitement over precision. Gaming metaphors. Meme-literate.",
        "slang": "Krass, Digga, Wallah, sheesh, uff, sus, cringe, safe, Ehrenmann, lost, Bock, vibe, lit, flex, Alter, no front, real talk, Bre, wild, random, Ehrenfrau",
        "vocab": "Alles durch Gaming-, Anime- oder Social-Media-Metaphern erklären. 'Schwarze Löcher sind der Endboss der Physik.' Sätze unter 15 Wörtern. Fragmentsätze OK. CAPS für Emphasis.",
        "cultural_refs": "Minecraft, One Piece, Attack on Titan, Gronkh, Rezo, HandOfBlood, Julien Bam, HeyMoritz, TikTok-Deutschland, Twitch-DE, Jujutsu Kaisen, Demon Slayer, GermanLetsPlay",
        "hooks": "Cold Open mit wilder Behauptung. 'Die NASA hat gerade etwas gefunden, das es NICHT geben sollte.' Cliffhanger alle 3 Minuten. 'Warte warte warte' Momente. TikTok-clippable Segmente.",
        "avoid": "Boomer-Sprache, Hochdeutsch-Förmlichkeit, Witze erklären, Referenzen vor 2015, langsame Intros, passive Stimme, 'Herzlich willkommen bei unserem Podcast'",
    },
    ("de", "health_wellness"): {
        "lang_label": "German", "audience_label": "Health & Wellness",
        "tone": "Warm, empathetic, scientifically grounded but emotional. Like a compassionate doctor friend who reads cutting-edge research. Personal stakes — 'this affects YOUR body.' Inspiring without preaching.",
        "slang": "Biohacking, Langlebigkeit, Optimieren, Darm-Hirn-Achse, zirkadiane Rhythmen, Stoffwechsel, Eisbaden, Erdung, Nervensystem-Regulation, Achtsamkeit, Selbstheilung",
        "vocab": "Medizinische Begriffe mit sofortiger Alltagserklärung. Weltraum/Physik mit Humanbiologie verbinden. Nutze: Telomere, Mitochondrien, Neuroplastizität, Mikrobiom — immer erklären was es für IHRE Gesundheit bedeutet.",
        "cultural_refs": "Dr. Eckart von Hirschhausen, Quarks, Geo Wissen, Charité, MaxPlanck, Huberman Lab (DE-Fans), Tim Ferriss, ARD Gesundheit, Apotheken Umschau (modern), Biohacking-Szene Berlin",
        "hooks": "Starte mit einer Gesundheitsimplikation: 'Diese Entdeckung könnte 20 Jahre zu deinem Leben hinzufügen.' Sci-Fi durch Körper/Geist-Linse. 'Was die NASA über Altern im All entdeckt hat verändert alles.'",
        "avoid": "Medizinische Behauptungen ohne Evidenz, Lifestyle-Predigt, kalte klinische Distanz, emotionale Dimension ignorieren, Panikmache ohne Lösungen, Heilversprechen",
    },
    ("de", "scifi_curious"): {
        "lang_label": "German", "audience_label": "Sci-Fi Curious",
        "tone": "Wonder-filled, story-first, accessible. Like a cool science teacher who makes you forget you're learning. Equal parts entertainment and education. Build awe. Create 'holy shit' moments.",
        "slang": "Mind-Blow, Plot Twist, Lore Drop, Multiversum, Simulation confirmed, Zeitreise-Vibes, Galaxy Brain, Reality Check, kosmischer Horror, Easter Egg, Worldbuilding, Canon",
        "vocab": "Wissenschaft cineastisch machen. Jedes Konzept kriegt eine Film-Beschreibung. Lebendige Metaphern: 'Stell dir vor, das gesamte Universum passt in einen Teelöffel.' Balance echte Science mit spekulativem 'Was wäre wenn'.",
        "cultural_refs": "Dark (Netflix), Interstellar, Dune, The Expanse, Kurzgesagt, Terra X, Perry Rhodan, Drei Körper Problem, Black Mirror, Harald Lesch, Raumzeit Podcast, Star Trek (DE Synchron)",
        "hooks": "Starte mit mind-bending Szenario. 'Wissenschaftler haben gerade bewiesen dass wir in einem Hologramm leben könnten.' 'Stell dir vor du stehst auf...' Technik. Filmische Szenen DANN die Wissenschaft.",
        "avoid": "Langweilig sein, trockene Erklärungen ohne Narrativ, den Wow-Faktor verlieren, Science-Gatekeeping, zu viel Vorwissen annehmen, Vorlesung ohne Storytelling",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🇫🇷 FRENCH
    # ─────────────────────────────────────────────────────────────────────────

    ("fr", "finance_listeners"): {
        "lang_label": "French", "audience_label": "Finance Listeners",
        "tone": "Elegant but hard-hitting. Like a Goldman Sachs analyst passionate about sci-fi. Rigorous with numbers. Intellectual confidence. 'Smart money is already positioning.'",
        "slang": "Rendement, portefeuille, valorisation, disruption, scalable, game-changer, bull run, bear market, hedge, effet de levier, liquidité, allocation, private equity, levée de fonds",
        "vocab": "Termes scientifiques liés à l'impact marché. Cadrer les découvertes comme des tendances investissables. Utiliser: TAM, courbe S, deeptech, économie de l'attention. Quantique/IA comme thèse d'investissement.",
        "cultural_refs": "Les Échos, BFM Business, LVMH Innovation, Station F, Xavier Niel, BpiFrance, Dassault Systèmes, Ariane Group, CMA CGM tech ventures, Matthieu Pigasse",
        "hooks": "Commencer avec un chiffre de marché choc. 'Cette percée pourrait créer un marché de 400 milliards d'euros d'ici 2030.' Montrer ce que fait la smart money MAINTENANT.",
        "avoid": "Langage familier excessif, mèmes, ton trop décontracté, spéculation sans fondement, exemples américains sans équivalent français, jargon sans explication",
    },
    ("fr", "millennials"): {
        "lang_label": "French", "audience_label": "Millennials",
        "tone": "Intellectual but accessible. Like a France Culture podcast gone pop. Deep reflection with lightness. The pleasure of understanding. Unapologetic 90s/2000s nostalgia. Everyday philosophy.",
        "slang": "C'est chaud, ça passe, tranquille, grave, trop bien, en mode, banger, galère, mytho, la flemme, cramé, c'est relou, j'avoue, en vrai, stylé, validé",
        "vocab": "Science accessible avec références culturelles françaises. Philosophie et physique main dans la main. Métaphores du quotidien parisien — métro, boulot, existentialisme appliqué.",
        "cultural_refs": "Kaamelott, OSS 117, Matrix, Interstellar, Étienne Klein, Hubert Reeves, Astérix (ironique), Les Inconnus, Daft Punk, les années Canal+, Dark (Netflix), Fondation (Asimov)",
        "hooks": "Commencer par une question existentielle ancrée dans le réel. 'Et si Descartes avait raison — mais pour les mauvaises raisons?' Construire une tension narrative. Le plaisir de la révélation.",
        "avoid": "Condescendance, vulgarisation excessive, ignorer le contexte social, anglicismes inutiles, ton corporate, prendre les auditeurs pour des idiots",
    },
    ("fr", "tech_enthusiasts"): {
        "lang_label": "French", "audience_label": "Tech Enthusiasts",
        "tone": "Precise, rigorous, passionate. Like an INRIA engineer explaining a breakthrough. First-principles. Respect the listener's intelligence. Deep-dive welcome. The elegance of logic.",
        "slang": "Ça compile, shipper, déployer, edge case, dette technique, code spaghetti, ça marche sur ma machine, stack overflow, overengineered, feature creep, merge conflict, pull request",
        "vocab": "Terminologie technique réelle — expliquer une fois, puis utiliser librement. Référencer des papers. Big-O, API comme métaphore, architecture système. Phénomènes naturels comme systèmes distribués.",
        "cultural_refs": "Le Journal du Hacker, Next INpact, INRIA, CNRS, Polytechnique, OVHcloud, Mistral AI, LeBonCoin tech blog, Alan, Doctolib engineering, Paris AI meetups, 42 School",
        "hooks": "Ouvrir avec un paradoxe technique. 'Il y a un bug dans le Modèle Standard que personne ne peut corriger.' Référencer un paper récent. 'Décortiquons l'architecture ensemble.'",
        "avoid": "Simplifier sans donner la vraie explication, erreurs factuelles, handwaving, buzzwords vides, franglais excessif, ton marketing, approximations scientifiques",
    },
    ("fr", "gen_z"): {
        "lang_label": "French", "audience_label": "Gen Z",
        "tone": "Ultra-fast, authentic, chaotic but brilliant. Like two friends screaming on Discord at 2 AM. Maximum energy. Meme-literate. Self-deprecating humor. Break the fourth wall.",
        "slang": "Frère, c'est chaud, wallah, j'avoue, chanmé, la hess, dead, clivant, cringe, seum, daron/daronne, bail, ça claque, en vrai, pookie, slay, ratio, mid, goat",
        "vocab": "Tout expliquer via gaming, anime ou réseaux sociaux. 'Les trous noirs c'est le boss final de la physique.' Phrases courtes. Fragments OK. MAJUSCULES pour emphasis. Energie TikTok.",
        "cultural_refs": "Squeezie, Cyprien, Inoxtag, Minecraft, One Piece, Naruto, Jujutsu Kaisen, TikTok France, Twitch FR, Gotaga, Kameto, Kylian Mbappé, Zone Interdite (mèmes), Netflix FR",
        "hooks": "Cold open choc. 'La NASA vient de trouver un truc qui devrait PAS exister.' Cliffhanger toutes les 3 minutes. 'Attends attends attends.' Segments TikTok-clippables de 30 secondes.",
        "avoid": "Ton corporate, références de boomer, expliquer les mèmes, utiliser le verlan mal, format cours magistral, intros de plus de 30 secondes, 'bonjour et bienvenue dans notre podcast'",
    },
    ("fr", "health_wellness"): {
        "lang_label": "French", "audience_label": "Health & Wellness",
        "tone": "Warm, empathetic, anchored in science. Like a doctor friend who reads the latest publications. Personal stakes — 'this concerns YOUR body.' Inspiring without moralizing. Art of living.",
        "slang": "Bien-être, pleine conscience, détox, microbiote, chronobiologie, jeûne intermittent, cohérence cardiaque, naturopathie, médecine fonctionnelle, longivité, anti-âge",
        "vocab": "Termes médicaux avec explication immédiate en langage courant. Connecter espace/physique à la biologie humaine. Telomères, mitochondries, neuroplasticité — toujours ce que ça signifie pour LEUR santé.",
        "cultural_refs": "Michel Cymes, France 5 Santé, Doctissimo (modernisé), Institut Pasteur, INSERM, Thierry Casasnovas (controversé mais connu), FitnessPark, Yuka app, Goop trad FR",
        "hooks": "Ouvrir avec une implication santé: 'Cette découverte pourrait ajouter 20 ans à votre vie.' Cadrer le sci-fi à travers le corps/esprit. 'Ce que la NASA a découvert sur le vieillissement dans l'espace change tout.'",
        "avoid": "Promesses médicales sans preuves, ton clinique froid, ignorer la dimension émotionnelle, alarmisme sans solutions, promesses de guérison, condescendance sur le mode de vie",
    },
    ("fr", "scifi_curious"): {
        "lang_label": "French", "audience_label": "Sci-Fi Curious",
        "tone": "Wonder-filled, narrative-first, accessible. Like a cool science teacher who makes you forget you're learning. Entertainment and education in equal parts. Build wonder. Create 'holy shit' moments.",
        "slang": "Mind-blow, plot twist, lore drop, multivers, simulation confirmée, vibes voyage temporel, galaxy brain, reality check, horreur cosmique, monde ouvert, worldbuilding, Easter egg",
        "vocab": "Science rendue cinématique. Chaque concept reçoit une description digne d'un film. Métaphores vivantes: 'Imagine l'univers entier dans une cuillère à café.' Balance science réelle et scénarios 'et si'.",
        "cultural_refs": "Dark (Netflix), Interstellar, Dune, La Planète des singes, Valérian, Jules Verne, Le Petit Prince (métaphore), Métal Hurlant, Besson (Le Cinquième Élément), Fondation, Étienne Klein",
        "hooks": "Scénario mind-bending en ouverture. 'Des scientifiques viennent de prouver qu'on pourrait vivre dans un hologramme.' Technique du 'imagine que tu te tiens sur...' Scène cinématique PUIS la science.",
        "avoid": "Être ennuyeux, explications sèches sans narration, perdre le facteur wow, gatekeeping scientifique, trop de connaissances préalables, cours magistral sans storytelling",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🇧🇷 PORTUGUESE (Brazilian)
    # ─────────────────────────────────────────────────────────────────────────

    ("pt", "finance_listeners"): {
        "lang_label": "Portuguese", "audience_label": "Finance Listeners",
        "tone": "Authoritative but passionate. Like a sharp analyst who gets excited about market opportunities. Concrete data. Premium Brazilian podcast energy. Confidence without arrogance.",
        "slang": "Cara, firmeza, top demais, pesado, jogada, virada de jogo, rendimento, carteira, aporte, renda passiva, valuation, tese de investimento, upside, compound interest",
        "vocab": "Ciência conectada a impacto de mercado. Descobertas como tendências investíveis. Use: TAM, curva S, disrupção, unit economics. Explique quântica/IA através do ROI.",
        "cultural_refs": "Primo Rico, Nath Finanças, InfoMoney, B3, Nubank, Shark Tank Brasil, Elon Musk, real vs dólar, Itaú Labs, Embraer, Stone, PagSeguro, Warren Buffett",
        "hooks": "Comece com número devastador. 'Essa descoberta pode criar um mercado de R$ 2 trilhões até 2030.' Mostre o que o smart money já está fazendo. Frame cada tópico como tese de investimento.",
        "avoid": "Linguagem juvenil, memes, tom casual demais, especulação sem fundamento, exemplos americanos sem paralelo brasileiro, hype sem substância",
    },
    ("pt", "millennials"): {
        "lang_label": "Portuguese", "audience_label": "Millennials",
        "tone": "Reflective, intelligent, with a nostalgic touch. Like explaining fascinating science to smart friends at a bar. Balanced optimism. Depth welcome. Philosophy in Brazilian daily life.",
        "slang": "Mano, é isso, faz sentido, real oficial, tá ligado, zueira never ends, surreal, pique, mood, tipo, rolê, perrengue, correria, vibe",
        "vocab": "Ciência acessível com contexto brasileiro. Filosofia e física juntas. Metáforas do dia a dia — boleto, carreira, crise existencial. Temas complexos através da experiência vivida.",
        "cultural_refs": "Porta dos Fundos, 3%, Black Mirror, Matrix, Chaves (nostalgia), Mamonas Assassinas, Sandy e Junior, Harry Potter, Interstellar, Jovem Nerd, Nerdologia, Atila Iamarino",
        "hooks": "Comece com 'e se' conectado à vida real deles. 'E se a teoria da simulação explicar por que seu emprego parece um script?' Construir stakes pessoais.",
        "avoid": "Ser condescendente, hype puro sem profundidade, ignorar contexto socioeconômico brasileiro, ser acadêmico demais, clickbait sem entrega",
    },
    ("pt", "tech_enthusiasts"): {
        "lang_label": "Portuguese", "audience_label": "Tech Enthusiasts",
        "tone": "Precise, rigorous, deeply curious. Like a senior dev explaining cutting-edge research. First-principles. Respect their intelligence. Deep-dive into mechanisms. Technical clarity.",
        "slang": "Deploy, shipar, edge case, dívida técnica, código espaguete, funciona na minha máquina, rubber ducking, gambiarra (com orgulho), stack, overengineered, POC, MVP, sprint",
        "vocab": "Terminologia técnica real — explique uma vez, depois use. Referencie papers. Big-O como metáfora, analogias de API, pensamento de system design. Fenômenos naturais como sistemas distribuídos.",
        "cultural_refs": "TabNews, Filipe Deschamps, Código Fonte TV, Fabio Akita, Alura, RockContent, Nubank engineering blog, iFood tech, PagSeguro dev, GitHub Brasil, Hacker News",
        "hooks": "Comece com paradoxo técnico. 'Tem um bug no Modelo Padrão que ninguém consegue fixar.' Referencie paper recente. 'Deixa eu quebrar essa arquitetura pra vocês.'",
        "avoid": "Simplificar sem oferecer explicação real, erros factuais, handwaving, buzzword soup, portuñol forçado, tom de marketing",
    },
    ("pt", "gen_z"): {
        "lang_label": "Portuguese", "audience_label": "Gen Z",
        "tone": "Fast, chaotic, authentic. Like two friends screaming about science on Discord at 2 AM. Maximum energy. Meme-literate. Self-aware. Break the fourth wall.",
        "slang": "Mano, brabo, cringe, based, slay, goat, mid, sus, é real, surreal, aleatório, cancelado, ratio, lacrou, mitou, descoladíssimo, paia, mó",
        "vocab": "Explicar tudo via gaming, anime ou redes sociais. 'Buracos negros são o boss final da física.' Frases com menos de 15 palavras. Fragmentos OK. CAPS pra ênfase.",
        "cultural_refs": "Minecraft, One Piece, Felipe Neto, Casimiro, Cellbit, Winderson, T3ddy, TikTok Brasil, Twitch BR, Naruto, Jujutsu Kaisen, Cortes podcast, Flow Podcast clips",
        "hooks": "Cold open insano. 'A NASA acabou de achar algo que NÃO deveria existir.' Cliffhanger a cada 3 minutos. 'Calma calma calma.' Segmentos clippáveis pra TikTok de 30 segundos.",
        "avoid": "Tom corporativo, referências de tiozão, explicar memes, gíria usada errada, formato aula, intros maiores que 30 segundos, 'olá sejam bem-vindos ao nosso podcast'",
    },
    ("pt", "health_wellness"): {
        "lang_label": "Portuguese", "audience_label": "Health & Wellness",
        "tone": "Welcoming, empathetic, science-based but emotionally resonant. Like a doctor friend who reads cutting-edge research. Personal stakes — 'this affects YOUR body.' Inspiring without preaching.",
        "slang": "Biohacking, longevidade, otimizar, eixo intestino-cérebro, ritmo circadiano, saúde metabólica, jejum intermitente, banho de gelo, aterramento, regulação do sistema nervoso, mindfulness",
        "vocab": "Termos médicos com explicação imediata em linguagem simples. Conectar espaço/física à biologia humana. Telômeros, mitocôndrias, neuroplasticidade, microbioma — sempre o que significa pra SAÚDE deles.",
        "cultural_refs": "Drauzio Varella, Dr. Barakat, Saúde da Mente com Daniel Barros, Globo Repórter saúde, SUS (contexto), Nature Brasilis, academia brasileira, suplementação, Puravida",
        "hooks": "Comece com implicação de saúde: 'Essa descoberta pode adicionar 20 anos à sua vida.' Sci-fi pela lente corpo/mente. 'O que a NASA descobriu sobre envelhecimento no espaço muda tudo.'",
        "avoid": "Alegações médicas sem evidência, tom clínico frio, ignorar dimensão emocional, alarmismo sem soluções, promessas de cura, pregar sobre estilo de vida",
    },
    ("pt", "scifi_curious"): {
        "lang_label": "Portuguese", "audience_label": "Sci-Fi Curious",
        "tone": "Filled with wonder, narrative-first, accessible. Like a cool science teacher who makes you forget you're learning. Entertainment and education in equal parts. Build awe.",
        "slang": "Mind-blow, plot twist, lore drop, multiverso, simulação confirmada, vibe viagem no tempo, galaxy brain, reality check, horror cósmico, mundo aberto, worldbuilding, Easter egg",
        "vocab": "Ciência tornada cinematográfica. Cada conceito ganha descrição digna de filme. Metáforas vívidas: 'Imagina o universo inteiro cabendo numa colher de chá.' Balance ciência real com cenários 'e se'.",
        "cultural_refs": "Interstellar, Dune, 3% (Netflix Brasil), Black Mirror, Nerdologia, Jovem Nerd, Kurzgesagt, SpaceTodayTV, Canaltech, Isaac Asimov, Arthur C. Clarke, Star Wars",
        "hooks": "Cenário mind-bending pra abrir. 'Cientistas acabaram de provar que a gente pode estar vivendo num holograma.' Técnica do 'imagina que você está em pé no...' Cena cinematográfica DEPOIS a ciência.",
        "avoid": "Ser chato, explicações secas sem narrativa, perder o fator uau, gatekeeping de ciência, assumir muito conhecimento prévio, aula sem storytelling",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🇪🇸 SPANISH
    # ─────────────────────────────────────────────────────────────────────────

    ("es", "finance_listeners"): {
        "lang_label": "Spanish", "audience_label": "Finance Listeners",
        "tone": "Serious but passionate. Like a Wall Street analyst who loves sci-fi. Hard data, intellectual confidence. Precision with emotion. 'Smart money is already moving.'",
        "slang": "Rendimiento, cartera, inversión, disruption, game-changer, mercado alcista/bajista, apalancamiento, liquidez, yield, diversificación, tesis de inversión, upside, hedge",
        "vocab": "Ciencia vinculada al impacto de mercado. Descubrimientos como tendencias invertibles. TAM, curva S, disrupción. Cuántica/IA como tesis de inversión. Física como tendencia de mercado.",
        "cultural_refs": "Andrei Jikh (LATAM fans), El Economista, Bloomberg Línea, Mercado Libre, Nubank México, Kavak, Rappi, BBVA Research, Santander Innovation, La Bolsa Mexicana de Valores",
        "hooks": "Empezar con cifra de mercado impactante. 'Este avance podría crear un mercado de $400 mil millones para 2030.' Mostrar qué hace el smart money AHORA. Cada tema es una tesis de inversión.",
        "avoid": "Lenguaje juvenil, memes, tono demasiado informal, especulación sin base, ejemplos solo estadounidenses, hype sin sustancia, regionalismos excluyentes",
    },
    ("es", "millennials"): {
        "lang_label": "Spanish", "audience_label": "Millennials",
        "tone": "Reflective, intelligent, with a nostalgic touch. Like explaining fascinating science to smart friends over craft beer. Balanced optimism. Depth welcome. Everyday philosophy.",
        "slang": "Mola, bro, de locos, posta, re copado, está heavy, ñoño con orgullo, mood, vibes, validado, gacho, chido, bacán, genial, la neta, orale",
        "vocab": "Ciencia accesible con contexto. Filosofía y física de la mano. Metáforas de la vida diaria — alquiler, carrera, crisis existencial. Temas complejos a través de experiencia vivida.",
        "cultural_refs": "La Casa de Papel, Dark (Netflix), Matrix, Interstellar, El Ministerio del Tiempo, Operación Triunfo, Mafalda, Borges, Club de Cuervos, Guillermo del Toro, Quantum Break",
        "hooks": "Empezar con '¿Y si...?' conectado a su vida. '¿Y si la teoría de la simulación explica por qué tu trabajo se siente guionizado?' Construir stakes personales. Narrativa de revelación.",
        "avoid": "Ser condescendiente, hype sin profundidad, ignorar contexto socioeconómico, tono académico puro, clickbait sin entrega, regionalismos que excluyan",
    },
    ("es", "tech_enthusiasts"): {
        "lang_label": "Spanish", "audience_label": "Tech Enthusiasts",
        "tone": "Precise, rigorous, deeply curious. Like a senior developer explaining cutting-edge research. First-principles. Respect their intelligence. Deep-dive into mechanisms. Logical elegance.",
        "slang": "Deployar, shippear, edge case, deuda técnica, código espagueti, funciona en mi máquina, rubber ducking, overengineered, stack, sprint, pull request, merge conflict, legacy code",
        "vocab": "Terminología técnica real — explicar una vez, luego usar. Referenciar papers. Big-O como metáfora, analogías de API, pensamiento de diseño de sistemas. Fenómenos naturales como sistemas distribuidos.",
        "cultural_refs": "Platzi, HolaMundo, BettaTech, Midudev, MoureDev, Xataka, Genbeta, GitHub Trending, Hacker News, Stack Overflow en español, Telefónica Tech, Cabify engineering",
        "hooks": "Abrir con paradoja técnica. 'Hay un bug en el Modelo Estándar que nadie puede arreglar.' Referenciar paper reciente. 'Déjenme desmenuzar la arquitectura.'",
        "avoid": "Simplificar sin dar la explicación real, errores factuales, handwaving, buzzwords vacíos, spanglish excesivo, tono de marketing",
    },
    ("es", "gen_z"): {
        "lang_label": "Spanish", "audience_label": "Gen Z",
        "tone": "Ultra-fast, authentic, chaotic but brilliant. Like two friends screaming about science on Discord at 2 AM. Maximum energy. Meme-literate. Self-aware. Break the fourth wall constantly.",
        "slang": "Bro, lol, random, cringe, based, slay, goat, mid, sus, es real, pana, marico (VE), wey/güey (MX), capo, re loco, posta, manco, tryhard, top, épico, GG",
        "vocab": "Explicar todo vía gaming, anime o redes sociales. 'Los agujeros negros son el boss final de la física.' Frases de menos de 15 palabras. Fragmentos OK. MAYÚSCULAS para énfasis.",
        "cultural_refs": "Minecraft, One Piece, Ibai, AuronPlay, ElRubius, TheGrefg, Jujutsu Kaisen, TikTok LATAM, Twitch ES, Naruto, Demon Slayer, Luisito Comunica, Windygirk",
        "hooks": "Cold open salvaje. 'La NASA acaba de encontrar algo que NO debería existir.' Cliffhanger cada 3 minutos. 'Espera espera espera.' Segmentos clippables para TikTok de 30 segundos.",
        "avoid": "Tono corporativo, referencias de boomer, explicar memes, usar slang mal, formato de clase, intros de más de 30 segundos, 'hola y bienvenidos a nuestro podcast'",
    },
    ("es", "health_wellness"): {
        "lang_label": "Spanish", "audience_label": "Health & Wellness",
        "tone": "Warm, empathetic, science-based but emotionally resonant. Like a doctor friend who reads cutting-edge research. Personal stakes — 'this affects YOUR body.' Inspiring without sermonizing.",
        "slang": "Biohacking, longevidad, optimizar, eje intestino-cerebro, ritmo circadiano, salud metabólica, ayuno intermitente, baño de hielo, grounding, regulación del sistema nervioso, mindfulness",
        "vocab": "Términos médicos con explicación inmediata en lenguaje simple. Conectar espacio/física con biología humana. Telómeros, mitocondrias, neuroplasticidad, microbioma — siempre qué significa para SU salud.",
        "cultural_refs": "Carlos López-Otín, DW Español ciencia, Aprendemos Juntos, Saber Vivir TVE, La Sexta salud, Fitness Revolucionario, biohacking hispano, Dr. La Rosa, Yoga con Adriene (ES)",
        "hooks": "Abrir con implicación de salud: 'Este descubrimiento podría agregar 20 años a tu vida.' Sci-fi a través del cuerpo/mente. 'Lo que la NASA descubrió sobre el envejecimiento en el espacio lo cambia todo.'",
        "avoid": "Afirmaciones médicas sin evidencia, tono clínico frío, ignorar dimensión emocional, alarmismo sin soluciones, promesas de cura, sermonear sobre estilo de vida",
    },
    ("es", "scifi_curious"): {
        "lang_label": "Spanish", "audience_label": "Sci-Fi Curious",
        "tone": "Wonder-filled, narrative-first, accessible. Like a cool science teacher who makes you forget you're learning. Entertainment and education in equal parts. Build awe. Create 'wow' moments.",
        "slang": "Mind-blow, plot twist, lore drop, multiverso, simulación confirmada, vibes de viaje temporal, galaxy brain, reality check, horror cósmico, mundo abierto, worldbuilding, Easter egg",
        "vocab": "Ciencia hecha cinematográfica. Cada concepto recibe descripción digna de película. Metáforas vívidas: 'Imagina el universo entero cabiendo en una cucharita.' Balance ciencia real con escenarios '¿y si?'.",
        "cultural_refs": "Interstellar, Dune, Black Mirror, Fundación (Asimov), Borges, Cuarto Milenio, El Ministerio del Tiempo, Star Wars, Kurzgesagt (ES), CdeCiencia, QuantumFracture, Date un Vlog",
        "hooks": "Escenario mind-bending para abrir. 'Científicos acaban de probar que podríamos vivir en un holograma.' Técnica de 'imagina que estás parado en...' Escena cinematográfica LUEGO la ciencia.",
        "avoid": "Ser aburrido, explicaciones secas sin narrativa, perder el factor wow, gatekeeping científico, asumir mucho conocimiento previo, clase sin storytelling, usar solo español de España",
    },
}


def main():
    force = "--force" in sys.argv

    db = os.path.abspath(DB_PATH)
    if not os.path.exists(db):
        print(f"[ERROR] Database not found: {db}")
        sys.exit(1)

    conn = sqlite3.connect(db, check_same_thread=False, timeout=10)

    # Ensure table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skill_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lang TEXT NOT NULL, audience TEXT NOT NULL,
            lang_label TEXT, audience_label TEXT,
            tone TEXT, vocab TEXT, slang TEXT,
            cultural_refs TEXT, hooks TEXT, avoid TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lang, audience)
        )
    """)
    conn.commit()

    inserted = 0
    skipped = 0
    updated = 0

    for (lang, audience), profile in PROFILES.items():
        existing = conn.execute(
            "SELECT id FROM skill_profiles WHERE lang=? AND audience=?",
            (lang, audience)
        ).fetchone()

        if existing and not force:
            skipped += 1
            continue

        if existing and force:
            conn.execute("""
                UPDATE skill_profiles
                SET lang_label=?, audience_label=?, tone=?, vocab=?, slang=?,
                    cultural_refs=?, hooks=?, avoid=?, created_at=CURRENT_TIMESTAMP
                WHERE lang=? AND audience=?
            """, (
                profile["lang_label"], profile["audience_label"],
                profile["tone"], profile["vocab"], profile["slang"],
                profile["cultural_refs"], profile["hooks"], profile["avoid"],
                lang, audience
            ))
            updated += 1
        else:
            conn.execute("""
                INSERT INTO skill_profiles
                (lang, audience, lang_label, audience_label, tone, vocab, slang, cultural_refs, hooks, avoid)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                lang, audience,
                profile["lang_label"], profile["audience_label"],
                profile["tone"], profile["vocab"], profile["slang"],
                profile["cultural_refs"], profile["hooks"], profile["avoid"],
            ))
            inserted += 1

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM skill_profiles").fetchone()[0]
    by_lang = conn.execute(
        "SELECT lang, COUNT(*) FROM skill_profiles GROUP BY lang ORDER BY lang"
    ).fetchall()

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Skill Profiles Seeded")
    print(f"{'='*60}")
    print(f"  Inserted: {inserted}")
    print(f"  Updated:  {updated}")
    print(f"  Skipped:  {skipped} (already exist, use --force)")
    print(f"  Total:    {total} profiles in DB")
    print(f"{'='*60}")
    for lang, count in by_lang:
        flag = {"en": "🇬🇧", "de": "🇩🇪", "fr": "🇫🇷", "pt": "🇧🇷", "es": "🇪🇸"}.get(lang, "🌐")
        print(f"  {flag} {lang}: {count} profiles")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
