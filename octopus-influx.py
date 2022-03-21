import os
from argparse import ArgumentParser
import urllib.parse
from pprint import pprint

import pandas as pd
import requests


base_url = "https://api.octopus.energy"


def _results(response : requests.Response):
    json_reponse = response.json()
    for result in json_reponse["results"]:
        yield result


def get_tariff(api_key, product_code="AGILE-OUTGOING-19-05-13", tariff_code="E-1R-AGILE-OUTGOING-19-05-13-G"):
    end_point = f"/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/"
    url = urllib.parse.urljoin(base_url, end_point)
    response = requests.get(url, auth=(api_key, None))
    records = pd.DataFrame.from_records(response.json()["results"])
    print(records)


def main():
    api_key = os.environ["OCTOPUS_API_KEY"]
    get_tariff(api_key, product_code="AGILE-OUTGOING-19-05-13", tariff_code="E-1R-AGILE-OUTGOING-19-05-13-G")


if __name__ == "__main__":
    main()
