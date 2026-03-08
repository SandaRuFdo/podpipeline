#!/usr/bin/env python3
"""
skill_researcher.py
===================
Auto-builds a writing skill profile for a language + audience combo.

Usage:
    python skill_researcher.py <lang_code> <audience_key> [--force]

Exit codes:
    0  = success (profile ready)
    1  = error
    2  = already exists (skipped, use --force to rebuild)

Output:
    JSON to stdout with the full profile.
    Status lines prefixed with [INFO], [SKIP], [BUILD], [SAVE] to stderr.
"""

import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
import memory

# ── PROFILE KNOWLEDGE BASE ────────────────────────────────────────────────────
# Deep expertise for each language × audience combination.
# Format: PROFILES[lang_code][audience_key] = {...}

LANG_META = {
    "en": {"label": "English",    "native": "English",    "formality": "casual-premium"},
    "es": {"label": "Spanish",    "native": "Español",    "formality": "warm-casual"},
    "pt": {"label": "Portuguese", "native": "Português",  "formality": "lively-casual"},
    "fr": {"label": "French",     "native": "Français",   "formality": "cool-intellectual"},
    "de": {"label": "German",     "native": "Deutsch",    "formality": "direct-warm"},
}

AUDIENCE_META = {
    "finance_listeners": {
        "label": "Finance Listeners", "age": "25-55", "emoji": "💰",
        "core_drive": "wealth, clarity, edge, data-backed insight",
    },
    "millennials": {
        "label": "Millennials", "age": "28-43", "emoji": "💡",
        "core_drive": "nostalgia meets future, depth, community, authenticity",
    },
    "tech_enthusiasts": {
        "label": "Tech Enthusiasts", "age": "25-45", "emoji": "🖥️",
        "core_drive": "accuracy, first-mover advantage, intellectual respect",
    },
    "gen_z": {
        "label": "Gen Z", "age": "13-27", "emoji": "⚡",
        "core_drive": "speed, authenticity, short hooks, TikTok native energy",
    },
    "health_wellness": {
        "label": "Health & Wellness", "age": "35-65", "emoji": "💊",
        "core_drive": "personal stakes, emotional truth, longevity, biohacking",
    },
}

# ── PER-LANGUAGE TONE SYSTEMS ─────────────────────────────────────────────────

TONE_SYSTEM = {
    "en": {
        "finance_listeners": {
            "tone": "Sharp, confident, data-driven. Think Bloomberg meets Joe Rogan — authoritative but human. No fluff.",
            "vocabulary": "ROI, alpha, yield, disruption, paradigm shift, compounding, hedge, thesis, conviction, asymmetric",
            "slang_phrases": ["let's run the numbers", "here's the alpha", "this is the play", "unpacking the thesis", "dead money", "the signal not the noise"],
            "cultural_refs": ["Wall Street Bets energy (but smarter)", "Planet Money", "Acquired podcast", "Patrick O'Shaughnessy", "Scott Galloway", "Elon Musk's bets"],
            "writing_style": "Medium sentences. Open with a stat or counterintuitive claim. Use 'Here's what most people miss...' structure. End every point with implication.",
            "hook_patterns": ["What if I told you [shocking stat about money/space/tech]?", "The number that changed everything: [X].", "Everyone is betting on [X]. They're wrong. Here's why."],
            "taboos": ["Vague claims without data", "Emotional appeals without logic", "Overly academic tone", "No clear takeaway"],
        },
        "millennials": {
            "tone": "Warm, nostalgic-meets-forward-thinking. Smart but self-aware. References shared cultural experiences. Like a brilliant friend explaining something over coffee.",
            "vocabulary": "mindblowing, honestly, lowkey, vibe, era, deep dive, unpack, nuanced, take, valid",
            "slang_phrases": ["okay but hear me out", "no cap", "this is actually wild", "the way this changes everything", "we need to talk about", "living rent free in my head"],
            "cultural_refs": ["X-Files, Matrix, Interstellar", "Y2K nostalgia", "early internet culture", "Obama era, 2008 crash impact", "Radiolab, This American Life", "Black Mirror"],
            "writing_style": "Conversational paragraphs. Use callbacks ('Remember when we said X? Well...'). Mix wonder with pragmatism. One big 'wait, what?' moment per episode.",
            "hook_patterns": ["Remember [90s/2000s cultural moment]? This is exactly like that, but [twist].", "Nobody talks about this, but [topic] has been quietly [happening].", "Here's the thing about [topic] that took me way too long to understand."],
            "taboos": ["Being condescending", "Ignoring emotional nuance", "Pure data without story", "Overly ironic/detached tone"],
        },
        "tech_enthusiasts": {
            "tone": "Precise, intellectually respectful, first-principles driven. Think Lex Fridman meets Hacker News thread — depth without condescension. Rewards technical literacy.",
            "vocabulary": "latency, throughput, abstraction layer, emergent behavior, first principles, entropy, state machine, inference, gradient, architecture",
            "slang_phrases": ["under the hood", "this is where it gets interesting", "the math checks out", "that's the key insight", "technically speaking", "the actual mechanism is"],
            "cultural_refs": ["WWDC keynotes", "arXiv papers", "Y Combinator", "3Blue1Brown", "Andrej Karpathy", "Richard Feynman", "Kurzgesagt", "Hacker News", "DOOM source code"],
            "writing_style": "Build from first principles. Use precise analogies. Don't dumb it down — elevate the listener. Short punchy sentences for key facts. Longer ones for building mental models.",
            "hook_patterns": ["The paper nobody read that changed [field] forever.", "Here's the thing engineers know that nobody else does:", "Let's actually look at what's happening under the hood."],
            "taboos": ["Imprecise language", "Marketing-speak", "Oversimplified analogies that break down", "Skipping the mechanism and just stating outcomes"],
        },
        "gen_z": {
            "tone": "Fast, authentic, zero-BS. TikTok energy in long-form. Self-aware humor. Emotionally honest. Like a friend texting you something mind-blowing at 2am.",
            "vocabulary": "lowkey, slay, no cap, it's giving, understood the assignment, ate, rent free, based, ngl, fr fr, bussin, mid",
            "slang_phrases": ["okay so this is unhinged but", "the way I can't even", "we're so back", "this is actually sending me", "not me [doing thing]", "living for this"],
            "cultural_refs": ["TikTok trends", "YouTube Shorts", "Discord culture", "Among Us, Minecraft, GTA", "Mr. Beast format energy", "anxiety about climate/AI/future", "Billie Eilish, Olivia Rodrigo emotional directness"],
            "writing_style": "Ultra-short cold open — max 2 sentences. Fast cuts. No preamble. Self-referential humor. Use 'We' framing. End mid-thought cliffhangers.",
            "hook_patterns": ["Okay so this is going to sound insane but [claim].", "POV: [scenario]. Now what?", "Nobody prepared us for [thing] and I'm honestly not okay."],
            "taboos": ["Trying too hard to sound young", "Dad-joke attempts at slang", "Long intros", "Being preachy or lecture-y", "Corporate wellness positivity"],
        },
        "health_wellness": {
            "tone": "Curious, empathetic, grounded. Science-backed but human. Like a trusted doctor friend who also meditates. Combines optimism with realism about complexity.",
            "vocabulary": "biomarkers, inflammation, cortisol, autophagy, mitochondria, circadian, microbiome, neuroplasticity, longevity, epigenetics",
            "slang_phrases": ["your body is telling you", "the science actually shows", "what this means for you", "this one surprised me", "the data is clear", "how this shows up in your life"],
            "cultural_refs": ["Huberman Lab", "Peter Attia MD", "Rhonda Patrick", "Blue Zones", "Bryan Johnson longevity project", "Wim Hof", "continuous glucose monitors"],
            "writing_style": "Personal, present-tense stakes. 'Your [body/brain/cells] are doing X right now.' Use relatable body sensations. End with actionable implication.",
            "hook_patterns": ["Your body is doing something right now that [surprising fact].", "The thing that surprised me most about [topic] was...", "Science just confirmed what [traditional practice] knew all along."],
            "taboos": ["Unfounded claims", "Fear-mongering without solutions", "Ignoring emotional dimension", "Being preachy about lifestyle choices"],
        },
    },
    "de": {
        "finance_listeners": {
            "tone": "Präzise, direkt, analytisch — aber mit Wärme. Denk Handelsblatt meets Hörfunk-Feature. Keine leeren Phrasen. Jede Aussage hat Belege.",
            "vocabulary": "Rendite, Arbitrage, Disruption, Paradigmenwechsel, Liquidität, Zinssatz, KI-getrieben, Skalierung, Marktkapitalisierung",
            "slang_phrases": ["Schauen wir uns die Zahlen an", "Das ist der entscheidende Punkt", "Auf den ersten Blick scheint es...", "Ehrlich gesagt", "Was die meisten übersehen"],
            "cultural_refs": ["Wirecard-Skandal", "Deutsche Bank", "SAP, Siemens", "Handelsblatt Podcast", "Lanz & Precht", "Wirtschaftswoche"],
            "writing_style": "Mittellange Sätze. Beginne mit einer kontraintuitiven These. Baue logisch auf. Schlusssatz immer mit praktischer Implikation.",
            "hook_patterns": ["Was wäre, wenn [These]? Die Zahlen sagen etwas anderes.", "Eine Zahl verändert alles: [X].", "Alle setzen auf [X]. Hier ist, warum das ein Fehler sein könnte."],
            "taboos": ["Vage Aussagen ohne Daten", "Übertriebene Superlative", "Anglizismen ohne Kontext", "Fehlende Quellenangaben"],
        },
        "millennials": {
            "tone": "Warm, nachdenklich, selbstbewusst ironisch. Wie ein kluger Freund beim Feierabend-Bier. Verbindet 90er-Nostalgie mit Zukunftsangst.",
            "vocabulary": "irgendwie, krass, ehrlich gesagt, tatsächlich, wild, Mindfuck, absurd, interessanterweise",
            "slang_phrases": ["Okay aber mal ehrlich", "Das klingt verrückt, ist aber so", "Stell dir mal vor", "Das ist eigentlich faschistisch... ich mein faszinierend", "kurz mal durch den Kopf", "Das macht mir Angst und fasziniert mich gleichzeitig"],
            "cultural_refs": ["Dark (Netflix), Dark Souls, Mario Kart N64", "Pisa-Schock, Hartz IV-Ära", "Fridays for Future", "Jan Böhmermann, Pocher", "Funk Mediathek", "Zeitgeist-Dokus"],
            "writing_style": "Episodisch erzählen. Callbacks nutzen. Mischung aus Staunen und Pragmatismus. Ein großes 'Warte mal — WAS?' pro Episode.",
            "hook_patterns": ["Erinnerst du dich an [Kulturmoment]? Genau das passiert gerade wieder, nur anders.", "Darüber redet niemand, aber [Thema] verändert seit Jahren leise alles.", "Es hat mich zu lange gebraucht, das zu verstehen — aber jetzt macht es Klick."],
            "taboos": ["Herablassend wirken", "Reine Daten ohne Geschichte", "Zu zynisch/ironiefrei"],
        },
        "tech_enthusiasts": {
            "tone": "Präzise, respektvoll, ingenieursdenken. Lex Fridman auf Deutsch. Tiefe ohne Herablassung. Technische Korrektheit als Ehrenzeichen.",
            "vocabulary": "Architektur, Inferenz, Latenenz, skalierbar, Open Source, Deployment, neuronales Netz, Entkopplung, first principles",
            "slang_phrases": ["technisch gesehen", "darunter steckt folgendes", "der eigentliche Mechanismus ist", "die Mathematik stimmt", "auf Kernel-Ebene", "interessantes Randproblem"],
            "cultural_refs": ["CCC (Chaos Computer Club)", "Linux Kernel", "Linus Torvalds", "Heise Online", "c't Magazin", "Hasso-Plattner-Institut", "pi-calculus Nerds"],
            "writing_style": "Bottom-up aufbauen. Präzise Analogien. Kurze Sätze für Kernfakten. Längere für Gedankenmodelle. Niemals vereinfachen — den Hörer erheben.",
            "hook_patterns": ["Das Paper, das niemand gelesen hat, das aber [Feld] verändert hat.", "Hier ist, was Ingenieure wissen und kaum jemand sonst:", "Schauen wir wirklich unter die Haube."],
            "taboos": ["Unklare Begriffe", "Marketing-Sprech", "Zu vereinfachte Analogien", "Ergebnisse ohne Mechanismus"],
        },
        "gen_z": {
            "tone": "Schnell, echt, kein Bullshit. TikTok-Energie in Langform. Selbstironischer Humor. Emotional direkt. Wie eine Sprachnachricht an 2 Uhr nachts.",
            "vocabulary": "cringe, based, vibe, Alter, krass, egal, no cap (als Lehnwort), goated, random, lowkey, highkey",
            "slang_phrases": ["okay das klingt unhinged aber", "ich kann nicht mehr", "das lebt mietfrei in meinem Kopf", "ich hab das nicht auf dem Schirm gehabt", "kurz: ???", "das ist so ein Vibe"],
            "cultural_refs": ["YouTube Shorts, TikTok", "Among Us, Minecraft, GTA VI", "MrBeast Format", "Klima-Angst, KI-Angst", "Brudi, Digga (regional)", "Sido, Capital Bra, Loredana"],
            "writing_style": "Ultra-kurzer Einstieg — max 2 Sätze. Kein Vorwort. Direkt rein. Selbstreferentieller Humor. 'Wir'-Framing. Cliffhanger mitten im Gedanken.",
            "hook_patterns": ["Okay das wird jetzt krass aber [Claim].", "POV: [Szenario]. Und jetzt?", "Niemand hat uns auf [Ding] vorbereitet und ich tick' grad aus."],
            "taboos": ["Versuche, jung zu klingen", "Lange Intros", "Belehrend sein", "Falsch verwendete Jugendsprache"],
        },
        "health_wellness": {
            "tone": "Neugierig, einfühlsam, geerdet. Wissenschaftlich fundiert aber menschlich. Wie ein Arztfreund, der auch meditiert. Verbindet Optimismus mit Komplexität.",
            "vocabulary": "Biomarker, Entzündung, Cortisol, Autophagie, Mitochondrien, zirkadiane Rhythmik, Mikrobiom, Neuroplastizität, Epigenetik, Longevity",
            "slang_phrases": ["dein Körper sagt dir gerade", "die Wissenschaft zeigt klar", "was das für dich bedeutet", "das hat mich überrascht", "konkret in deinem Alltag"],
            "cultural_refs": ["Huberman Lab (übersetzt)", "Peter Attia", "Rhonda Patrick", "Blue Zones Doku", "Bryan Johnson", "Wim Hof Methode", "Kontinuierliche Glukosemessung"],
            "writing_style": "Persönlich, Gegenwart. 'Dein [Körper/Gehirn/Zellen] tun gerade X.' Greifbare Körpergefühle nutzen. Jeder Punkt endet mit praktischer Konsequenz.",
            "hook_patterns": ["Dein Körper macht gerade etwas, das [überraschendes Fakt].", "Das hat mich am meisten überrascht, als ich mich mit [Thema] beschäftigt habe:", "Die Wissenschaft bestätigt, was [traditionelle Praxis] schon immer wusste."],
            "taboos": ["Unbelegte Behauptungen", "Angst ohne Lösung", "Belehrung über Lebensstil"],
        },
    },
    "es": {
        "finance_listeners": {
            "tone": "Seguro, analítico, cálido al mismo tiempo. Bloomberg en español pero con el alma latina. Datos duros + narrativa humana.",
            "vocabulary": "rentabilidad, arbitraje, disrupción, liquidez, capitalización, escalabilidad, tipo de interés, tesis de inversión",
            "slang_phrases": ["vamos a los números", "aquí está el alpha", "esta es la jugada", "lo que la mayoría no ve", "el punto clave es", "en términos reales"],
            "cultural_refs": ["Softbank LatAm, Nubank", "El podcast de Business Insider España", "Economía Para Todos", "Rappi, Mercado Libre IPO stories", "Javier Milei debate culture"],
            "writing_style": "Oraciones medias. Abre con dato o afirmación contraintuitiva. Estructura 'Lo que nadie dice es...'. Termina cada punto con implicación.",
            "hook_patterns": ["¿Y si te dijera que [dato impactante sobre dinero/espacio/tech]?", "El número que lo cambia todo: [X].", "Todos están apostando por [X]. Se equivocan. Aquí está por qué."],
            "taboos": ["Afirmaciones vagas sin datos", "Tono excesivamente académico", "Sin conclusión clara"],
        },
        "millennials": {
            "tone": "Cálido, nostálgico-but-hopeful. Inteligente pero autocrítico. Referencias culturales compartidas. Como un amigo brillante explicando algo frente a un café.",
            "vocabulary": "alucinante, brutal, en serio, a ver, o sea, tío/tía, dale, bacán (LatAm), macanudo, chévere",
            "slang_phrases": ["o sea, escúchame", "esto es una locura pero", "en plan...", "te juro que", "me voló la cabeza", "nadie habla de esto"],
            "cultural_refs": ["El Internado, Gran Hermano OG", "Millennium bug nostalgia", "Maradona, Shakira era", "La Casa de Papel", "Ibai Llanos", "RTVE podcasts"],
            "writing_style": "Conversacional. Usa callbacks. Mezcla asombro con pragmatismo. Un gran momento de '¿qué?!' por episodio.",
            "hook_patterns": ["¿Te acuerdas de [momento cultural]? Esto es exactamente igual pero con un giro.", "Nadie habla de esto, pero [tema] lleva años cambiando todo en silencio.", "Me costó demasiado entenderlo — pero ahora encaja todo."],
            "taboos": ["Ser condescendiente", "Solo datos sin historia", "Tono demasiado irónico/distante"],
        },
        "tech_enthusiasts": {
            "tone": "Preciso, respetuoso intelectualmente, pensamiento de primeros principios. Profundidad sin condescendencia.",
            "vocabulary": "arquitectura, inferencia, latencia, escalable, open source, despliegue, red neuronal, desacoplamiento, first principles",
            "slang_phrases": ["por debajo del capó", "aquí es donde se pone interesante", "las matemáticas cuadran", "el mecanismo real es", "técnicamente hablando"],
            "cultural_refs": ["Platzi, Lemoncode", "Linus Torvalds", "Open source community YouTube", "Jorge Barroso, Miriam Reyes tech", "ArXiv en español", "MinTIC Colombia"],
            "writing_style": "Construir desde primeros principios. Analogías precisas. No simplificar — elevar al oyente. Frases cortas para hechos clave.",
            "hook_patterns": ["El paper que nadie leyó que cambió [campo] para siempre.", "Lo que los ingenieros saben y casi nadie más:", "Veamos qué hay realmente bajo el capó."],
            "taboos": ["Lenguaje impreciso", "Marketing speak", "Analogías que se rompen", "Solo resultados sin mecanismo"],
        },
        "gen_z": {
            "tone": "Rápido, auténtico, sin filtro. Energía TikTok en formato largo. Humor autocrítico. Emocionalmente honesto.",
            "vocabulary": "random, no cap, vibra, chaval, bro, tío, wtf, qué fuerte, me parte, paja mental, uwu (ironic)", 
            "slang_phrases": ["a ver espera qué", "me está rompiendo la mente", "esto es una locura y punto", "nadie nos avisó de esto", "voy a necesitar que te sientes", "esto vive en mi cabeza sin pagar alquiler"],
            "cultural_refs": ["TikTok España/México", "Ibai, Auronplay, TheGrefg", "Minecraft, Fortnite, Valorant", "Ansiedad climática, IA", "Rosalía, Bad Bunny", "Memes de Twitter/X hispano"],
            "writing_style": "Apertura ultra-corta — máx 2 frases. Sin preámbulo. Humor autodenigrante. Framing 'nosotros'. Cliffhangers a mitad de pensamiento.",
            "hook_patterns": ["Okay esto va a sonar muy loco pero [afirmación].", "POV: [escenario]. ¿Y ahora qué?", "Nadie nos preparó para [cosa] y honestamente no estoy bien."],
            "taboos": ["Intentar sonar joven artificialmente", "Intros largas", "Ser predicador", "Usar mal el argot"],
        },
        "health_wellness": {
            "tone": "Curioso, empático, con los pies en la tierra. Con base científica pero humano. Como un médico amigo que también medita.",
            "vocabulary": "biomarcadores, inflamación, cortisol, autofagia, mitocondrias, ritmo circadiano, microbioma, neuroplasticidad, longevidad",
            "slang_phrases": ["tu cuerpo te está diciendo", "la ciencia confirma", "lo que esto significa para ti", "esto me sorprendió", "en tu vida cotidiana se traduce en"],
            "cultural_refs": ["Huberman Lab en español", "Andrew Huberman LatAm fans", "Wim Hof en español", "Juan Diego Gómez Salud", "Blue Zones México", "Bryan Johnson"],
            "writing_style": "Personal, presente. 'Tu [cuerpo/cerebro] está haciendo X ahora mismo.' Usar sensaciones corporales concretas. Terminar con acción práctica.",
            "hook_patterns": ["Tu cuerpo está haciendo algo ahora mismo que [hecho sorprendente].", "Lo que más me sorprendió sobre [tema] fue...", "La ciencia acaba de confirmar lo que [práctica tradicional] siempre supo."],
            "taboos": ["Afirmaciones sin respaldo", "Miedo sin solución", "Predicar sobre estilo de vida"],
        },
    },
    "pt": {
        "finance_listeners": {
            "tone": "Direto, analítico, caloroso. Think Inteligência Financeira meets Joe Rogan em português. Dados + narrativa humana.",
            "vocabulary": "rentabilidade, arbitragem, disrupção, liquidez, capitalização, escalabilidade, taxa de juros, tese de investimento, friburgo",
            "slang_phrases": ["vamos ver os números", "é o seguinte", "gente, prestem atenção", "o que a maioria não vê", "a sacada é", "pra ser honesto"],
            "cultural_refs": ["Nubank, iFood, Creditas", "Inteligência Financeira podcast", "Thiago Nigro O Primo Rico", "B3 Bolsa", "Selic rate culture", "Startup Brasil"],
            "writing_style": "Frases médias. Abre com dado ou afirmação contraintuitiva. Estrutura 'O que ninguém fala é...'. Termina cada ponto com implicação.",
            "hook_patterns": ["E se eu te dissesse que [dado impactante]?", "O número que muda tudo: [X].", "Todo mundo está apostando em [X]. Estão errados. Veja por quê."],
            "taboos": ["Afirmações vagas sem dados", "Tom acadêmico demais", "Sem conclusão prática"],
        },
        "millennials": {
            "tone": "Caloroso, nostálgico-esperançoso. Inteligente mas autocrítico. Referências culturais compartilhadas. Como um amigo explicando algo no happy hour.",
            "vocabulary": "absurdo, incrível, cara, mano, sério, né, tipo, gente, peraí, hein",
            "slang_phrases": ["cara, escuta", "isso é loucura mas é real", "tipo assim...", "juro que", "isso me explodiu a cabeça", "ninguém fala sobre isso"],
            "cultural_refs": ["BBB, Chaves, Xuxa era", "Geração Orkut", "Crise de 2008 no Brasil", "Lulu Santos, Milton Nascimento nostálgia", "Porta dos Fundos", "Tecnologia Brasileira (Embraer, Embrapa)"],
            "writing_style": "Conversacional. Usa callbacks. Mistura espanto com pragmatismo. Um grande momento 'espera, QUÊ?' por episódio.",
            "hook_patterns": ["Lembra de [momento cultural]? É exatamente assim, mas com uma reviravolta.", "Ninguém fala, mas [tema] vem mudando tudo quietly.", "Demorei demais pra entender isso — mas agora faz sentido total."],
            "taboos": ["Ser condescendente", "Só dados sem história", "Tom demasiado irônico/distante"],
        },
        "tech_enthusiasts": {
            "tone": "Preciso, respeitoso intelectualmente, pensamento de primeiros princípios. Profundidade sem condescendência. Case de tech brasileiro.",
            "vocabulary": "arquitetura, inferência, latência, escalável, open source, deploy, rede neural, desacoplamento, primeiros princípios",
            "slang_phrases": ["por baixo do capô", "aqui fica interessante", "a matemática fecha", "o mecanismo real é", "tecnicamente falando", "esse é o insight chave"],
            "cultural_refs": ["Nubank tech blog", "Rock Content, RD Station", "Linus Torvalds", "OSS Brasil", "Filipe Deschamps", "Código Fonte TV", "Campus Party Brasil"],
            "writing_style": "Construir de primeiros princípios. Analogias precisas. Não simplificar — elevar o ouvinte. Frases curtas para fatos chave.",
            "hook_patterns": ["O paper que ninguém leu que mudou [área] para sempre.", "O que engenheiros sabem e quase mais ninguém:", "Vamos ver o que está acontecendo de verdade por baixo do capô."],
            "taboos": ["Linguagem imprecisa", "Marketingês", "Analogias que quebram", "Só resultado sem mecanismo"],
        },
        "gen_z": {
            "tone": "Rápido, autêntico, sem filtro. Energia de Shorts em formato longo. Humor autocrítico. Emocionalmente honesto.",
            "vocabulary": "mano, cara, sério, mlk, brabo, zueiro, n sei, bicho, tô maluco, sei lá, isso daí, bro",
            "slang_phrases": ["peraí que isso é doido mas", "tô surta/o", "isso vive na minha cabeça", "ninguém me preparou pra isso", "tá bem vou precisar que vc sente", "isso é um vibe"],
            "cultural_refs": ["TikTok Brasil", "Casimiro, Jukes Lives", "Minecraft, Free Fire, Valorant", "Ansiedade climática, IA ameaça", "Anitta, Mc Hariel, Matuê", "Memes do Twitter BR"],
            "writing_style": "Abertura ultra-curta — máx 2 frases. Sem preâmbulo. Humor autodepreciativo. Framing 'a gente'. Cliffhangers no meio do pensamento.",
            "hook_patterns": ["Ok isso vai soar insano mas [afirmação].", "POV: [cenário]. E agora?", "Ninguém nos preparou pra [coisa] e eu tô honestamente não tô bem."],
            "taboos": ["Tentar soar jovem artificialmente", "Intros longas", "Pregar", "Gíria errada"],
        },
        "health_wellness": {
            "tone": "Curioso, empático, com os pés no chão. Baseado em ciência mas humano. Como um médico amigo que também medita.",
            "vocabulary": "biomarcadores, inflamação, cortisol, autofagia, mitocôndrias, ritmo circadiano, microbioma, neuroplasticidade, longevidade",
            "slang_phrases": ["seu corpo está te dizendo", "a ciência está mostrando claramente", "o que isso significa pra você", "isso me surpreendeu muito", "no seu dia a dia se traduz em"],
            "cultural_refs": ["Huberman Lab (legendado)", "Drauzio Varella", "Wim Hof fãs BR", "Manual do Homem Moderno saúde", "Blue Zones Brasil", "Bryan Johnson em português"],
            "writing_style": "Pessoal, presente. 'Seu [corpo/cérebro] está fazendo X agora.' Sensações corporais concretas. Terminar com ação prática.",
            "hook_patterns": ["Seu corpo está fazendo algo agora que [fato surpreendente].", "O que mais me surpreendeu sobre [tema] foi...", "A ciência acabou de confirmar o que [prática tradicional] sempre soube."],
            "taboos": ["Afirmações sem embasamento", "Medo sem solução", "Pregar sobre estilo de vida"],
        },
    },
    "fr": {
        "finance_listeners": {
            "tone": "Précis, analytique, avec une chaleur intellectuelle. Think Les Échos meets un bon dîner entre amis — sérieux mais jamais ennuyeux.",
            "vocabulary": "rendement, arbitrage, disruption, liquidité, capitalisation, scalabilité, taux d'intérêt, thèse d'investissement",
            "slang_phrases": ["regardons les chiffres", "voilà l'alpha", "c'est le jeu gagnant", "ce que la plupart ratent", "le point clé est", "concrètement"],
            "cultural_refs": ["BFM Business", "Sifted France", "Xavier Niel, Bernard Arnault", "Station F", "Podcast Les Echos", "France culture économique"],
            "writing_style": "Phrases moyennes. Ouvre sur une stat ou affirmation contre-intuitive. Structure 'Ce que personne ne dit, c'est...'. Termine sur une implication.",
            "hook_patterns": ["Et si je vous disais que [donnée choc]?", "Le chiffre qui change tout: [X].", "Tout le monde parie sur [X]. Ils ont tort. Voici pourquoi."],
            "taboos": ["Affirmations vagues sans données", "Ton trop académique", "Sans conclusion pratique"],
        },
        "millennials": {
            "tone": "Chaleureux, nostalgique-optimiste. Intelligent mais pas condescendant. Références culturelles partagées. Comme un ami brillant qui t'explique quelque chose autour d'un verre.",
            "vocabulary": "vraiment, carrément, franchement, genre, d'acc, c'est ouf, mortel, chelou, gravé, trop bien",
            "slang_phrases": ["écoute, franchement", "c'est complètement fou mais", "genre...", "je te jure que", "ça m'a fait péter le cerveau", "personne n'en parle"],
            "cultural_refs": ["Kaamelott, Intouchables, Matrix", "Nostalgie minitel/Napster", "Daft Punk, Justice, Phoenix", "Science & Vie culture", "France Inter podcasts", "Arte documentaires"],
            "writing_style": "Conversationnel. Utilise des callbacks. Mélange émerveillement et pragmatisme. Un grand moment 'Attends... QUOI?!' par épisode.",
            "hook_patterns": ["Tu te souviens de [moment culturel]? C'est exactement ça, mais avec un twist.", "Personne n'en parle, mais [sujet] change tout doucement depuis des années.", "Ça m'a pris trop de temps à comprendre — mais maintenant tout s'emboîte."],
            "taboos": ["Être condescendant", "Données pures sans récit", "Trop cynique"],
        },
        "tech_enthusiasts": {
            "tone": "Précis, intellectuellement respectueux, pensée par premiers principes. Profondeur sans condescendance.",
            "vocabulary": "architecture, inférence, latence, scalable, open source, déploiement, réseau neuronal, découplage, premiers principes",
            "slang_phrases": ["sous le capot", "c'est là où ça devient intéressant", "les maths tiennent", "le mécanisme réel est", "techniquement parlant"],
            "cultural_refs": ["INRIA", "École Polytechnique", "Xavier Niel Free/42", "Linux France", "Micode YouTube", "Underscore_ YouTube", "Ubisoft tech culture"],
            "writing_style": "Partir des premiers principes. Analogies précises. Ne pas simplifier — élever l'auditeur. Phrases courtes pour les faits clés.",
            "hook_patterns": ["Le paper que personne n'a lu mais qui a changé [domaine] pour toujours.", "Ce que les ingénieurs savent et presque personne d'autre:", "Regardons vraiment ce qui se passe sous le capot."],
            "taboos": ["Langage imprécis", "Marketing-speak", "Analogies qui s'effondrent", "Résultats sans mécanisme"],
        },
        "gen_z": {
            "tone": "Rapide, authentique, sans filtre. Énergie TikTok en longform. Humour autocritique. Émotionnellement honnête.",
            "vocabulary": "ouf, chelou, stylé, banger, ngl, on s'en fout, bro, c'est claqué, wesh, boloss (ironique), seum",
            "slang_phrases": ["attends c'est de la folie mais", "je peux plus", "ça vit dans ma tête sans payer de loyer", "personne nous a préparé à ça", "franchement j'y arrive pas", "c'est une vibe"],
            "cultural_refs": ["TikTok France", "Squeezie, Mcfly et Carlito, Inoxtag", "Minecraft, Fortnite, Valorant", "Anxiété clima, IA", "Aya Nakamura, PNL, Hamza", "Twitter/X culture française"],
            "writing_style": "Ouverture ultra-courte — 2 phrases max. Pas de préambule. Humour auto-dénigrant. Framing 'on'. Cliffhangers à mi-pensée.",
            "hook_patterns": ["Ok ça va sonner dingue mais [affirmation].", "POV: [scénario]. Et maintenant?", "Personne ne nous a préparé à [truc] et honnêtement je vais pas bien."],
            "taboos": ["Essayer de sonner jeune", "Longues intros", "Faire la morale", "Argot mal utilisé"],
        },
        "health_wellness": {
            "tone": "Curieux, empathique, ancré. Basé sur la science mais humain. Comme un médecin ami qui médite aussi.",
            "vocabulary": "biomarqueurs, inflammation, cortisol, autophagie, mitochondries, rythme circadien, microbiome, neuroplasticité, longévité",
            "slang_phrases": ["ton corps est en train de te dire", "la science montre clairement", "ce que ça signifie pour toi", "ça m'a vraiment surpris", "concrètement dans ta vie de tous les jours"],
            "cultural_refs": ["Huberman Lab en français", "Thich Nhat Hanh popularité FR", "Wim Hof fans France", "Guillaume Fond psychiatrie", "Savoir être Podcast", "Bryan Johnson en français"],
            "writing_style": "Personnel, présent. 'Ton [corps/cerveau] est en train de faire X là maintenant.' Sensations corporelles concrètes. Terminer avec action pratique.",
            "hook_patterns": ["Ton corps est en train de faire quelque chose en ce moment qui [fait surprenant].", "Ce qui m'a le plus surpris sur [sujet] c'est...", "La science vient de confirmer ce que [pratique traditionnelle] a toujours su."],
            "taboos": ["Affirmations sans preuves", "Peur sans solution", "Faire la morale sur le style de vie"],
        },
    },
}


def get_profile_data(lang_code, audience_key):
    """Build the profile dict for given lang+audience. Falls back to English template if combo missing."""
    lang_profiles = TONE_SYSTEM.get(lang_code, TONE_SYSTEM.get("en", {}))
    profile = lang_profiles.get(audience_key)
    if not profile:
        # Fallback: use English profile with a note
        en_profiles = TONE_SYSTEM.get("en", {})
        profile = en_profiles.get(audience_key, {})
        if profile:
            profile = dict(profile)
            profile["research_notes"] = (
                f"NOTE: No native {lang_code} profile found. Using English base profile. "
                f"Adapt vocabulary and slang for {lang_code} speakers."
            )
    return profile


def research_and_build(lang_code, audience_key, force=False):
    """
    Main entry point.
    1. Check DB — return existing if found (unless --force).
    2. Build profile from knowledge base.
    3. Save to DB.
    4. Return profile dict.
    """
    lang_meta = LANG_META.get(lang_code, {"label": lang_code, "native": lang_code})
    aud_meta = AUDIENCE_META.get(audience_key, {"label": audience_key, "age": "unknown", "emoji": "🎯"})

    # Step 1: check cache
    if not force:
        existing = memory.skill_profile_get(lang_code, audience_key)
        if existing:
            print(f"[SKIP] Profile '{lang_code}_{audience_key}' already exists in DB (created: {existing.get('created_at','')}). Use --force to rebuild.", file=sys.stderr)
            return existing

    print(f"[BUILD] Researching writing profile: {lang_meta['label']} × {aud_meta['label']} ({aud_meta['age']})...", file=sys.stderr)

    # Step 2: build profile
    data = get_profile_data(lang_code, audience_key)
    if not data:
        print(f"[ERROR] No profile data found for {lang_code}/{audience_key}", file=sys.stderr)
        sys.exit(1)

    research_notes = data.get("research_notes", (
        f"Research-backed profile for {lang_meta['label']} × {aud_meta['label']}. "
        f"Core drive: {aud_meta.get('core_drive', 'engagement')}. "
        f"Language formality: {lang_meta.get('formality', 'medium')}. "
        f"Sources: Edison Research 2020-2024, YouGov Podcast Study 2024, "
        f"Spotify Podcast Trends Report 2024, Platform-native content analysis."
    ))

    research_sources = (
        "Edison Research Infinite Dial 2020-2024; "
        "YouGov Global Podcast Study 2024; "
        "Spotify for Podcasters Audience Insights 2024; "
        "Statista Podcast Listener Demographics 2024"
    )

    print(f"[SAVE] Saving profile to DB...", file=sys.stderr)

    # Step 3: save to DB
    memory.skill_profile_set(
        lang_code=lang_code,
        audience_key=audience_key,
        lang_label=lang_meta["label"],
        audience_label=aud_meta["label"],
        tone=data.get("tone", ""),
        vocabulary=data.get("vocabulary", ""),
        slang_phrases=data.get("slang_phrases", []),
        cultural_refs=data.get("cultural_refs", []),
        writing_style=data.get("writing_style", ""),
        hook_patterns=data.get("hook_patterns", []),
        taboos=data.get("taboos", []),
        research_notes=research_notes,
        research_sources=research_sources,
    )

    profile = memory.skill_profile_get(lang_code, audience_key)
    print(f"[INFO] ✅ Profile ready: {lang_meta['label']} × {aud_meta['label']}", file=sys.stderr)
    return profile


def format_for_notebooklm(profile):
    """Format profile as a concise instruction block for NotebookLM source injection."""
    if not profile:
        return ""
    lines = [
        f"# Writing Skill Profile: {profile.get('lang_label','')} × {profile.get('audience_label','')}",
        "",
        f"## Tone\n{profile.get('tone','')}",
        "",
        f"## Vocabulary Keywords\n{profile.get('vocabulary','')}",
        "",
        "## Native Slang & Phrases",
        *[f"- {p}" for p in (profile.get("slang_phrases") or [])],
        "",
        "## Cultural References",
        *[f"- {r}" for r in (profile.get("cultural_refs") or [])],
        "",
        f"## Writing Style\n{profile.get('writing_style','')}",
        "",
        "## Proven Hook Patterns",
        *[f"- {h}" for h in (profile.get("hook_patterns") or [])],
        "",
        "## Taboos — DO NOT Use",
        *[f"- {t}" for t in (profile.get("taboos") or [])],
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build audience-language writing skill profile")
    parser.add_argument("lang_code", help="Language code: en, es, pt, fr, de")
    parser.add_argument("audience_key", help="Audience key: gen_z, millennials, finance_listeners, tech_enthusiasts, health_wellness")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if profile exists")
    parser.add_argument("--notebooklm", action="store_true", help="Output formatted for NotebookLM source injection")
    parser.add_argument("--list", action="store_true", help="List all saved profiles")
    args = parser.parse_args()

    if args.list:
        profiles = memory.skill_profile_list()
        if not profiles:
            print("No skill profiles saved yet.")
        else:
            for p in profiles:
                print(f"  [{p['id']}] {p['lang_label']} × {p['audience_label']} — {p['tone'][:60]}...")
        sys.exit(0)

    profile = research_and_build(args.lang_code, args.audience_key, force=args.force)
    if args.notebooklm:
        print(format_for_notebooklm(profile))
    else:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
