class RatePokemon:
    # Pokemon mapped to primary specialty. Expanded to cover Gen 1-6 roster in Pokémon Sleep.
    pokemon = {
        # GEN 1
        'Bulbasaur': 'Ingredients', 'Ivysaur': 'Ingredients', 'Venusaur': 'Ingredients',
        'Charmander': 'Ingredients', 'Charmeleon': 'Ingredients', 'Charizard': 'Ingredients',
        'Squirtle': 'Ingredients', 'Wartortle': 'Ingredients', 'Blastoise': 'Ingredients',
        'Caterpie': 'Berries', 'Metapod': 'Berries', 'Butterfree': 'Berries',
        'Rattata': 'Berries', 'Raticate': 'Berries',
        'Ekans': 'Berries', 'Arbok': 'Berries',
        'Pikachu': 'Berries', 'Raichu': 'Berries',
        'Jigglypuff': 'Skills', 'Wigglytuff': 'Skills',
        'Diglett': 'Ingredients', 'Dugtrio': 'Ingredients',
        'Meowth': 'Skills', 'Persian': 'Skills',
        'Psyduck': 'Skills', 'Golduck': 'Skills',
        'Mankey': 'Berries', 'Primeape': 'Berries',
        'Growlithe': 'Skills', 'Arcanine': 'Skills',
        'Bellsprout': 'Ingredients', 'Weepinbell': 'Ingredients', 'Victreebel': 'Ingredients',
        'Geodude': 'Ingredients', 'Graveler': 'Ingredients', 'Golem': 'Ingredients',
        'Slowpoke': 'Skills', 'Slowbro': 'Skills',
        'Magnemite': 'Skills', 'Magneton': 'Skills',
        'Doduo': 'Berries', 'Dodrio': 'Berries',
        'Gastly': 'Ingredients', 'Haunter': 'Ingredients', 'Gengar': 'Ingredients',
        'Cubone': 'Berries', 'Marowak': 'Berries',
        'Kangaskhan': 'Ingredients',
        'Pinsir': 'Ingredients',
        'Ditto': 'Ingredients',
        'Eevee': 'Skills', 'Vaporeon': 'Skills', 'Jolteon': 'Skills', 'Flareon': 'Skills',
        # GEN 2
        'Chikorita': 'Berries', 'Bayleef': 'Berries', 'Meganium': 'Berries',
        'Cyndaquil': 'Berries', 'Quilava': 'Berries', 'Typhlosion': 'Berries',
        'Totodile': 'Berries', 'Croconaw': 'Berries', 'Feraligatr': 'Berries',
        'Pichu': 'Berries',
        'Igglybuff': 'Skills',
        'Togepi': 'Skills', 'Togetic': 'Skills',
        'Mareep': 'Skills', 'Flaaffy': 'Skills', 'Ampharos': 'Skills',
        'Sudowoodo': 'Skills',
        'Espeon': 'Skills', 'Umbreon': 'Skills',
        'Slowking': 'Skills',
        'Wobbuffet': 'Skills',
        'Heracross': 'Skills',
        'Houndour': 'Berries', 'Houndoom': 'Berries',
        'Larvitar': 'Ingredients', 'Pupitar': 'Ingredients', 'Tyranitar': 'Ingredients',
        # GEN 3
        'Treecko': 'Berries', 'Grovyle': 'Berries', 'Sceptile': 'Berries',
        'Torchic': 'Ingredients', 'Combusken': 'Ingredients', 'Blaziken': 'Ingredients',
        'Mudkip': 'Berries', 'Marshtomp': 'Berries', 'Swampert': 'Berries',
        'Lotad': 'Ingredients', 'Lombre': 'Ingredients', 'Ludicolo': 'Ingredients',
        'Ralts': 'Skills', 'Kirlia': 'Skills', 'Gardevoir': 'Skills',
        'Shroomish': 'Ingredients', 'Breloom': 'Ingredients',
        'Slakoth': 'Berries', 'Vigoroth': 'Berries', 'Slaking': 'Berries',
        'Sableye': 'Skills',
        'Electrike': 'Berries', 'Manectric': 'Berries',
        'Gulpin': 'Skills', 'Swalot': 'Skills',
        'Corphish': 'Ingredients', 'Crawdaunt': 'Ingredients',
        'Lileep': 'Ingredients', 'Cradily': 'Ingredients',
        'Absol': 'Ingredients',
        'Swablu': 'Berries', 'Altaria': 'Berries',
        'Trapinch': 'Berries', 'Vibrava': 'Berries', 'Flygon': 'Berries',
        'Wynaut': 'Skills',
        'Spheal': 'Berries', 'Sealeo': 'Berries', 'Walrein': 'Berries',
        'Shuppet': 'Berries', 'Banette': 'Berries',
        'Onix': 'Berries', 'Steelix': 'Berries',
        'Delibird': 'Ingredients',
        'Snover': 'Ingredients', 'Abomasnow': 'Ingredients',
        # GEN 4
        'Turtwig': 'Berries', 'Grotle': 'Berries', 'Torterra': 'Berries',
        'Chimchar': 'Skills', 'Monferno': 'Skills', 'Infernape': 'Skills',
        'Piplup': 'Ingredients', 'Prinplup': 'Ingredients', 'Empoleon': 'Ingredients',
        'Budew': 'Ingredients', 'Roselia': 'Ingredients', 'Roserade': 'Ingredients',
        'Mime Jr.': 'Ingredients', 'Mr. Mime': 'Ingredients',
        'Chingling': 'Skills', 'Chimecho': 'Skills',
        'Happiny': 'Skills', 'Chansey': 'Skills', 'Blissey': 'Skills',
        'Bonsly': 'Skills',
        'Munchlax': 'Berries',
        'Mantyke': 'Skills', 'Mantine': 'Skills',
        'Riolu': 'Skills', 'Lucario': 'Skills',
        'Croagunk': 'Ingredients', 'Toxicroak': 'Ingredients',
        'Togekiss': 'Skills',
        'Magnezone': 'Skills',
        'Leafeon': 'Skills', 'Glaceon': 'Skills',
        'Cleffa': 'Berries', 'Clefairy': 'Berries', 'Clefable': 'Berries',
        # GEN 5
        'Snivy': 'Berries', 'Servine': 'Berries', 'Serperior': 'Berries',
        'Tepig': 'Berries', 'Pignite': 'Berries', 'Emboar': 'Berries',
        'Oshawott': 'Ingredients', 'Dewott': 'Ingredients', 'Samurott': 'Ingredients',
        'Lillipup': 'Berries', 'Herdier': 'Berries', 'Stoutland': 'Berries',
        'Dwebble': 'Berries', 'Crustle': 'Berries',
        'Foongus': 'Ingredients', 'Amoonguss': 'Ingredients',
        'Litwick': 'Skills', 'Lampent': 'Skills', 'Chandelure': 'Skills',
        # GEN 6
        'Chespin': 'Berries', 'Quilladin': 'Berries', 'Chesnaught': 'Berries',
        'Fennekin': 'Skills', 'Braixen': 'Skills', 'Delphox': 'Skills',
        'Froakie': 'Ingredients', 'Frogadier': 'Ingredients', 'Greninja': 'Ingredients',
        'Dedenne': 'Skills',
        'Sylveon': 'Skills',
    }

    # Nature rated by category. [0] = Berries, [1] = Ingredients, [2] = Skills.
    natures = {'Hardy': [1.00, 1.00, 1.00], 'Lonely': [1.00, 1.00, 0.67], 'Brave': [1.67, 1.67, 1.67],
               'Adamant': [3.00, -0.17, 0.67], 'Naughty': [1.83, 1.67, -0.17],
               'Bold': [-1.33, -1.33, -1.00], 'Docile': [1.00, 1.00, 1.00], 'Relaxed': [-0.67, -0.67, -0.33],
               'Impish': [1.50, -1.33, -0.17], 'Lax': [0.17, 0.17, -1.00],
               'Timid': [-1.00, -1.00, -1.00], 'Hasty': [0.33, 0.33, 0], 'Serious': [1.00, 1.00, 1.00],
               'Jolly': [2.17, -1.00, 0.17], 'Naive': [0.83, 0.58, -1.00],
               'Modest': [-1.67, 0.50, -0.33], 'Mild': [-1.00, 1.17, 0], 'Quiet': [-0.67, 2.00, 1.00],
               'Bashful': [1.00, 1.00, 1.00], 'Rash': [-0.50, 2.00, -0.67],
               'Calm': [-0.67, -0.67, 0.67], 'Gentle': [-0.33, 0.33, 1.33], 'Sassy': [0, 0.25, 1.67],
               'Careful': [1.50, -1.00, 1.33], 'Quirky': [1.00, 1.00, 1.00]}

    # Subskill ratings per specialty. [0] = Berries, [1] = Ingredients, [2] = Skills.
    # Energy Recovery S/M filled in; values follow the same S < M tier pattern as other subskills.
    subskills = {'Berry Finding S': [5, 4, 5], 'Dream Shard Bonus': [2, 2, 2],
                 'Energy Recovery Bonus': [3, 3, 3], 'Energy Recovery S': [2, 2, 2], 'Energy Recovery M': [3, 3, 3],
                 'Helping Bonus': [5, 5, 5], 'Helping Speed S': [3, 3, 3], 'Helping Speed M': [4, 4, 4],
                 'Ingredient Finder S': [1, 4, 3], 'Ingredient Finder M': [1, 5, 4],
                 'Inventory Up S': [2, 3, 2], 'Inventory Up M': [3, 4, 3], 'Inventory Up L': [4, 5, 4],
                 'Research EXP Bonus': [2, 2, 2],
                 'Skill Level Up S': [3, 3, 4], 'Skill Level Up M': [4, 4, 5],
                 'Skill Trigger S': [3, 3, 4], 'Skill Trigger M': [4, 4, 5],
                 'Sleep EXP Bonus': [3, 3, 3]}

    # Base helping frequency in seconds at Lv1 (approximate community data).
    # Used for frequency-weighted scoring of speed-sensitive subskills.
    base_frequencies = {
        # GEN 1
        'Bulbasaur': 4320, 'Ivysaur': 4320, 'Venusaur': 4320,
        'Charmander': 4680, 'Charmeleon': 4680, 'Charizard': 4680,
        'Squirtle': 4500, 'Wartortle': 4500, 'Blastoise': 4500,
        'Caterpie': 3060, 'Metapod': 3060, 'Butterfree': 3060,
        'Rattata': 2940, 'Raticate': 2940,
        'Ekans': 3960, 'Arbok': 3960,
        'Pikachu': 3600, 'Raichu': 3600,
        'Jigglypuff': 3840, 'Wigglytuff': 3840,
        'Diglett': 2880, 'Dugtrio': 2880,
        'Meowth': 4080, 'Persian': 4080,
        'Psyduck': 4440, 'Golduck': 4440,
        'Mankey': 3840, 'Primeape': 3840,
        'Growlithe': 4500, 'Arcanine': 4500,
        'Bellsprout': 4200, 'Weepinbell': 4200, 'Victreebel': 4200,
        'Geodude': 4500, 'Graveler': 4500, 'Golem': 4500,
        'Slowpoke': 5760, 'Slowbro': 5760,
        'Magnemite': 5100, 'Magneton': 5100,
        'Doduo': 3480, 'Dodrio': 3480,
        'Gastly': 4320, 'Haunter': 4320, 'Gengar': 4320,
        'Cubone': 3960, 'Marowak': 3960,
        'Kangaskhan': 5460,
        'Pinsir': 4800,
        'Ditto': 5040,
        'Eevee': 4680, 'Vaporeon': 4680, 'Jolteon': 4680, 'Flareon': 4680,
        # GEN 2
        'Chikorita': 4320, 'Bayleef': 4320, 'Meganium': 4320,
        'Cyndaquil': 4680, 'Quilava': 4680, 'Typhlosion': 4680,
        'Totodile': 3960, 'Croconaw': 3960, 'Feraligatr': 3960,
        'Pichu': 3600,
        'Igglybuff': 3840,
        'Togepi': 4320, 'Togetic': 4320,
        'Mareep': 3840, 'Flaaffy': 3840, 'Ampharos': 3840,
        'Sudowoodo': 5400,
        'Espeon': 4680, 'Umbreon': 4680,
        'Slowking': 5760,
        'Wobbuffet': 5040,
        'Heracross': 3120,
        'Houndour': 4080, 'Houndoom': 4080,
        'Larvitar': 4800, 'Pupitar': 4800, 'Tyranitar': 4800,
        # GEN 3
        'Treecko': 3840, 'Grovyle': 3840, 'Sceptile': 3840,
        'Torchic': 4080, 'Combusken': 4080, 'Blaziken': 4080,
        'Mudkip': 3960, 'Marshtomp': 3960, 'Swampert': 3960,
        'Lotad': 4320, 'Lombre': 4320, 'Ludicolo': 4320,
        'Ralts': 4320, 'Kirlia': 4320, 'Gardevoir': 4320,
        'Shroomish': 4920, 'Breloom': 4920,
        'Slakoth': 4800, 'Vigoroth': 4800, 'Slaking': 4800,
        'Sableye': 5040,
        'Electrike': 3840, 'Manectric': 3840,
        'Gulpin': 4320, 'Swalot': 4320,
        'Corphish': 3960, 'Crawdaunt': 3960,
        'Lileep': 5520, 'Cradily': 5520,
        'Absol': 4320,
        'Swablu': 3600, 'Altaria': 3600,
        'Trapinch': 4680, 'Vibrava': 4680, 'Flygon': 4680,
        'Wynaut': 5040,
        'Spheal': 3720, 'Sealeo': 3720, 'Walrein': 3720,
        'Shuppet': 4320, 'Banette': 4320,
        'Onix': 5520, 'Steelix': 5520,
        'Delibird': 4200,
        'Snover': 4920, 'Abomasnow': 4920,
        # GEN 4
        'Turtwig': 4320, 'Grotle': 4320, 'Torterra': 4320,
        'Chimchar': 3840, 'Monferno': 3840, 'Infernape': 3840,
        'Piplup': 4440, 'Prinplup': 4440, 'Empoleon': 4440,
        'Budew': 4320, 'Roselia': 4320, 'Roserade': 4320,
        'Mime Jr.': 4680, 'Mr. Mime': 4680,
        'Chingling': 4320, 'Chimecho': 4320,
        'Happiny': 5040, 'Chansey': 5040, 'Blissey': 5040,
        'Bonsly': 5400,
        'Munchlax': 5040,
        'Mantyke': 3840, 'Mantine': 3840,
        'Riolu': 3480, 'Lucario': 3480,
        'Croagunk': 3960, 'Toxicroak': 3960,
        'Togekiss': 4320,
        'Magnezone': 5100,
        'Leafeon': 4680, 'Glaceon': 4680,
        'Cleffa': 3720, 'Clefairy': 3720, 'Clefable': 3720,
        # GEN 5
        'Snivy': 4320, 'Servine': 4320, 'Serperior': 4320,
        'Tepig': 4320, 'Pignite': 4320, 'Emboar': 4320,
        'Oshawott': 4320, 'Dewott': 4320, 'Samurott': 4320,
        'Lillipup': 3120, 'Herdier': 3120, 'Stoutland': 3120,
        'Dwebble': 3960, 'Crustle': 3960,
        'Foongus': 4320, 'Amoonguss': 4320,
        'Litwick': 4680, 'Lampent': 4680, 'Chandelure': 4680,
        # GEN 6
        'Chespin': 3840, 'Quilladin': 3840, 'Chesnaught': 3840,
        'Fennekin': 4680, 'Braixen': 4680, 'Delphox': 4680,
        'Froakie': 4080, 'Frogadier': 4080, 'Greninja': 4080,
        'Dedenne': 3600,
        'Sylveon': 4680,
    }

    # Subskills whose value scales with helping frequency (faster Pokémon benefit more).
    SPEED_SENSITIVE_SUBSKILLS = frozenset({'Helping Speed S', 'Helping Speed M', 'Berry Finding S'})

    # Maps detection order index → subskill unlock level.
    # The Pokémon Sleep UI uses a two-column layout, so OCR reads subskills as:
    # index 0 = Lv.10, index 1 = Lv.50, index 2 = Lv.100, index 3 = Lv.25, index 4 = Lv.75
    DETECTION_ORDER_LEVELS = [10, 50, 100, 25, 75]

    # Theoretical [min, max] score range per specialty, used for percentile estimation.
    SCORE_RANGES = {
        'Berries': (4.33, 28.0),
        'Ingredients': (11.0, 24.0),
        'Skills': (10.5, 26.0),
    }

    # Baseline frequency (seconds) used as the reference for frequency weighting.
    _BASELINE_FREQ = 4500

    # Fraction of base frequency assumed to be effective at average camp level (~Lv30-50).
    # Used only for the production estimate; does not affect the rating score.
    _PRODUCTION_EFFICIENCY = 0.80

    def __init__(self, name='', nature='', skills=None):
        self.name = name
        self.nature = nature
        if skills is None:
            skills = []
        self.skills = skills
        self.skills_value = {}
        self.nature_rating = 0
        self.skills_rating = 0
        self.locked_skills = set()

    def get_stats(self):
        return self.name, self.nature, self.skills

    def find_specialty(self, results):
        for item in results:
            if item in self.pokemon:
                self.name = item
            if item in self.natures:
                self.nature = item
            if item in self.subskills:
                self.skills.append(item)
        return self.pokemon.get(self.name)

    def _frequency_weight(self):
        """Return a multiplier based on this Pokémon's base helping frequency.

        Faster Pokémon (lower seconds) yield a multiplier > 1, meaning
        speed-sensitive subskills are worth more for them.
        """
        freq = self.base_frequencies.get(self.name)
        if not freq:
            return 1.0
        return self._BASELINE_FREQ / freq

    def _score_subskill(self, subskill, specialty_idx, freq_weight):
        """Return the score for one subskill, applying frequency weighting where relevant."""
        values = RatePokemon.subskills.get(subskill, [])
        if not values:
            return 0
        base = values[specialty_idx]
        if subskill in RatePokemon.SPEED_SENSITIVE_SUBSKILLS:
            return round(base * freq_weight, 2)
        return base

    def _rate_for_specialty(self, specialty, pokemon_level=None):
        """Compute a full rating breakdown for the given specialty.

        Does not mutate instance state so it can be called for all three
        specialties in one pass.

        Returns (grade, nature_rating, skills_value, locked_skills, percentile).
        """
        idx = {'Berries': 0, 'Ingredients': 1, 'Skills': 2}[specialty]
        nature_rating = RatePokemon.natures[self.nature][idx]
        freq_weight = self._frequency_weight()

        skills_rating = 0.0
        skills_value = {}
        locked_skills = set()

        for i, skill in enumerate(self.skills):
            unlock_level = (self.DETECTION_ORDER_LEVELS[i]
                            if i < len(self.DETECTION_ORDER_LEVELS) else 10)
            is_locked = pokemon_level is not None and pokemon_level < unlock_level
            if is_locked:
                skills_value[skill] = 0
                locked_skills.add(skill)
                continue
            score = self._score_subskill(skill, idx, freq_weight)
            skills_value[skill] = score
            skills_rating += score

        grade = round(skills_rating + nature_rating, 2)
        percentile = self._compute_percentile(grade, specialty)
        return grade, nature_rating, skills_value, locked_skills, percentile

    def _compute_percentile(self, grade, specialty):
        """Estimate where this score falls within the theoretical range (0–100)."""
        if specialty not in self.SCORE_RANGES:
            return 50
        min_val, max_val = self.SCORE_RANGES[specialty]
        pct = (grade - min_val) / (max_val - min_val) * 100
        return max(0, min(100, round(pct)))

    def grading_scale(self, grade):
        if grade <= 11.0:
            return '**F**! <a:torchheadbang:1150206226181918720>'
        elif 11.0 < grade <= 14.0:
            return '**D**! <:psyduck:1150207071468388432>'
        elif 14.0 < grade <= 17.0:
            return '**C**! <:flushedtomb:1150206887812419665>'
        elif 17.0 < grade <= 20.0:
            return '**B**! <a:squirtlevibe:1150206216451137586>'
        elif 20.0 < grade <= 23.0:
            return '**A**! <:raichudab:1150207082390368388>'
        else:
            return '**S**! <:gengarshades:1150207094297997332>'

    def rate_pokemon(self, results, pokemon_level=None):
        """Rate the Pokémon described by OCR results.

        Args:
            results: list of text strings returned by detect_text_uri.
            pokemon_level: optional int; if provided, subskills not yet
                unlocked at that level are excluded from the score.

        Returns a dict with all rating data, or False if the Pokémon or
        nature could not be identified.
        """
        specialty = self.find_specialty(results)
        if not specialty or not self.nature:
            return False

        # Primary-specialty rating (also sets instance state for compatibility)
        grade, self.nature_rating, self.skills_value, self.locked_skills, percentile = \
            self._rate_for_specialty(specialty, pokemon_level)
        self.skills_rating = round(grade - self.nature_rating, 2)

        # All-specialty scores for comparison display
        all_scores = {}
        for spec in ('Berries', 'Ingredients', 'Skills'):
            spec_grade, _, _, _, spec_pct = self._rate_for_specialty(spec, pokemon_level)
            all_scores[spec] = {'grade': spec_grade, 'percentile': spec_pct}

        # Rough production estimate: helps per day at ~80% of base frequency
        # (approximates average Lv30–50 Pokémon with typical camp bonuses).
        freq = self.base_frequencies.get(self.name)
        helps_per_day = round(86400 / (freq * self._PRODUCTION_EFFICIENCY)) if freq else None

        return {
            'name': self.name,
            'final_grade': self.grading_scale(grade),
            'skills_value': self.skills_value,
            'locked_skills': self.locked_skills,
            'nature': str(self.nature),
            'nature_rating': str(self.nature_rating),
            'grade': str(grade),
            'percentile': percentile,
            'all_scores': all_scores,
            'helps_per_day': helps_per_day,
            'specialty': specialty,
        }


# Quick smoke-test (uncomment to run locally):
# name = 'Spheal'
# nature = 'Impish'
# skills = ['Energy Recovery Bonus', 'Inventory Up S', 'Helping Speed M', 'Inventory Up L', 'Skill Trigger S']
# obj = RatePokemon(name, nature, skills)
# print(obj.rate_pokemon([], pokemon_level=50))
