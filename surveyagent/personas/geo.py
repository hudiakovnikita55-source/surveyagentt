"""Geography, languages and name pools used by the persona generator.

All numbers are rough, public-statistics-level approximations (population in
millions, average full-time gross salary in EUR, share of companies using AI).
They only need to be plausible enough to produce realistic-looking personas.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Countries of residence
# --------------------------------------------------------------------------- #
# english: distribution of English proficiency among office workers
# ai: relative AI adoption at work (1.0 = EU average)
# cities: (city, weight) or (city, weight, language, name_pool) for multilingual
#         countries where the city decides the local language.

EN_NATIVE = {"native": 1}
EN_HIGH = {"C2": 3, "C1": 5, "B2": 2}
EN_MIDHIGH = {"C2": 1, "C1": 4, "B2": 4, "B1": 1}
EN_MID = {"C1": 3, "B2": 5, "B1": 2}

COUNTRIES: dict[str, dict] = {
    "DE": dict(name="Germany", nationality="German", pop=84, ai=1.1, salary=52000,
               language="German", english=EN_MIDHIGH, cities=[
                   ("Berlin", 5), ("Munich", 4), ("Hamburg", 3), ("Frankfurt am Main", 3),
                   ("Cologne", 2), ("Stuttgart", 2), ("Düsseldorf", 2), ("Leipzig", 1),
                   ("Dresden", 1), ("Nuremberg", 1), ("Hanover", 1), ("Karlsruhe", 1),
                   ("Bremen", 1), ("Freiburg", 1)]),
    "FR": dict(name="France", nationality="French", pop=68, ai=0.9, salary=42000,
               language="French", english=EN_MID, cities=[
                   ("Paris", 8), ("Lyon", 3), ("Toulouse", 2), ("Nantes", 2), ("Bordeaux", 2),
                   ("Lille", 2), ("Marseille", 2), ("Montpellier", 1), ("Rennes", 1),
                   ("Grenoble", 1), ("Strasbourg", 1), ("Nice", 1)]),
    "UK": dict(name="United Kingdom", nationality="British", pop=68, ai=1.2, salary=46000,
               language="English", english=EN_NATIVE, cities=[
                   ("London", 8), ("Manchester", 3), ("Birmingham", 2), ("Edinburgh", 2),
                   ("Bristol", 2), ("Leeds", 2), ("Glasgow", 2), ("Cambridge", 1),
                   ("Oxford", 1), ("Cardiff", 1), ("Belfast", 1), ("Brighton", 1),
                   ("Newcastle upon Tyne", 1), ("Nottingham", 1)]),
    "IT": dict(name="Italy", nationality="Italian", pop=59, ai=0.8, salary=33000,
               language="Italian", english=EN_MID, cities=[
                   ("Milan", 6), ("Rome", 4), ("Turin", 2), ("Bologna", 2), ("Florence", 1),
                   ("Naples", 1), ("Padua", 1), ("Verona", 1), ("Genoa", 1), ("Bari", 1),
                   ("Trento", 1)]),
    "ES": dict(name="Spain", nationality="Spanish", pop=48, ai=0.9, salary=30000,
               language="Spanish", english=EN_MID, cities=[
                   ("Madrid", 6), ("Barcelona", 5), ("Valencia", 2), ("Seville", 1),
                   ("Málaga", 2), ("Bilbao", 1), ("Zaragoza", 1), ("Palma", 1),
                   ("Alicante", 1), ("Granada", 1)]),
    "PL": dict(name="Poland", nationality="Polish", pop=37, ai=0.7, salary=20000,
               language="Polish", english=EN_MIDHIGH, cities=[
                   ("Warsaw", 5), ("Kraków", 3), ("Wrocław", 2), ("Poznań", 1), ("Gdańsk", 2),
                   ("Łódź", 1), ("Katowice", 1), ("Lublin", 1)]),
    "UA": dict(name="Ukraine", nationality="Ukrainian", pop=33, ai=0.8, salary=7000,
               language="Ukrainian", english=EN_MID, cities=[
                   ("Kyiv", 5), ("Lviv", 3), ("Kharkiv", 1), ("Dnipro", 1), ("Odesa", 1)]),
    "RO": dict(name="Romania", nationality="Romanian", pop=19, ai=0.5, salary=16000,
               language="Romanian", english=EN_MIDHIGH, cities=[
                   ("Bucharest", 5), ("Cluj-Napoca", 3), ("Timișoara", 2), ("Iași", 1),
                   ("Brașov", 1)]),
    "NL": dict(name="Netherlands", nationality="Dutch", pop=18, ai=1.5, salary=55000,
               language="Dutch", english=EN_HIGH, cities=[
                   ("Amsterdam", 5), ("Rotterdam", 2), ("Utrecht", 2), ("The Hague", 2),
                   ("Eindhoven", 2), ("Groningen", 1), ("Leiden", 1), ("Delft", 1)]),
    "BE": dict(name="Belgium", nationality="Belgian", pop=11.8, ai=1.4, salary=55000,
               language="Dutch", english=EN_MIDHIGH, cities=[
                   ("Brussels", 2, "French", "BE_FR"), ("Brussels", 2, "Dutch", "BE_NL"),
                   ("Antwerp", 3, "Dutch", "BE_NL"), ("Ghent", 2, "Dutch", "BE_NL"),
                   ("Leuven", 2, "Dutch", "BE_NL"), ("Liège", 1, "French", "BE_FR"),
                   ("Namur", 1, "French", "BE_FR")]),
    "CZ": dict(name="Czechia", nationality="Czech", pop=10.9, ai=0.8, salary=22000,
               language="Czech", english=EN_MIDHIGH, cities=[
                   ("Prague", 5), ("Brno", 2), ("Ostrava", 1), ("Plzeň", 1)]),
    "SE": dict(name="Sweden", nationality="Swedish", pop=10.5, ai=1.5, salary=46000,
               language="Swedish", english=EN_HIGH, cities=[
                   ("Stockholm", 5), ("Gothenburg", 2), ("Malmö", 2), ("Uppsala", 1),
                   ("Linköping", 1), ("Lund", 1)]),
    "PT": dict(name="Portugal", nationality="Portuguese", pop=10.6, ai=0.9, salary=22000,
               language="Portuguese", english=EN_MIDHIGH, cities=[
                   ("Lisbon", 5), ("Porto", 3), ("Braga", 1), ("Coimbra", 1), ("Aveiro", 1)]),
    "GR": dict(name="Greece", nationality="Greek", pop=10.4, ai=0.7, salary=19000,
               language="Greek", english=EN_MIDHIGH, cities=[
                   ("Athens", 5), ("Thessaloniki", 2), ("Patras", 1), ("Heraklion", 1)]),
    "HU": dict(name="Hungary", nationality="Hungarian", pop=9.6, ai=0.7, salary=16000,
               language="Hungarian", english=EN_MID, cities=[
                   ("Budapest", 5), ("Debrecen", 1), ("Szeged", 1), ("Győr", 1)]),
    "AT": dict(name="Austria", nationality="Austrian", pop=9.1, ai=1.2, salary=53000,
               language="German", english=EN_MIDHIGH, cities=[
                   ("Vienna", 5), ("Graz", 2), ("Linz", 1), ("Salzburg", 1), ("Innsbruck", 1)]),
    "CH": dict(name="Switzerland", nationality="Swiss", pop=8.9, ai=1.3, salary=88000,
               language="German", english=EN_HIGH, cities=[
                   ("Zurich", 5, "German", "CH_DE"), ("Basel", 2, "German", "CH_DE"),
                   ("Bern", 1, "German", "CH_DE"), ("Zug", 1, "German", "CH_DE"),
                   ("Geneva", 2, "French", "CH_FR"), ("Lausanne", 2, "French", "CH_FR"),
                   ("Lugano", 1, "Italian", "CH_IT")]),
    "RS": dict(name="Serbia", nationality="Serbian", pop=6.6, ai=0.7, salary=11000,
               language="Serbian", english=EN_MIDHIGH, cities=[
                   ("Belgrade", 4), ("Novi Sad", 2), ("Niš", 1)]),
    "BG": dict(name="Bulgaria", nationality="Bulgarian", pop=6.4, ai=0.6, salary=12000,
               language="Bulgarian", english=EN_MIDHIGH, cities=[
                   ("Sofia", 5), ("Plovdiv", 2), ("Varna", 1)]),
    "DK": dict(name="Denmark", nationality="Danish", pop=5.9, ai=1.6, salary=66000,
               language="Danish", english=EN_HIGH, cities=[
                   ("Copenhagen", 4), ("Aarhus", 2), ("Odense", 1), ("Aalborg", 1)]),
    "FI": dict(name="Finland", nationality="Finnish", pop=5.6, ai=1.4, salary=47000,
               language="Finnish", english=EN_HIGH, cities=[
                   ("Helsinki", 4), ("Espoo", 2), ("Tampere", 2), ("Turku", 1), ("Oulu", 1)]),
    "NO": dict(name="Norway", nationality="Norwegian", pop=5.5, ai=1.4, salary=58000,
               language="Norwegian", english=EN_HIGH, cities=[
                   ("Oslo", 4), ("Bergen", 2), ("Trondheim", 2), ("Stavanger", 1)]),
    "SK": dict(name="Slovakia", nationality="Slovak", pop=5.4, ai=0.8, salary=17000,
               language="Slovak", english=EN_MIDHIGH, cities=[
                   ("Bratislava", 4), ("Košice", 1), ("Žilina", 1)]),
    "IE": dict(name="Ireland", nationality="Irish", pop=5.3, ai=1.4, salary=58000,
               language="English", english=EN_NATIVE, cities=[
                   ("Dublin", 5), ("Cork", 2), ("Galway", 1), ("Limerick", 1)]),
    "HR": dict(name="Croatia", nationality="Croatian", pop=3.9, ai=0.8, salary=18000,
               language="Croatian", english=EN_MIDHIGH, cities=[
                   ("Zagreb", 4), ("Split", 1), ("Rijeka", 1)]),
    "LT": dict(name="Lithuania", nationality="Lithuanian", pop=2.9, ai=0.8, salary=22000,
               language="Lithuanian", english=EN_MIDHIGH, cities=[
                   ("Vilnius", 4), ("Kaunas", 2), ("Klaipėda", 1)]),
    "SI": dict(name="Slovenia", nationality="Slovenian", pop=2.1, ai=1.0, salary=29000,
               language="Slovenian", english=EN_MIDHIGH, cities=[
                   ("Ljubljana", 4), ("Maribor", 1)]),
    "LV": dict(name="Latvia", nationality="Latvian", pop=1.9, ai=0.7, salary=19000,
               language="Latvian", english=EN_MIDHIGH, cities=[
                   ("Riga", 4), ("Jelgava", 1)]),
    "EE": dict(name="Estonia", nationality="Estonian", pop=1.4, ai=1.2, salary=24000,
               language="Estonian", english=EN_HIGH, cities=[
                   ("Tallinn", 4), ("Tartu", 2)]),
    "CY": dict(name="Cyprus", nationality="Cypriot", pop=0.93, ai=0.8, salary=27000,
               language="Greek", english=EN_HIGH, cities=[
                   ("Nicosia", 1), ("Limassol", 1)]),
    "LU": dict(name="Luxembourg", nationality="Luxembourgish", pop=0.67, ai=1.4, salary=80000,
               language="Luxembourgish", english=EN_HIGH, cities=[
                   ("Luxembourg City", 3), ("Esch-sur-Alzette", 1)]),
    "MT": dict(name="Malta", nationality="Maltese", pop=0.55, ai=1.0, salary=25000,
               language="Maltese", english={"native": 3, "C2": 2}, cities=[
                   ("Valletta", 1), ("Sliema", 1), ("St Julian's", 1)]),
    "IS": dict(name="Iceland", nationality="Icelandic", pop=0.39, ai=1.2, salary=70000,
               language="Icelandic", english=EN_HIGH, cities=[
                   ("Reykjavík", 3), ("Akureyri", 1)]),
}

# Extra local languages some residents also speak (city -> language).
CITY_SECOND_LANGUAGE = {
    "Barcelona": "Catalan",
    "Valencia": "Valencian",
    "Bilbao": "Basque",
    "Luxembourg City": "French",
    "Esch-sur-Alzette": "French",
    "Helsinki": "Swedish",
}

# --------------------------------------------------------------------------- #
# Origins that are not (only) countries of residence: diaspora / expats
# --------------------------------------------------------------------------- #
EXTRA_ORIGINS: dict[str, dict] = {
    "TR": dict(name="Turkey", nationality="Turkish", language="Turkish", english=EN_MID),
    "MAGHREB": dict(name="Morocco", nationality="Moroccan", language="Arabic", english=EN_MID,
                    alt_names=["Morocco", "Algeria", "Tunisia"]),
    "SOUTH_ASIAN": dict(name="India", nationality="Indian", language="Hindi", english=EN_HIGH,
                        alt_names=["India", "Pakistan", "Bangladesh"],
                        heritage_languages=["Punjabi", "Urdu", "Gujarati", "Bengali", "Hindi", "Tamil"]),
    "IN": dict(name="India", nationality="Indian", language="Hindi", english={"C2": 5, "C1": 4},
               alt_languages=["Hindi", "Tamil", "Telugu", "Marathi", "Kannada", "Malayalam", "Bengali"]),
    "ARABIC": dict(name="Syria", nationality="Syrian", language="Arabic", english=EN_MID,
                   alt_names=["Syria", "Iraq", "Lebanon", "Egypt"]),
    "BR": dict(name="Brazil", nationality="Brazilian", language="Portuguese", english=EN_MID),
    "US": dict(name="United States", nationality="American", language="English", english=EN_NATIVE),
    "RU": dict(name="Latvia", nationality="Latvian", language="Russian", english=EN_MIDHIGH),
}

# Probability that a resident has a migration background, and where from.
# kind: "heritage" = born/raised in the country (native local language too),
#       "expat"    = moved as an adult.
MIGRATION: dict[str, tuple[float, list[tuple[str, float, str]]]] = {
    "DE": (0.22, [("TR", 3, "heritage"), ("PL", 1, "expat"), ("IT", 1, "expat"), ("UA", 1, "expat"),
                  ("IN", 1.5, "expat"), ("GR", 1, "expat"), ("ES", 1, "expat"), ("RO", 1, "expat"),
                  ("ARABIC", 1, "heritage"), ("BR", 0.5, "expat")]),
    "UK": (0.24, [("SOUTH_ASIAN", 4, "heritage"), ("PL", 1, "expat"), ("IT", 1, "expat"),
                  ("ES", 1, "expat"), ("FR", 1, "expat"), ("IN", 1, "expat"), ("RO", 1, "expat"),
                  ("IE", 1, "expat"), ("US", 0.7, "expat"), ("GR", 0.5, "expat")]),
    "FR": (0.16, [("MAGHREB", 4, "heritage"), ("PT", 1, "heritage"), ("IT", 1, "expat"),
                  ("ES", 1, "expat"), ("RO", 0.7, "expat"), ("BE", 0.5, "expat")]),
    "NL": (0.22, [("MAGHREB", 2, "heritage"), ("TR", 2, "heritage"), ("IN", 2, "expat"),
                  ("DE", 1, "expat"), ("IT", 1, "expat"), ("ES", 1, "expat"), ("PL", 1, "expat"),
                  ("BR", 0.7, "expat"), ("UA", 0.7, "expat"), ("GR", 0.5, "expat")]),
    "BE": (0.2, [("MAGHREB", 3, "heritage"), ("TR", 1, "heritage"), ("IT", 1, "heritage"),
                 ("FR", 1, "expat"), ("RO", 1, "expat"), ("ES", 0.7, "expat"), ("PL", 0.7, "expat")]),
    "SE": (0.2, [("ARABIC", 3, "heritage"), ("FI", 1, "heritage"), ("PL", 1, "expat"),
                 ("IN", 1, "expat"), ("DE", 1, "expat"), ("TR", 0.7, "heritage"), ("UA", 0.7, "expat")]),
    "IE": (0.22, [("PL", 2, "expat"), ("IN", 2, "expat"), ("BR", 2, "expat"), ("IT", 1, "expat"),
                  ("ES", 1, "expat"), ("FR", 1, "expat"), ("US", 0.7, "expat"), ("UK", 1, "expat")]),
    "CH": (0.27, [("DE", 3, "expat"), ("IT", 2, "expat"), ("FR", 1, "expat"), ("PT", 2, "heritage"),
                  ("ES", 1, "expat"), ("IN", 1, "expat"), ("UK", 0.7, "expat")]),
    "AT": (0.2, [("DE", 3, "expat"), ("TR", 1, "heritage"), ("RS", 1, "heritage"), ("HR", 1, "heritage"),
                 ("RO", 1, "expat"), ("HU", 1, "expat"), ("PL", 0.7, "expat")]),
    "ES": (0.1, [("BR", 1, "expat"), ("IT", 1, "expat"), ("UK", 1, "expat"), ("FR", 1, "expat"),
                 ("RO", 1, "heritage"), ("UA", 0.7, "expat"), ("DE", 1, "expat")]),
    "PT": (0.12, [("BR", 4, "expat"), ("UK", 1, "expat"), ("FR", 1, "expat"), ("DE", 1, "expat"),
                  ("UA", 1, "expat"), ("IN", 0.5, "expat")]),
    "IT": (0.07, [("RO", 2, "heritage"), ("UA", 1, "expat"), ("BR", 1, "expat"), ("ARABIC", 0.7, "heritage")]),
    "DK": (0.12, [("PL", 1, "expat"), ("DE", 1, "expat"), ("SE", 1, "expat"), ("IN", 1, "expat"),
                  ("IT", 1, "expat"), ("ES", 1, "expat"), ("ARABIC", 1, "heritage"), ("UA", 0.7, "expat")]),
    "NO": (0.12, [("PL", 1.5, "expat"), ("SE", 1, "expat"), ("DE", 1, "expat"), ("IN", 1, "expat"),
                  ("LT", 1, "expat"), ("ARABIC", 0.7, "heritage")]),
    "FI": (0.08, [("EE", 2, "expat"), ("IN", 1, "expat"), ("UA", 1, "expat"), ("DE", 0.5, "expat")]),
    "LU": (0.5, [("PT", 3, "heritage"), ("FR", 3, "expat"), ("BE", 1, "expat"), ("DE", 2, "expat"),
                 ("IT", 1, "expat"), ("ES", 0.5, "expat")]),
    "PL": (0.08, [("UA", 5, "expat"), ("IN", 1, "expat")]),
    "CZ": (0.1, [("UA", 3, "expat"), ("SK", 3, "expat"), ("IN", 0.5, "expat")]),
    "EE": (0.22, [("RU", 5, "heritage"), ("UA", 1, "expat"), ("FI", 0.5, "expat")]),
    "LV": (0.25, [("RU", 5, "heritage"), ("UA", 1, "expat")]),
    "LT": (0.06, [("UA", 1, "expat"), ("RU", 0.5, "heritage")]),
    "MT": (0.15, [("IT", 2, "expat"), ("UK", 2, "expat"), ("IN", 1, "expat"), ("RS", 1, "expat")]),
    "CY": (0.1, [("GR", 3, "expat"), ("UK", 1, "expat"), ("BG", 1, "expat"), ("RO", 1, "expat")]),
    "IS": (0.1, [("PL", 3, "expat"), ("LT", 1, "expat")]),
    "SK": (0.04, [("CZ", 1, "expat"), ("UA", 1, "expat")]),
    "HU": (0.03, [("RO", 1, "expat")]),
    "SI": (0.05, [("HR", 1, "heritage"), ("RS", 1, "heritage")]),
    "HR": (0.03, [("RS", 1, "heritage")]),
    "GR": (0.03, [("BG", 1, "expat")]),
}

# How the different language backgrounds tend to show in written English.
L1_WRITING_NOTES: dict[str, str] = {
    "German": "may capitalise a noun now and then, uses 'since' with present tense "
              "('I use it since 2023'), fairly direct and precise wording",
    "French": "may put a space before '?' or '!', uses 'actually' to mean 'currently', "
              "occasionally French word order",
    "Italian": "may use 'actually' for 'currently', 'explain me', longer run-on sentences",
    "Spanish": "may drop a subject pronoun, 'actually' for 'currently', 'assist' for 'attend'",
    "Portuguese": "may use 'actually' for 'currently', 'make a question', slightly formal phrasing",
    "Catalan": "may drop a subject pronoun, 'actually' for 'currently'",
    "Polish": "sometimes drops or misuses articles (a/the), short direct sentences",
    "Ukrainian": "sometimes drops articles, direct phrasing, occasional wrong preposition",
    "Russian": "sometimes drops articles, direct phrasing",
    "Czech": "sometimes drops articles, direct phrasing",
    "Slovak": "sometimes drops articles, direct phrasing",
    "Slovenian": "sometimes drops articles",
    "Croatian": "sometimes drops articles, direct phrasing",
    "Serbian": "sometimes drops articles, direct phrasing",
    "Bulgarian": "sometimes drops articles, occasional wrong preposition",
    "Romanian": "may use 'actually' for 'currently', occasional preposition slips",
    "Hungarian": "occasionally mixes up he/she, article slips",
    "Greek": "occasional article and preposition slips, slightly formal",
    "Dutch": "near-fluent, occasional Dutch word order or 'I work here since'",
    "Swedish": "fluent and casual, very occasional direct translations",
    "Danish": "fluent and casual, very occasional direct translations",
    "Norwegian": "fluent and casual, very occasional direct translations",
    "Finnish": "may skip articles, occasionally mixes up he/she",
    "Estonian": "may skip articles, occasionally mixes up he/she",
    "Latvian": "sometimes drops articles",
    "Lithuanian": "sometimes drops articles",
    "Icelandic": "fluent, very occasional direct translations",
    "Turkish": "sometimes drops articles, simple sentence structure",
    "Arabic": "sometimes drops articles or uses 'the' where not needed",
    "Hindi": "fluent Indian English phrasing ('prepone', 'do the needful' very rarely)",
    "Tamil": "fluent Indian English phrasing",
    "Telugu": "fluent Indian English phrasing",
    "Marathi": "fluent Indian English phrasing",
    "Kannada": "fluent Indian English phrasing",
    "Malayalam": "fluent Indian English phrasing",
    "Bengali": "fluent Indian English phrasing",
    "Luxembourgish": "fluent, occasional French/German-style phrasing",
    "Maltese": "native-like English with some Maltese English expressions",
}

# --------------------------------------------------------------------------- #
# Name pools. Surnames: "Name" (same for all genders), ("Male", "Female") or
# ("Male", "Female married form", "Female maiden form") for Lithuanian.
# --------------------------------------------------------------------------- #

NAME_POOLS: dict[str, dict[str, list]] = {
    "DE": dict(
        male=["Lukas", "Maximilian", "Jonas", "Felix", "Tobias", "Florian", "Sebastian", "Jan",
              "Niklas", "Michael", "Thomas", "Andreas", "Stefan", "Markus", "Christian", "Daniel",
              "Matthias", "Philipp", "Moritz", "Tim", "Jürgen", "Frank"],
        female=["Anna", "Laura", "Julia", "Lena", "Sarah", "Katharina", "Lisa", "Hannah", "Sophie",
                "Johanna", "Sabine", "Claudia", "Nicole", "Stefanie", "Miriam", "Franziska",
                "Carolin", "Jana", "Lea", "Theresa", "Petra", "Kerstin"],
        surnames=["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
                  "Schulz", "Hoffmann", "Koch", "Richter", "Klein", "Wolf", "Schröder", "Neumann",
                  "Schwarz", "Braun", "Zimmermann", "Krüger", "Hartmann", "Lange", "Werner",
                  "Krause", "Lehmann", "Köhler", "Vogel", "Friedrich"]),
    "AT": dict(
        male=["Lukas", "David", "Florian", "Stefan", "Michael", "Andreas", "Thomas", "Christoph",
              "Matthias", "Dominik", "Bernhard", "Georg", "Manuel", "Alexander", "Martin", "Raphael"],
        female=["Katharina", "Anna", "Lisa", "Julia", "Sarah", "Christina", "Magdalena", "Theresa",
                "Verena", "Barbara", "Sabine", "Elisabeth", "Johanna", "Sophie", "Birgit", "Marlene"],
        surnames=["Gruber", "Huber", "Bauer", "Wagner", "Müller", "Pichler", "Steiner", "Moser",
                  "Mayer", "Hofer", "Leitner", "Berger", "Fuchs", "Eder", "Fischer", "Schmid",
                  "Winkler", "Weber", "Schwarz", "Maier", "Reiter", "Brunner"]),
    "CH_DE": dict(
        male=["Luca", "Noah", "Simon", "Lukas", "Reto", "Beat", "Urs", "Marco", "Adrian",
              "Patrick", "Fabian", "Dominik", "Samuel", "Jonas"],
        female=["Laura", "Sara", "Nadine", "Corinne", "Anna", "Lea", "Seraina", "Barbara",
                "Andrea", "Fabienne", "Martina", "Jasmin", "Nina", "Deborah"],
        surnames=["Müller", "Meier", "Schmid", "Keller", "Weber", "Huber", "Schneider", "Meyer",
                  "Steiner", "Fischer", "Gerber", "Brunner", "Baumann", "Frei", "Zimmermann",
                  "Moser", "Widmer", "Wyss", "Graf", "Roth"]),
    "CH_FR": dict(
        male=["Julien", "Nicolas", "Olivier", "Mathieu", "Yann", "Loïc", "Grégoire", "Florian"],
        female=["Céline", "Aurélie", "Camille", "Mélanie", "Sophie", "Chloé", "Valérie", "Joëlle"],
        surnames=["Favre", "Rochat", "Morel", "Bonvin", "Perrin", "Dubois", "Monnier",
                  "Chappuis", "Jaccard", "Rey", "Blanc", "Girard"]),
    "CH_IT": dict(
        male=["Luca", "Marco", "Matteo", "Davide", "Fabio"],
        female=["Giulia", "Chiara", "Sara", "Elena", "Laura"],
        surnames=["Bernasconi", "Rossi", "Ferrari", "Lepori", "Pedrazzini", "Bianchi", "Galli"]),
    "FR": dict(
        male=["Thomas", "Nicolas", "Julien", "Maxime", "Antoine", "Alexandre", "Hugo", "Lucas",
              "Mathieu", "Romain", "Guillaume", "Pierre", "Kevin", "Sébastien", "Vincent",
              "Baptiste", "Clément", "Quentin", "Laurent", "Olivier"],
        female=["Camille", "Marie", "Julie", "Léa", "Manon", "Chloé", "Sarah", "Laura", "Pauline",
                "Émilie", "Claire", "Mathilde", "Élodie", "Anaïs", "Céline", "Sophie", "Aurélie",
                "Inès", "Juliette", "Nathalie"],
        surnames=["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
                  "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "Bertrand",
                  "Roux", "Vincent", "Fournier", "Morel", "Girard", "Mercier", "Lambert", "Bonnet",
                  "Faure", "Rousseau", "Blanc", "Guérin", "Chevalier", "Lefèvre"]),
    "BE_NL": dict(
        male=["Jens", "Pieter", "Wouter", "Thomas", "Bram", "Arne", "Stijn", "Koen", "Joris", "Tom",
              "Kobe", "Sander", "Dries", "Lander"],
        female=["Lotte", "Elke", "Sofie", "Lien", "Marie", "Eline", "Annelies", "Hanne", "Jolien",
                "Evelien", "Sarah", "Charlotte", "Katrien", "Fien"],
        surnames=["Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Willems", "Claes",
                  "Goossens", "Wouters", "De Smet", "Vermeulen", "Van den Broeck", "De Clercq",
                  "Pauwels", "Hermans", "Van Damme", "Verstraeten", "Aerts"]),
    "BE_FR": dict(
        male=["Maxime", "Nicolas", "Julien", "Olivier", "Arnaud", "Grégory", "Cédric", "Benoît",
              "Quentin", "Sébastien"],
        female=["Aurélie", "Céline", "Julie", "Charlotte", "Manon", "Amélie", "Sophie",
                "Stéphanie", "Laetitia", "Émilie"],
        surnames=["Dubois", "Lambert", "Dupont", "Martin", "Simon", "Laurent", "Leclercq",
                  "Lejeune", "Renard", "Collard", "Dumont", "François", "Hubert", "Gilson", "Lemaire"]),
    "UK": dict(
        male=["James", "Oliver", "Thomas", "Daniel", "Matthew", "Samuel", "Jack", "Harry", "George",
              "Ben", "Tom", "Chris", "Rob", "Luke", "Ryan", "Adam", "Callum", "Jamie", "Mark",
              "Stuart", "Gareth", "Rhys", "Euan", "Iain"],
        female=["Emily", "Sophie", "Charlotte", "Hannah", "Olivia", "Lucy", "Amy", "Jessica",
                "Rebecca", "Laura", "Katie", "Georgia", "Eleanor", "Rachel", "Emma", "Holly",
                "Chloe", "Hayley", "Siân", "Kirsty", "Fiona", "Gemma"],
        surnames=["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson",
                  "Thomas", "Johnson", "Roberts", "Robinson", "Thompson", "Wright", "Walker",
                  "White", "Edwards", "Hughes", "Green", "Hall", "Wood", "Harris", "Lewis",
                  "Clarke", "Turner", "Hill", "Scott", "Cooper", "Morris", "Ward", "Watson",
                  "Baker", "Harrison", "Morgan", "Campbell", "Stewart", "MacDonald", "Murray"]),
    "IE": dict(
        male=["Seán", "Conor", "Cian", "Darragh", "Ciarán", "Eoin", "Niall", "Liam", "Patrick",
              "Declan", "Shane", "Aidan", "Kevin", "Brian", "Rory", "Fionn"],
        female=["Aoife", "Niamh", "Siobhán", "Ciara", "Sinéad", "Orla", "Róisín", "Aisling",
                "Clodagh", "Emma", "Sarah", "Gráinne", "Caoimhe", "Saoirse", "Laura", "Méabh"],
        surnames=["Murphy", "Kelly", "O'Sullivan", "Walsh", "O'Brien", "Byrne", "Ryan", "O'Connor",
                  "O'Neill", "O'Reilly", "Doyle", "McCarthy", "Gallagher", "Doherty", "Kennedy",
                  "Lynch", "Murray", "Quinn", "Moore", "Brennan", "Fitzgerald", "Nolan", "Keane"]),
    "IT": dict(
        male=["Marco", "Alessandro", "Luca", "Matteo", "Andrea", "Francesco", "Lorenzo", "Davide",
              "Simone", "Federico", "Giuseppe", "Stefano", "Riccardo", "Paolo", "Giorgio",
              "Tommaso", "Gabriele", "Nicola", "Emanuele", "Fabio"],
        female=["Giulia", "Francesca", "Chiara", "Sara", "Martina", "Valentina", "Alessia", "Elena",
                "Federica", "Silvia", "Laura", "Elisa", "Paola", "Roberta", "Ilaria", "Beatrice",
                "Serena", "Anna", "Marta", "Veronica"],
        surnames=["Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci",
                  "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Mancini", "Costa",
                  "Giordano", "Rizzo", "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro",
                  "Mariani", "Rinaldi", "Caruso", "Ferrara", "Galli", "Martini", "Leone"]),
    "ES": dict(
        male=["Alejandro", "Pablo", "Daniel", "David", "Javier", "Sergio", "Carlos", "Adrián",
              "Álvaro", "Jorge", "Miguel", "Manuel", "Raúl", "Diego", "Iván", "Rubén", "Marcos",
              "Antonio", "Íñigo", "Jordi"],
        female=["Lucía", "María", "Laura", "Marta", "Paula", "Andrea", "Sara", "Cristina", "Elena",
                "Ana", "Irene", "Carmen", "Nuria", "Alba", "Raquel", "Beatriz", "Silvia", "Claudia",
                "Montserrat", "Ainhoa"],
        surnames=["García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez",
                  "Pérez", "Gómez", "Martín", "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno",
                  "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez", "Navarro", "Torres",
                  "Domínguez", "Vázquez", "Ramos", "Gil", "Serrano", "Blanco", "Molina", "Castro"]),
    "PT": dict(
        male=["João", "Pedro", "Tiago", "Miguel", "Rui", "André", "Diogo", "Ricardo", "Bruno",
              "Nuno", "Hugo", "Gonçalo", "Francisco", "Luís", "Filipe", "Duarte"],
        female=["Ana", "Inês", "Mariana", "Beatriz", "Sofia", "Catarina", "Joana", "Rita", "Marta",
                "Carolina", "Sara", "Filipa", "Margarida", "Patrícia", "Helena", "Teresa"],
        surnames=["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues",
                  "Martins", "Sousa", "Fernandes", "Gonçalves", "Gomes", "Lopes", "Marques",
                  "Alves", "Almeida", "Ribeiro", "Pinto", "Carvalho", "Teixeira", "Moreira",
                  "Correia", "Mendes"]),
    "PL": dict(
        male=["Piotr", "Krzysztof", "Tomasz", "Paweł", "Michał", "Marcin", "Kamil", "Jakub",
              "Łukasz", "Mateusz", "Bartosz", "Adam", "Maciej", "Wojciech", "Grzegorz", "Rafał",
              "Szymon", "Dawid"],
        female=["Anna", "Katarzyna", "Magdalena", "Agnieszka", "Joanna", "Aleksandra", "Monika",
                "Natalia", "Karolina", "Marta", "Ewa", "Paulina", "Justyna", "Zuzanna", "Weronika",
                "Dominika", "Małgorzata", "Julia"],
        surnames=[("Kowalski", "Kowalska"), ("Wiśniewski", "Wiśniewska"), "Wójcik", "Kowalczyk",
                  ("Kamiński", "Kamińska"), ("Lewandowski", "Lewandowska"), ("Zieliński", "Zielińska"),
                  ("Szymański", "Szymańska"), "Woźniak", ("Dąbrowski", "Dąbrowska"),
                  ("Kozłowski", "Kozłowska"), ("Jankowski", "Jankowska"), "Mazur",
                  ("Wojciechowski", "Wojciechowska"), ("Kwiatkowski", "Kwiatkowska"), "Krawczyk",
                  "Kaczmarek", "Nowak", ("Piotrowski", "Piotrowska"), ("Grabowski", "Grabowska"),
                  "Pawlak", "Michalak", ("Nowicki", "Nowicka"), "Adamczyk"]),
    "NL": dict(
        male=["Daan", "Sem", "Lars", "Bram", "Thijs", "Jeroen", "Ruben", "Niels", "Sander", "Joost",
              "Martijn", "Bas", "Tim", "Jasper", "Wouter", "Maarten", "Stijn", "Rik"],
        female=["Emma", "Sanne", "Lisa", "Anouk", "Fleur", "Lotte", "Femke", "Iris", "Eva",
                "Marloes", "Anne", "Esther", "Maaike", "Sophie", "Roos", "Inge", "Linda", "Julia"],
        surnames=["de Jong", "Jansen", "de Vries", "van den Berg", "van Dijk", "Bakker", "Janssen",
                  "Visser", "Smit", "Meijer", "de Boer", "Mulder", "de Groot", "Bos", "Vos",
                  "Peters", "Hendriks", "van Leeuwen", "Dekker", "Brouwer", "de Wit", "Dijkstra",
                  "Smits", "de Graaf", "van der Meer", "Kok"]),
    "SE": dict(
        male=["Erik", "Lars", "Anders", "Johan", "Karl", "Oskar", "Viktor", "Emil", "Filip",
              "Gustav", "Henrik", "Mattias", "Fredrik", "Magnus", "Andreas", "Axel", "Linus", "Jonas"],
        female=["Anna", "Emma", "Sara", "Maria", "Johanna", "Elin", "Linnea", "Frida", "Klara",
                "Ida", "Karin", "Sofia", "Malin", "Hanna", "Ebba", "Maja", "Lina", "Julia"],
        surnames=["Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson",
                  "Persson", "Svensson", "Gustafsson", "Pettersson", "Jonsson", "Jansson",
                  "Hansson", "Bengtsson", "Lindberg", "Lindqvist", "Lundgren", "Berg", "Holm",
                  "Sandberg", "Forsberg", "Engström", "Lindström"]),
    "DK": dict(
        male=["Mads", "Frederik", "Rasmus", "Mikkel", "Jesper", "Anders", "Søren", "Christian",
              "Morten", "Kasper", "Thomas", "Mathias", "Jonas", "Emil", "Nikolaj", "Henrik"],
        female=["Mette", "Anne", "Camilla", "Louise", "Sofie", "Ida", "Maria", "Line", "Signe",
                "Julie", "Katrine", "Freja", "Emma", "Cecilie", "Maja", "Pernille"],
        surnames=["Nielsen", "Jensen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen",
                  "Sørensen", "Rasmussen", "Jørgensen", "Petersen", "Madsen", "Kristensen",
                  "Olsen", "Thomsen", "Christiansen", "Poulsen", "Johansen", "Møller", "Mortensen"]),
    "NO": dict(
        male=["Ole", "Lars", "Magnus", "Henrik", "Martin", "Kristian", "Andreas", "Jonas",
              "Sindre", "Eirik", "Håkon", "Even", "Sander", "Thomas", "Espen", "Øyvind"],
        female=["Ingrid", "Kari", "Nora", "Emma", "Ida", "Silje", "Marte", "Ingvild", "Kristine",
                "Hanne", "Maria", "Thea", "Sara", "Guro", "Marit", "Tone"],
        surnames=["Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen", "Nilsen",
                  "Kristiansen", "Jensen", "Karlsen", "Johnsen", "Pettersen", "Eriksen", "Berg",
                  "Haugen", "Hagen", "Johannessen", "Andreassen", "Jacobsen", "Dahl", "Halvorsen",
                  "Lie", "Bakken", "Solberg"]),
    "FI": dict(
        male=["Mikko", "Juha", "Jari", "Antti", "Janne", "Mika", "Ville", "Teemu", "Tuomas",
              "Lauri", "Aleksi", "Joonas", "Eero", "Olli", "Sami", "Petri"],
        female=["Anna", "Laura", "Sanna", "Johanna", "Katja", "Emilia", "Maria", "Heidi", "Minna",
                "Riikka", "Aino", "Elina", "Noora", "Tiina", "Veera", "Kaisa"],
        surnames=["Korhonen", "Virtanen", "Mäkinen", "Nieminen", "Mäkelä", "Hämäläinen", "Laine",
                  "Heikkinen", "Koskinen", "Järvinen", "Lehtonen", "Lehtinen", "Saarinen",
                  "Salminen", "Heinonen", "Niemi", "Heikkilä", "Kinnunen", "Salonen", "Turunen"]),
    "IS": dict(
        male=["Jón", "Sigurður", "Guðmundur", "Gunnar", "Ólafur", "Einar", "Kristján", "Stefán",
              "Magnús", "Árni"],
        female=["Guðrún", "Anna", "Kristín", "Sigríður", "Margrét", "Helga", "Sigrún",
                "Ingibjörg", "Katrín", "Ásta"],
        surnames=[("Jónsson", "Jónsdóttir"), ("Guðmundsson", "Guðmundsdóttir"),
                  ("Sigurðarson", "Sigurðardóttir"), ("Gunnarsson", "Gunnarsdóttir"),
                  ("Ólafsson", "Ólafsdóttir"), ("Einarsson", "Einarsdóttir"),
                  ("Kristjánsson", "Kristjánsdóttir"), ("Stefánsson", "Stefánsdóttir"),
                  ("Magnússon", "Magnúsdóttir"), ("Björnsson", "Björnsdóttir")]),
    "CZ": dict(
        male=["Jan", "Petr", "Tomáš", "Martin", "Jakub", "Lukáš", "Ondřej", "Michal", "David",
              "Jiří", "Pavel", "Filip", "Vojtěch", "Marek", "Daniel", "Josef"],
        female=["Tereza", "Lucie", "Kateřina", "Veronika", "Petra", "Eva", "Jana", "Barbora",
                "Markéta", "Michaela", "Klára", "Anna", "Hana", "Martina", "Lenka", "Zuzana"],
        surnames=[("Novák", "Nováková"), ("Svoboda", "Svobodová"), ("Novotný", "Novotná"),
                  ("Dvořák", "Dvořáková"), ("Černý", "Černá"), ("Procházka", "Procházková"),
                  ("Kučera", "Kučerová"), ("Veselý", "Veselá"), ("Horák", "Horáková"),
                  ("Němec", "Němcová"), ("Pokorný", "Pokorná"), ("Marek", "Marková"),
                  ("Pospíšil", "Pospíšilová"), ("Hájek", "Hájková"), ("Král", "Králová"),
                  ("Jelínek", "Jelínková"), ("Růžička", "Růžičková"), ("Beneš", "Benešová")]),
    "SK": dict(
        male=["Martin", "Peter", "Michal", "Tomáš", "Lukáš", "Juraj", "Marek", "Ján", "Matej",
              "Jakub", "Pavol", "Filip", "Samuel", "Miroslav"],
        female=["Zuzana", "Katarína", "Lucia", "Veronika", "Monika", "Jana", "Martina", "Simona",
                "Petra", "Barbora", "Michaela", "Andrea", "Kristína", "Lenka"],
        surnames=[("Horváth", "Horváthová"), ("Kováč", "Kováčová"), ("Varga", "Vargová"),
                  ("Tóth", "Tóthová"), ("Baláž", "Balážová"), ("Molnár", "Molnárová"),
                  ("Lukáč", "Lukáčová"), ("Novák", "Nováková"), ("Kráľ", "Kráľová"),
                  ("Hudák", "Hudáková"), ("Polák", "Poláková"), ("Kollár", "Kollárová"),
                  ("Oravec", "Oravcová"), ("Šimko", "Šimková")]),
    "HU": dict(
        male=["Bence", "Máté", "Dávid", "Balázs", "Gergő", "Péter", "Tamás", "Zoltán", "Gábor",
              "Ádám", "Levente", "László", "Attila", "Dániel", "Márton", "Krisztián"],
        female=["Anna", "Eszter", "Réka", "Zsófia", "Katalin", "Fanni", "Dóra", "Nóra", "Kinga",
                "Viktória", "Judit", "Petra", "Lilla", "Boglárka", "Ágnes", "Krisztina"],
        surnames=["Nagy", "Kovács", "Tóth", "Szabó", "Horváth", "Varga", "Kiss", "Molnár", "Németh",
                  "Farkas", "Balogh", "Papp", "Takács", "Juhász", "Lakatos", "Mészáros", "Oláh",
                  "Simon", "Rácz", "Fekete"]),
    "RO": dict(
        male=["Andrei", "Alexandru", "Mihai", "Ionuț", "Cristian", "Bogdan", "Radu", "Vlad",
              "Adrian", "Florin", "Ștefan", "Gabriel", "Sorin", "Cătălin", "Dan", "Răzvan"],
        female=["Andreea", "Elena", "Ioana", "Maria", "Alexandra", "Cristina", "Diana", "Mihaela",
                "Raluca", "Roxana", "Bianca", "Oana", "Gabriela", "Irina", "Simona", "Adina"],
        surnames=["Popescu", "Ionescu", "Popa", "Pop", "Dumitru", "Stan", "Stoica", "Gheorghe",
                  "Rusu", "Munteanu", "Matei", "Constantin", "Șerban", "Moldovan", "Lungu", "Ene",
                  "Marin", "Tudor", "Dobre", "Barbu", "Nistor", "Florea"]),
    "BG": dict(
        male=["Georgi", "Ivan", "Dimitar", "Nikolay", "Hristo", "Stoyan", "Martin", "Aleksandar",
              "Petar", "Todor", "Viktor", "Kaloyan", "Boris", "Yordan"],
        female=["Maria", "Ivana", "Elena", "Desislava", "Gergana", "Viktoria", "Yana",
                "Tsvetelina", "Radostina", "Nadezhda", "Teodora", "Kristina", "Mila", "Petya"],
        surnames=[("Ivanov", "Ivanova"), ("Georgiev", "Georgieva"), ("Dimitrov", "Dimitrova"),
                  ("Petrov", "Petrova"), ("Nikolov", "Nikolova"), ("Hristov", "Hristova"),
                  ("Stoyanov", "Stoyanova"), ("Todorov", "Todorova"), ("Iliev", "Ilieva"),
                  ("Vasilev", "Vasileva"), ("Atanasov", "Atanasova"), ("Petkov", "Petkova"),
                  ("Angelov", "Angelova"), ("Kolev", "Koleva"), ("Yordanov", "Yordanova"),
                  ("Marinov", "Marinova")]),
    "HR": dict(
        male=["Luka", "Ivan", "Marko", "Josip", "Filip", "Matej", "Ante", "Petar", "Tomislav",
              "Domagoj", "Karlo", "Mario", "Igor", "Dario"],
        female=["Ana", "Ivana", "Petra", "Marija", "Lucija", "Maja", "Martina", "Katarina", "Iva",
                "Nikolina", "Josipa", "Mia", "Tena", "Lana"],
        surnames=["Horvat", "Kovačević", "Babić", "Marić", "Jurić", "Novak", "Kovačić", "Knežević",
                  "Vuković", "Marković", "Petrović", "Matić", "Tomić", "Pavlović", "Božić",
                  "Blažević", "Grgić", "Pavić"]),
    "SI": dict(
        male=["Luka", "Jan", "Žiga", "Matej", "Nejc", "Rok", "Gregor", "Miha", "Andraž", "Tadej",
              "Jure", "Blaž"],
        female=["Maja", "Nina", "Eva", "Ana", "Tjaša", "Urška", "Nika", "Špela", "Katja", "Petra",
                "Mojca", "Anja"],
        surnames=["Novak", "Horvat", "Kovačič", "Krajnc", "Zupančič", "Potočnik", "Kovač",
                  "Mlakar", "Kos", "Vidmar", "Golob", "Turk", "Kralj", "Božič", "Korošec", "Bizjak"]),
    "RS": dict(
        male=["Nikola", "Stefan", "Marko", "Luka", "Milan", "Aleksandar", "Nemanja", "Miloš",
              "Dušan", "Vuk", "Ognjen", "Filip", "Đorđe", "Uroš"],
        female=["Milica", "Jelena", "Ana", "Marija", "Jovana", "Teodora", "Katarina", "Ivana",
                "Tamara", "Nevena", "Dragana", "Sanja", "Mina", "Tijana"],
        surnames=["Jovanović", "Petrović", "Nikolić", "Marković", "Đorđević", "Stojanović", "Ilić",
                  "Stanković", "Pavlović", "Popović", "Živković", "Todorović", "Kostić", "Ristić",
                  "Lazić", "Janković", "Mitrović"]),
    "GR": dict(
        male=["Giorgos", "Dimitris", "Kostas", "Nikos", "Giannis", "Christos", "Panos",
              "Alexandros", "Vasilis", "Thanos", "Stavros", "Michalis", "Vangelis", "Spyros"],
        female=["Maria", "Eleni", "Katerina", "Sofia", "Georgia", "Dimitra", "Ioanna", "Christina",
                "Despina", "Irene", "Konstantina", "Anna", "Vasiliki", "Natalia"],
        surnames=[("Papadopoulos", "Papadopoulou"), "Georgiou", "Nikolaou", ("Papadakis", "Papadaki"),
                  "Oikonomou", ("Vlachos", "Vlachou"), ("Karagiannis", "Karagianni"),
                  ("Pappas", "Pappa"), "Antoniou", "Dimitriou", ("Konstantinidis", "Konstantinidou"),
                  ("Makris", "Makri"), ("Ioannidis", "Ioannidou"), "Alexiou",
                  ("Michailidis", "Michailidou"), "Christodoulou", "Theodorou",
                  ("Angelopoulos", "Angelopoulou")]),
    "CY": dict(
        male=["Andreas", "Christos", "Giorgos", "Marios", "Nicos", "Panayiotis", "Constantinos",
              "Stelios"],
        female=["Maria", "Eleni", "Andri", "Christina", "Despo", "Marina", "Georgia", "Stella"],
        surnames=["Georgiou", "Ioannou", "Charalambous", "Constantinou", "Kyriacou", "Panayiotou",
                  "Christodoulou", "Andreou", "Savva", "Nicolaou", "Hadjipetrou"]),
    "LT": dict(
        male=["Lukas", "Mantas", "Tomas", "Paulius", "Justas", "Dovydas", "Andrius", "Darius",
              "Mindaugas", "Karolis", "Vytautas", "Jonas"],
        female=["Gabija", "Ieva", "Greta", "Rūta", "Agnė", "Eglė", "Monika", "Lina", "Justina",
                "Kristina", "Aistė", "Austėja"],
        surnames=[("Kazlauskas", "Kazlauskienė", "Kazlauskaitė"),
                  ("Jankauskas", "Jankauskienė", "Jankauskaitė"),
                  ("Petrauskas", "Petrauskienė", "Petrauskaitė"),
                  ("Stankevičius", "Stankevičienė", "Stankevičiūtė"),
                  ("Vasiliauskas", "Vasiliauskienė", "Vasiliauskaitė"),
                  ("Žukauskas", "Žukauskienė", "Žukauskaitė"),
                  ("Butkus", "Butkienė", "Butkutė"),
                  ("Paulauskas", "Paulauskienė", "Paulauskaitė"),
                  ("Urbonas", "Urbonienė", "Urbonaitė"),
                  ("Navickas", "Navickienė", "Navickaitė")]),
    "LV": dict(
        male=["Jānis", "Andris", "Mārtiņš", "Kārlis", "Edgars", "Artūrs", "Roberts", "Ričards",
              "Kristaps", "Raimonds", "Aivars", "Dāvis"],
        female=["Anna", "Laura", "Līga", "Ilze", "Kristīne", "Elīna", "Inese", "Dace", "Zane",
                "Sanita", "Agnese", "Evija"],
        surnames=[("Bērziņš", "Bērziņa"), ("Kalniņš", "Kalniņa"), ("Ozols", "Ozola"),
                  ("Jansons", "Jansone"), ("Ozoliņš", "Ozoliņa"), ("Liepiņš", "Liepiņa"),
                  ("Krūmiņš", "Krūmiņa"), ("Balodis", "Balode"), ("Eglītis", "Eglīte"),
                  ("Zariņš", "Zariņa"), ("Pētersons", "Pētersone"), ("Vītols", "Vītola")]),
    "EE": dict(
        male=["Martin", "Rasmus", "Markus", "Karl", "Kristjan", "Andres", "Tanel", "Siim", "Priit",
              "Rain", "Mihkel", "Kaspar"],
        female=["Maria", "Laura", "Kadri", "Kristiina", "Triin", "Liis", "Kertu", "Merilin", "Anu",
                "Helen", "Katrin", "Eliise"],
        surnames=["Tamm", "Saar", "Sepp", "Mägi", "Kask", "Kukk", "Rebane", "Ilves", "Pärn",
                  "Koppel", "Lepik", "Oja", "Luik", "Lepp", "Kuusk"]),
    "UA": dict(
        male=["Oleksandr", "Andrii", "Dmytro", "Serhii", "Maksym", "Volodymyr", "Mykola", "Ivan",
              "Artem", "Bohdan", "Taras", "Yurii", "Vladyslav", "Denys", "Oleh", "Roman"],
        female=["Olena", "Iryna", "Nataliia", "Tetiana", "Kateryna", "Oksana", "Yuliia",
                "Anastasiia", "Viktoriia", "Mariia", "Anna", "Sofiia", "Daryna", "Khrystyna",
                "Alina", "Svitlana"],
        surnames=["Melnyk", "Shevchenko", "Kovalenko", "Bondarenko", "Boiko", "Tkachenko",
                  "Kravchenko", "Kovalchuk", "Koval", "Oliinyk", "Shevchuk", "Polishchuk",
                  "Lysenko", "Rudenko", "Savchenko", "Marchenko", "Moroz", "Petrenko",
                  ("Kovalskyi", "Kovalska"), ("Levytskyi", "Levytska"), "Hnatiuk", "Romaniuk"]),
    "LU": dict(
        male=["Luc", "Marc", "Tom", "Yves", "Laurent", "Pit", "Ben", "Gilles", "Paul", "Jeff"],
        female=["Anne", "Claire", "Sophie", "Nathalie", "Sandra", "Laura", "Julie", "Carole",
                "Martine", "Lea"],
        surnames=["Schmit", "Muller", "Weber", "Wagner", "Hoffmann", "Thill", "Schroeder", "Klein",
                  "Kremer", "Reuter", "Schiltz", "Majerus", "Welter", "Feller"]),
    "MT": dict(
        male=["Matthew", "Luke", "Jean", "Karl", "Daniel", "Andrew", "Jake", "Mark", "Clayton",
              "Kurt"],
        female=["Maria", "Martina", "Nicole", "Claire", "Rachel", "Stephanie", "Francesca",
                "Kimberly", "Charlene", "Elena"],
        surnames=["Borg", "Camilleri", "Vella", "Farrugia", "Zammit", "Galea", "Micallef", "Grech",
                  "Attard", "Spiteri", "Azzopardi", "Mifsud", "Pace", "Agius", "Cassar", "Caruana"]),
    # --- diaspora / expat pools -------------------------------------------- #
    "TR": dict(
        male=["Mehmet", "Mustafa", "Ahmet", "Emre", "Can", "Burak", "Murat", "Cem", "Deniz",
              "Kerem", "Serkan", "Onur", "Yusuf", "Hakan"],
        female=["Ayşe", "Elif", "Zeynep", "Merve", "Selin", "Esra", "Derya", "Özlem", "Büşra",
                "Aylin", "Melike", "Ebru", "Gizem", "Deniz"],
        surnames=["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk",
                  "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç",
                  "Kurt", "Özkan", "Şimşek"]),
    "MAGHREB": dict(
        male=["Mehdi", "Karim", "Yassine", "Nabil", "Samir", "Rachid", "Sofiane", "Bilal",
              "Amine", "Youssef", "Hamza", "Ilyes", "Anis", "Walid"],
        female=["Nadia", "Samira", "Leïla", "Yasmine", "Sarah", "Inès", "Myriam", "Sonia", "Amel",
                "Nora", "Imane", "Salma", "Lina", "Rania"],
        surnames=["Benali", "Haddad", "Bouzid", "Belkacem", "Mansouri", "Amrani", "Cherif",
                  "Saidi", "El Idrissi", "Bennani", "Ouali", "Brahimi", "Hamdi", "Meziane",
                  "Boukhari", "El Amrani", "Azzouzi", "Rahmouni"]),
    "SOUTH_ASIAN": dict(
        male=["Arjun", "Rohan", "Amit", "Rahul", "Imran", "Vikram", "Sanjay", "Ravi", "Hassan",
              "Kiran", "Nikhil", "Aamir", "Sunil", "Zain"],
        female=["Priya", "Anjali", "Sana", "Aisha", "Neha", "Pooja", "Ayesha", "Kavita", "Meera",
                "Fatima", "Simran", "Divya", "Nisha", "Zara"],
        surnames=["Patel", "Shah", "Khan", ("Singh", "Kaur"), "Sharma", "Ahmed", "Hussain",
                  "Mistry", "Gupta", "Chaudhry", "Malik", "Iqbal", "Desai", "Mehta", "Rahman"]),
    "IN": dict(
        male=["Arjun", "Rohan", "Amit", "Rahul", "Vikram", "Sanjay", "Karthik", "Aditya",
              "Siddharth", "Nikhil", "Pranav", "Varun", "Anand", "Suresh"],
        female=["Priya", "Anjali", "Neha", "Pooja", "Kavya", "Divya", "Shruti", "Aishwarya",
                "Sneha", "Lakshmi", "Deepika", "Ananya", "Meera", "Ritu"],
        surnames=["Sharma", "Iyer", "Nair", "Reddy", "Patel", "Gupta", "Kumar", "Rao", "Menon",
                  "Joshi", "Kulkarni", "Banerjee", "Chatterjee", "Pillai", "Deshpande", "Srinivasan"]),
    "ARABIC": dict(
        male=["Ahmad", "Omar", "Ali", "Mohammed", "Khaled", "Tarek", "Hussein", "Rami", "Fadi",
              "Sami", "Ammar", "Bashar"],
        female=["Rana", "Lina", "Hiba", "Dima", "Nour", "Yara", "Rasha", "Maya", "Layla", "Reem",
                "Hala", "Aya"],
        surnames=["Al-Hassan", "Haddad", "Khalil", "Nasser", "Mansour", "Saleh", "Hamdan",
                  "Darwish", "Abboud", "Khoury", "Aziz", "Ibrahim", "Youssef", "Jaber", "Suleiman"]),
    "BR": dict(
        male=["Lucas", "Gabriel", "Rafael", "Thiago", "Matheus", "Felipe", "Gustavo", "Leonardo",
              "Bruno", "Diego", "Rodrigo", "Vinícius"],
        female=["Juliana", "Fernanda", "Camila", "Amanda", "Letícia", "Beatriz", "Larissa",
                "Gabriela", "Mariana", "Carolina", "Bruna", "Isabela"],
        surnames=["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues",
                  "Almeida", "Nascimento", "Carvalho", "Araújo", "Ribeiro", "Barbosa", "Rocha",
                  "Cardoso"]),
    "US": dict(
        male=["Michael", "David", "Chris", "Ryan", "Josh", "Tyler", "Kevin", "Brian", "Jason",
              "Andrew"],
        female=["Jessica", "Ashley", "Megan", "Lauren", "Katie", "Amanda", "Sarah", "Rachel",
                "Emily", "Nicole"],
        surnames=["Miller", "Johnson", "Anderson", "Nguyen", "Rodriguez", "Walker", "Mitchell",
                  "Carter", "Reed", "Collins", "Brooks", "Kim", "Sullivan"]),
    "RU": dict(
        male=["Aleksandr", "Dmitri", "Sergei", "Andrei", "Maksim", "Artjom", "Ilja", "Nikita",
              "Pavel", "Vladislav", "Jevgeni", "Roman"],
        female=["Anastasia", "Jekaterina", "Olga", "Natalja", "Julia", "Tatjana", "Irina",
                "Darja", "Marina", "Kristina", "Viktoria", "Jelena"],
        surnames=[("Ivanov", "Ivanova"), ("Petrov", "Petrova"), ("Smirnov", "Smirnova"),
                  ("Kuznetsov", "Kuznetsova"), ("Popov", "Popova"), ("Sokolov", "Sokolova"),
                  ("Volkov", "Volkova"), ("Morozov", "Morozova"), ("Pavlov", "Pavlova"),
                  ("Fjodorov", "Fjodorova")]),
}

# Language that goes with a surname in the South Asian / Indian pools.
SURNAME_LANGUAGE = {
    "Iyer": "Tamil", "Srinivasan": "Tamil", "Nair": "Malayalam", "Menon": "Malayalam", "Pillai": "Malayalam",
    "Reddy": "Telugu", "Rao": "Telugu", "Kulkarni": "Marathi", "Deshpande": "Marathi", "Joshi": "Marathi",
    "Banerjee": "Bengali", "Chatterjee": "Bengali", "Rahman": "Bengali", "Sharma": "Hindi", "Gupta": "Hindi",
    "Kumar": "Hindi", "Patel": "Gujarati", "Shah": "Gujarati", "Mistry": "Gujarati", "Desai": "Gujarati",
    "Mehta": "Gujarati", "Khan": "Urdu", "Ahmed": "Urdu", "Hussain": "Urdu", "Chaudhry": "Punjabi",
    "Malik": "Urdu", "Iqbal": "Urdu", "Singh": "Punjabi", "Kaur": "Punjabi",
}

# Country code -> default name pool (for countries not using per-city pools).
DEFAULT_POOL = {code: code for code in COUNTRIES if code in NAME_POOLS}
DEFAULT_POOL.update({"CH": "CH_DE", "BE": "BE_NL"})

# Country-flavoured hobbies mixed into the generic list.
COUNTRY_HOBBIES = {
    "NO": ["cross-country skiing"], "AT": ["skiing", "mountain hiking"], "CH": ["skiing", "hiking in the Alps"],
    "NL": ["cycling", "korfball"], "DK": ["sailing", "cycling"], "SE": ["sailing", "forest walks"],
    "FI": ["sauna evenings", "ice swimming"], "ES": ["padel", "football"], "PT": ["surfing", "football"],
    "IT": ["cooking for friends", "football"], "UK": ["pub quizzes", "football"], "IE": ["GAA", "hillwalking"],
    "IS": ["hiking", "swimming in hot pots"], "GR": ["sailing", "beach volleyball"],
    "PL": ["mountain hiking", "volleyball"], "CZ": ["hiking", "ice hockey"], "FR": ["cycling", "wine tasting"],
    "DE": ["cycling", "hiking"], "BE": ["cycling", "comic books"], "HR": ["sailing", "water polo"],
    "SI": ["climbing", "hiking"], "LT": ["basketball"], "LV": ["ice hockey"], "EE": ["cross-country skiing"],
}
