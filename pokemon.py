class RatePokemon:
    # Pokemon ordered by category, reverse mapping used for O(1) lookup efficiency.
    pokemon = {'Bulbasaur': 'Ingredients', 'Ivysaur': 'Ingredients', 'Venasaur': 'Ingredients',
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
               'Slakoth': 'Berries', 'Vigoroth': 'Berries', 'Slaking': 'Berries',
               'Sableye': 'Skills',
               'Gulpin': 'Skills', 'Swalot': 'Skills',
               'Swablu': 'Berries', 'Altaria': 'Berries',
               'Absol': 'Ingredients',
               'Wynaut': 'Skills',
               'Spheal': 'Berries', 'Sealeo': 'Berries', 'Walrein': 'Berries',
               'Bonsly': 'Skills',
               'Riolu': 'Skills', 'Lucario': 'Skills',
               'Croagunk': 'Ingredients', 'Toxicroak': 'Ingredients',
               'Magnezone': 'Skills',
               'Togekiss': 'Skills',
               'Leafeon': 'Skills', 'Glaceon': 'Skills', 'Sylveon': 'Skills'}
    # 'Mime Jr.': '', 'Mr. Mime': ''

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

    # Subskills rated by category. [0] = Berries, [1] = Ingredients, [2] = Skills.
    subskills = {'Berry Finding S': [5, 4, 5], 'Dream Shard Bonus': [2, 2, 2],
                 'Energy Recovery Bonus': [3, 3, 3], 'Energy Recovery S': [], 'Energy Recovery M': [],
                 'Helping Bonus': [5, 5, 5], 'Helping Speed S': [3, 3, 3], 'Helping Speed M': [4, 4, 4],
                 'Ingredient Finder S': [1, 4, 3], 'Ingredient Finder M': [1, 5, 4],
                 'Inventory Up S': [2, 3, 2], 'Inventory Up M': [3, 4, 3], 'Inventory Up L': [4, 5, 4],
                 'Research EXP Bonus': [2, 2, 2],
                 'Skill Level Up S': [3, 3, 4], 'Skill Level Up M': [4, 4, 5],
                 'Skill Trigger S': [3, 3, 4], 'Skill Trigger M': [4, 4, 5],
                 'Sleep EXP Bonus': [3, 3, 3]}

    def __init__(self, name, nature, skills):
        self.name = name
        self.nature = nature
        self.skills = skills
        self.nature_rating = 0
        self.skills_rating = 0

    def get_stats(self):
        print(self.name, self.nature, self.skills)

    def berries_subskills(self):
        for i in self.skills:
            self.skills_rating += RatePokemon.subskills[i][0]
        return self.skills_rating

    def ingredients_subskills(self):
        for i in self.skills:
            self.skills_rating += RatePokemon.subskills[i][1]
        return self.skills_rating

    def skills_subskills(self):
        for i in self.skills:
            self.skills_rating += RatePokemon.subskills[i][2]
        return self.skills_rating

    def get_specialty(self):
        return RatePokemon.pokemon.get(self.name)

    def grading_scale(self, grade):
        if grade <= 11.0:
            return 'F! <:imheeout:459249961310093316>'
        elif 12.0 <= grade <= 14.0:
            return 'D! <:thisisfine:835775058969362472>'
        elif 15.0 <= grade <= 17.0:
            return 'C! <:gigi:829096353173864508>'
        elif 18.0 <= grade <= 20.0:
            return 'B! <:ricekek:644009566622842921>'
        elif 21.0 <= grade <= 23.0:
            return 'A! <:thumbsupcat:424037436725788673>'
        else:
            return 'S+! <:index:588105844072251392>'

    def rate_pokemon(self):
        specialty = self.get_specialty()
        if specialty == 'Berries':
            self.nature_rating = RatePokemon.natures[self.nature][0]
            grade = self.berries_subskills() + self.nature_rating
        elif specialty == 'Ingredients':
            self.nature_rating = RatePokemon.natures[self.nature][1]
            grade = self.ingredients_subskills() + self.nature_rating
        elif specialty == 'Skills':
            self.nature_rating = RatePokemon.natures[self.nature][2]
            grade = self.skills_subskills() + self.nature_rating
        else:
            return 'Pokémon not found. Please check image upload.'
        return 'Your Pokémon is rated ' + self.grading_scale(grade) + '\nSubskills: ' \
            + str(self.skills_rating) + ' + Nature: ' + str(self.nature_rating) + ' = ' + str(grade)



# obj = RatePokemon(*detect_text_uri('https://cdn.discordapp.com/attachments/1056493099649597491/1149879618195685457/Screenshot_20230908_174928_Pokmon_Sleep.jpg'))
# name = 'Spheal'
# nature = 'Impish'
# skills = ['Energy Recovery Bonus', 'Inventory Up S', 'Helping Speed M', 'Inventory Up L', 'Skill Trigger S']
# obj = RatePokemon(name, nature, skills)
#
# print(obj.rate_pokemon())