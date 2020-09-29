import json
import os
import pathlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CURR_DIR = pathlib.Path(__file__).parent.absolute()
BASE_URL = "https://www.vrk.lt/statiniai/puslapiai/rinkimai/1104/rnk1424/kandidatai/"
PARTIJU_SARASAS_URL = "lrsKandidataiSarasai.html"
PARTIJOS_KANDIDATAI = "lrsKandidataiSarasas_rorgId-{}.html"
KANDIDATO_TURTAS = "lrsKandidatasTurtas_rkndId-{}.html"


def get_party_url_ids() -> dict:
    result = {}
    page_partijos = requests.get(urljoin(BASE_URL, PARTIJU_SARASAS_URL))
    soup_partijos = BeautifulSoup(page_partijos.content, "html.parser")

    temp_tables = soup_partijos.find_all("table", class_="partydata")
    partijos_rows = []
    for table in temp_tables:
        temp = table.find_all("tr")
        if len(temp) > len(partijos_rows):
            partijos_rows = temp

    for row in partijos_rows:
        for ix, col in enumerate(row.find_all("td")):
            if ix == 1:
                party_name = col.text.strip()
                party_id = re.findall("rorgId-(.*).html", str(col))[0]
                result[party_name] = party_id
                break

    return result


def get_candidate_url_ids(partijos):
    result = []

    cnt = 0
    for partija, partijos_id in partijos.items():
        cnt += 1
        print(f"- Partija: {partija} ({cnt} is {len(partijos.values())})")
        page_partijos = requests.get(urljoin(BASE_URL, PARTIJOS_KANDIDATAI.format(partijos_id)))
        soup_partijos = BeautifulSoup(page_partijos.content, "html.parser")

        temp_tables = soup_partijos.find_all("table", class_="partydata")
        main_table = []
        for table in temp_tables:
            temp = table.find_all("tr")
            if len(temp) > len(main_table):
                main_table = temp

        temp = {
            "partija": partija,
            "partijos_id": partijos_id,
        }
        for ix, row in enumerate(main_table):
            print(f"Kandidatas {ix} is {len(main_table)}")
            if ix == 0:
                continue

            for ixx, col in enumerate(row.find_all("td")):
                if ixx == 0:
                    temp["numeris partijos sarase"] = col.text.strip()
                elif ixx == 1:
                    temp["vardas"] = col.text.strip()
                    canidate_id = re.findall("rkndId-(.*).html", str(col))[0]
                    temp["kadidato_rogId"] = canidate_id
                elif ixx == 3:
                    temp["apygarda"] = col.text.strip()
            result.append(temp.copy())

    return result


def get_candidate_wealth(kandidatai_list):
    result = []

    for ix, kandidatas in enumerate(kandidatai_list):
        print(f"- Kandidatas: {ix} is {len(kandidatai_list)}")
        page_partijos = requests.get(urljoin(BASE_URL, KANDIDATO_TURTAS.format(kandidatas["kadidato_rogId"])))
        soup_partijos = BeautifulSoup(page_partijos.content, "html.parser")

        tables = soup_partijos.find_all("table", class_="tabinc")
        # TURTO DEKLARACIJOS
        rows = tables[0].find_all("tr")
        for ix_row, row in enumerate(rows):
            if ix_row == 0:
                continue
            for ix_col, col in enumerate(row.find_all("td")):
                if ix_col == 0:
                    continue
                if ix_row == 1:
                    key = "registruotas_turtas"
                elif ix_row == 2:
                    key = "vertybiniai_popieriai"
                elif ix_row == 3:
                    key = "grynieji_pinigai"
                elif ix_row == 4:
                    key = "suteiktos_paskolos"
                elif ix_row == 5:
                    key = "gautos_paskolos"
                else:
                    raise ValueError("oops")

                kandidatas[f"{key} (Eur)"] = col.text.replace("Eur", "").strip()

        # METINĖS PAJAMŲ MOKESČIO DEKLARACIJOS
        rows = tables[1].find_all("tr")
        for ix_row, row in enumerate(rows):
            if ix_row in [0, 1]:
                continue
            for ix_col, col in enumerate(row.find_all("td")):
                if ix_col == 0:
                    continue
                if ix_row == 2:
                    key = "deklaruotos_pajamos"
                elif ix_row == 3:
                    key = "individualios_veiklos_pajamos"
                elif ix_row == 4:
                    key = "nuostoliai"
                elif ix_row == 5:
                    key = "turto_pardavimas_perleidimas"
                elif ix_row == 6:
                    key = "to_turto_isigyjimo_kaina"
                elif ix_row == 7:
                    key = "deklaruota_moketina_pajamu_suma"
                else:
                    raise ValueError("oops")

                kandidatas[f"{key} (Eur)"] = float(col.text.replace("Eur", "").replace(",", ".").strip())

        result.append(kandidatas.copy())

    return result


# res = get_party_url_ids()
# print(res)

# Gauti kandidatu sarasa
# partiju_id = json.loads((CURR_DIR / "partiju_id.txt").read_text())
# res = get_candidate_url_ids(partiju_id)
# (CURR_DIR / "kandidatai_list.txt").write_text(json.dumps(res))

kandidatai_list = json.loads((CURR_DIR / "kandidatai_list.txt").read_text())
res = get_candidate_wealth(kandidatai_list)
(CURR_DIR / "kandidatai_list_turtas.txt").write_text(json.dumps(res))
print(1)
