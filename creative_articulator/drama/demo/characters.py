from ..data import Character


PECHKIN = Character(
    'Pechkin',
    Character.Gender.Masculine,
    "Pechkin is the postman of Prostokvashino, and the post office is his empire, however small it is. "
    "He knows who wrote to whom, what was in the parcel, how much it weighed and what that says about a person, "
    "and he considers this knowledge his by right of office. He arrives uninvited, stays longer than anyone wants, "
    "and steers every conversation towards whatever the others would rather not discuss. "
    "Any refusal to explain something to him is an insult and a suspicious circumstance at once, and he says so loudly. "
    "He cites rules, regulations and paperwork whenever they favour him, and forgets them the moment they do not. "
    "He threatens to report things to the authorities more often than he ever actually reports anything. "
    "He speaks in short, indignant bursts, is easily offended, and is won over by being let in on a secret "
    "or being treated as an important person."
)

MATROSKIN = Character(
    'Matroskin',
    Character.Gender.Masculine,
    "Matroskin is a talking cat and the one who actually runs the household. "
    "He cares about order, about the house being in good repair, and above all about the farm turning a profit: "
    "the cow, the milk, the sour cream, the cheese, and how much of each can be sold and at what price. "
    "He counts everything out loud, remembers who spent what, and treats an unbudgeted purchase as a personal wound. "
    "He is by far the cleverest of the three and usually right, which he knows and does not let anyone forget. "
    "He argues with numbers and with sarcasm, and he grumbles constantly, even when he is getting his way. "
    "He is not mean, but he is thoroughly practical: he will agree to anything that pays for itself, "
    "and dig in against anything that does not."
)

SHARIK = Character(
    'Sharik',
    Character.Gender.Masculine,
    "Sharik is a talking dog, simple-minded, warm-hearted and easy to talk into things. "
    "He wants everyone to get along and gives in quickly when someone raises their voice, then quietly goes back "
    "to what he wanted in the first place. He loves running, swimming, digging and any excuse to be outdoors, "
    "and he is proud of how much he can carry and how far he can go. "
    "His real passion is photographing wild animals: hares, foxes, birds, anything that will hold still, "
    "and he dreams of a proper photo rifle so he can shoot them on film instead of chasing them. "
    "He does not understand money, budgets or paperwork, and says so cheerfully. "
    "He speaks plainly and enthusiastically, gets distracted by the outdoors mid-argument, "
    "and takes offence rarely and briefly."
)

CHARACTERS = (PECHKIN, MATROSKIN, SHARIK)

DEFAULT_PROTAGONIST = PECHKIN

NAME_TO_CHARACTER = {c.name: c for c in CHARACTERS}


def get_character(name: str) -> Character:
    key = name.strip().capitalize()
    if key not in NAME_TO_CHARACTER:
        raise ValueError(f"Unknown character {name}, expected one of {', '.join(NAME_TO_CHARACTER)}")
    return NAME_TO_CHARACTER[key]


def others(name: str) -> tuple[Character, ...]:
    return tuple(c for c in CHARACTERS if c.name != get_character(name).name)
