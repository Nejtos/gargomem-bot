from bot.utils.helpers import get_hero_prof


mItemsName = [
    ["Uszkodzona różdżka", "Uszkodzony orb"],
    ["Szkatułka poskromiciela"],
    ["Płaszcz adepta", "Różdżka adepta", "Hełm otwarty"],
    ["Orb druida"],
    [
        "Buty rycerskie",
        "Różdżka maga",
        "Skórzane łachmany",
        "Orb letniego błysku",
        "Rękawice ochronne",
        "Zamknięty hełm",
    ],
    ["Recepta na miksturę uzdrawiającą"],
    ["Szkatułka poskromiciela II"],
    [
        "Unikatowe rękawice śmiałka",
        "Płaszcz leśnej magii",
        "Lodowa różdżka mistrza",
        "Lodowy orb mistrza",
        "Naszyjnik mocy wody",
        "Pierścień mocy wody",
        "Hełm garnczkowy",
    ],
    ["Recepta na większą miksturę uzdrawiającą"],
    ["Wzmocniona magiczna zbroja z wilczej skóry"],
    ["Szkatułka poskromiciela III"],
]

pItemsName = [
    ["Wyszczerbiony miecz", "Żelazna tarcza"],
    ["Szkatułka poskromiciela"],
    ["Lekka zbroja płytowa", "Zakrzywiony miecz rycerza", "Hełm otwarty"],
    ["Stalowa tarcza"],
    [
        "Buty rycerskie",
        "Szpada",
        "Skórzane łachmany",
        "Średnia tarcza",
        "Rękawice ochronne",
        "Zamknięty hełm",
    ],
    ["Recepta na miksturę uzdrawiającą"],
    ["Szkatułka poskromiciela II"],
    [
        "Unikatowe rękawice śmiałka",
        "Zbroja segmentowa",
        "Wzmocniony miecz półtoraręczny",
        "Wzmocniona tarcza",
        "Naszyjnik mocy wody",
        "Pierścień mocy wody",
        "Hełm garnczkowy",
    ],
    ["Recepta na większą miksturę uzdrawiającą"],
    ["Wzmocniony napierśnik z wilczej skóry"],
    ["Szkatułka poskromiciela III"],
]

wItemsName = [
    ["Wyszczerbiony miecz", "Żelazna tarcza"],
    ["Szkatułka poskromiciela"],
    ["Lekka zbroja płytowa", "Zakrzywiony miecz rycerza", "Hełm otwarty"],
    ["Stalowa tarcza"],
    [
        "Buty rycerskie",
        "Szpada",
        "Skórzane łachmany",
        "Średnia tarcza",
        "Rękawice ochronne",
        "Zamknięty hełm",
    ],
    ["Recepta na miksturę uzdrawiającą"],
    ["Szkatułka poskromiciela II"],
    [
        "Unikatowe rękawice śmiałka",
        "Zbroja segmentowa",
        "Wzmocniony miecz półtoraręczny",
        "Wzmocniona tarcza",
        "Naszyjnik mocy wody",
        "Pierścień mocy wody",
        "Hełm garnczkowy",
    ],
    ["Recepta na większą miksturę uzdrawiającą"],
    ["Wzmocniony napierśnik z wilczej skóry"],
    ["Szkatułka poskromiciela III"],
]

bItemsName = [
    ["Wyszczerbiony miecz", "Wyszczerbiony sztylet"],
    ["Szkatułka poskromiciela"],
    ["Lekka zbroja płytowa", "Zakrzywiony miecz rycerza", "Hełm otwarty"],
    ["Stalowa tarcza"],
    [
        "Buty rycerskie",
        "Szpada",
        "Skórzane łachmany",
        "Średnia tarcza",
        "Rękawice ochronne",
        "Zamknięty hełm",
    ],
    ["Recepta na miksturę uzdrawiającą"],
    ["Szkatułka poskromiciela II"],
    [
        "Unikatowe rękawice śmiałka",
        "Zbroja segmentowa",
        "Wzmocniony miecz półtoraręczny",
        "Wzmocniona tarcza",
        "Naszyjnik mocy wody",
        "Pierścień mocy wody",
        "Hełm garnczkowy",
    ],
    ["Recepta na większą miksturę uzdrawiającą"],
    ["Wzmocniony kaftan z wilczej skóry"],
    ["Szkatułka poskromiciela III"],
]

hItemsName = [
    ["Łuk młodego łowcy", "Krótkie strzały"],
    ["Szkatułka poskromiciela"],
    ["Lekka zbroja płytowa", "Zakrzywiony miecz rycerza", "Hełm otwarty"],
    ["Stalowa tarcza"],
    [
        "Buty rycerskie",
        "Szpada",
        "Skórzane łachmany",
        "Średnia tarcza",
        "Rękawice ochronne",
        "Zamknięty hełm",
    ],
    ["Recepta na miksturę uzdrawiającą"],
    ["Szkatułka poskromiciela II"],
    [
        "Unikatowe rękawice śmiałka",
        "Zbroja segmentowa",
        "Wzmocniony miecz półtoraręczny",
        "Wzmocniona tarcza",
        "Naszyjnik mocy wody",
        "Pierścień mocy wody",
        "Hełm garnczkowy",
    ],
    ["Recepta na większą miksturę uzdrawiającą"],
    ["Wzmocniony kaftan z wilczej skóry"],
    ["Szkatułka poskromiciela III"],
]

tItemsName = [
    ["Łuk młodego łowcy", "Krótkie strzały"],
    ["Szkatułka poskromiciela"],
    ["Lekka zbroja płytowa", "Zakrzywiony miecz rycerza", "Hełm otwarty"],
    ["Stalowa tarcza"],
    [
        "Buty rycerskie",
        "Szpada",
        "Skórzane łachmany",
        "Średnia tarcza",
        "Rękawice ochronne",
        "Zamknięty hełm",
    ],
    ["Recepta na miksturę uzdrawiającą"],
    ["Szkatułka poskromiciela II"],
    [
        "Unikatowe rękawice śmiałka",
        "Zbroja segmentowa",
        "Wzmocniony miecz półtoraręczny",
        "Wzmocniona tarcza",
        "Naszyjnik mocy wody",
        "Pierścień mocy wody",
        "Hełm garnczkowy",
    ],
    ["Recepta na większą miksturę uzdrawiającą"],
    ["Wzmocniona magiczna zbroja z wilczej skóry"],
    ["Szkatułka poskromiciela III"],
]


async def getRightItems():
    heroProf = await get_hero_prof()

    items_map = {
        "m": mItemsName,
        "p": pItemsName,
        "w": wItemsName,
        "b": bItemsName,
        "h": hItemsName,
        "t": tItemsName,
    }

    return items_map.get(heroProf, [])
