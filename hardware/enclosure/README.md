# Krabička krbového teploměru

| Soubor | Popis |
|--------|-------|
| `enclosure_box.stl` | krabička (ESP32 + MAX31856, otevřená zadní strana) |
| `enclosure_lid.stl` | víčko se zaklapávacími západkami |
| `build_enclosure.py` | skript, který modely vytvoří z originálu |
| `original/` | původní, neupravený model |

## Původ modelu

Tento model je **remix** díla:

- **Název:** ESP32-WROOM-32 (USB-C) Box with Lid
- **Autor:** PLAUK
- **Zdroj:** <https://www.printables.com/model/711587-esp32-wroom-32-usb-c-box-with-lid>
- **Licence:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Provedené změny

- Krabička je prodloužená o 40 mm. V přidaném oddílu je lože pro modul LaskaKit MAX31856 (30 × 24 mm), který se vkládá lícem dolů: boční police se sražením 45°, dorazy a vynechané místo pro svorkovnici.
- Plné dno pod ESP32 je nahrazené policí tloušťky 2 mm. Pod ní je kabelový prostor pro dupont konektory (20 mm) a ohyb vodičů (6 mm), podepřený podélným žebrem. Celková výška je 31,15 mm.
- Zadní strana je otevřená a má lepicí lem šířky 4 mm pro montáž na zeď.
- V pravé boční stěně je U-výřez pro kabel termočlánku. Víčko má jazýček, který ho uzavře na otvor 5,5 × 5 mm, a v límci víčka je pro výřez mezera.
- V prodloužené části přibyl druhý pár zaklapávacích západek; je to přesná kopie originálu.
- Víčko má čtyři přítlačné kolíky, které drží modul MAX31856.
- Původní část pro ESP32 (výřez pro USB, sloupky, spáry pro piny, mřížka a otvory pro tlačítka ve víčku) je beze změn.

## Licence

Upravené modely `enclosure_box.stl` a `enclosure_lid.stl` jsou šířeny pod licencí [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), viz [`LICENSE`](../../LICENSE). Při dalším sdílení uveďte jak tento projekt, tak autora původního modelu (PLAUK). Skript `build_enclosure.py` je pod licencí MIT, viz [`LICENSE-CODE`](../../LICENSE-CODE).
