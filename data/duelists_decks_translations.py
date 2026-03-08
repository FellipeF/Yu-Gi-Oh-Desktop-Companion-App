DUELISTS_DECKS_TRANSLATIONS = {
    "Yugi Muto": {
        "friendship": {
            "en": "Friendship",
            "pt": "Amizade",
        },
        "magic_darkness": {
            "en": "Magic Darkness",
            "pt": "Escuridão Mágica",
        },
        "give_you_courage": {
            "en": "Give You Courage",
            "pt": "A Coragem Esteja Contigo",
        },
        "magic_darkness_v1": {
            "en": "Magic Darkness v1",
            "pt": "Escuridão Mágica v1",
        },
        "magic_darkness_v2": {
            "en": "Magic Darkness v2",
            "pt": "Escuridão Mágica v2",
        },
        "magnet_power": {
            "en": "Magnet Power",
            "pt": "Poder Magnético",
        },
        "magic_time": {
            "en": "Magic Time",
            "pt": "Hora da Magia",
        },
        "true_friends": {
            "en": "True Friends",
            "pt": "Amigos de Verdade",
        },
        "gx_past": {
            "en": "GX / Past",
            "pt": "GX / Passado",
        },
        "gx_present": {
            "en": "GX / Present",
            "pt": "GX / Presente",
        },
        "bonds_beyond_time_teaser": {
            "en": "3D Bonds Beyond Time - Teaser",
            "pt": "Prévia - Vínculos Além do Tempo",
        },
    },
    "Seto Kaiba": {
        "childhood_deck": {
            "en": "Childhood Deck",
            "pt": "Deck da Infância",
        },
        "test_deck": {
            "en": "Test Deck",
            "pt": "Deck de Testes",
        },
        "first_briefcase": {
            "en": "First Briefcase",
            "pt": "Primeira Maleta",
        },
        "second_briefcase": {
            "en": "Second Briefcase",
            "pt": "Segunda Maleta",
        },
        "third_briefcase": {
            "en": "Third Briefcase",
            "pt": "Terceira Maleta",
        },
        "fourth_briefcase": {
            "en": "Fourth Briefcase",
            "pt": "Quarta Maleta",
        },
        "fifth_briefcase": {
            "en": "Fifth Briefcase",
            "pt": "Quinta Maleta",
        },
        "manga_test_deck": {
            "en": "Manga - Test Deck",
            "pt": "Mangá - Deck de Testes",
        },
        "blue_eyes_burst": {
            "en": "Blue-Eyes Burst",
            "pt": "Rajada de Olhos Azuis",
        },
        "fist_of_fury": {
            "en": "Fist of Fury",
            "pt": "Punho da Fúria",
        },
        "kaiser_impact": {
            "en": "Kaiser Impact",
            "pt": "Impacto Kaiser",
        },
        "obelisk_impact": {
            "en": "Obelisk Impact",
            "pt": "Impacto Obelisco",
        },
        "ruinous_beast": {
            "en": "Ruinous Beast",
            "pt": "Besta Ruinosa",
        },
        "noble_soul": {
            "en": "Noble Soul",
            "pt": "Alma Nobre",
        },
        "pulse_of_trishula": {
            "en": "Pulse of Trishula",
            "pt": "Pulso de Trishula",
        },
    },
    "Joey Wheeler": {
        "amateur": {
            "en": "Amateur",
            "pt": "Amador",
        },
        "phantom_pyramid": {
            "en": "Phantom Pyramid",
            "pt": "Pirâmide Fantasma",
        },
        "reshef_possessed": {
            "en": "Reshef of Destruction - Possessed",
            "pt": "Rexefe da Destruição - Possuído",
        },
        "warrior_max": {
            "en": "Warrior Max",
            "pt": "Guerreiro Máximo",
        },
        "display_of_courage": {
            "en": "Display of Courage",
            "pt": "Mostra de Coragem",
        },
        "ideal_partner": {
            "en": "Ideal Partner",
            "pt": "Parceiro Ideal",
        },
        "dice_power": {
            "en": "Dice Power",
            "pt": "Poder dos Dados",
        },
        "power_of_luck": {
            "en": "Power of Luck",
            "pt": "Poder da Sorte",
        },
        "warrior_max_v1": {
            "en": "Warrior Max v1",
            "pt": "Guerreiro Máximo v1",
        },
        "warrior_max_v2": {
            "en": "Warrior Max v2",
            "pt": "Guerreiro Máximo v2",
        },
        "super_warrior": {
            "en": "Super Warrior",
            "pt": "Super Guerreiro",
        },
        "duel_gambler": {
            "en": "Duel Gambler",
            "pt": "Duelista Apostador",
        },
    },
    "Solomon Muto": {
        "grandpa": {
            "en": "Grandpa",
            "pt": "Vovô",
        },
        "casket_guardian": {
            "en": "Casket Guardian",
            "pt": "Guardião do Caixão",
        },
        "ancient_pharaoh_v1": {
            "en": "Ancient Pharaoh v1",
            "pt": "Faraó Antigo v1",
        },
        "ancient_pharaoh_v2": {
            "en": "Ancient Pharaoh v2",
            "pt": "Faraó Antigo v2",
        },
        "apnarg_tactics": {
            "en": "Apnarg Tactics",
            "pt": "Táticas Apnarg",
        },
    },
}

def translate_deck(character: str, deck_key: str, lang: str, default_lang: str="en") -> str:
    character_data = DUELISTS_DECKS_TRANSLATIONS.get(character)

    if not character_data:
        return deck_key

    deck_data = character_data.get(deck_key)

    if not deck_data:
        return deck_key

    return deck_data.get(lang, deck_data.get(default_lang, deck_key))
