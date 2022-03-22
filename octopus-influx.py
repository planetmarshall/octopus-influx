import os
from argparse import ArgumentParser
import urllib.parse

from influxdb_client import InfluxDBClient
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
    records = response.json()
    df = pd.DataFrame.from_records(records["results"])
    df.set_index(pd.to_datetime(df.valid_from), inplace=True)
    return df[["value_inc_vat"]] * 0.01


def write_tariff_dataframe(tariff_dataframe: pd.DataFrame, influx_token=None):
    with InfluxDBClient(url="http://localhost:8086", token=influx_token, org="home") as client:
        with client.write_api() as write_client:
            write_client.write(
                "data",
                "home",
                record=tariff_dataframe,
                data_frame_measurement_name="octopus_agile_outgoing"
            )


def main():
    api_key = os.environ["OCTOPUS_API_KEY"]
    tariff_dataframe = get_tariff(
        api_key,
        product_code="AGILE-OUTGOING-19-05-13",
        tariff_code="E-1R-AGILE-OUTGOING-19-05-13-G"
    )
    write_tariff_dataframe(tariff_dataframe)


if __name__ == "__main__":
    parser = ArgumentParser(description="Get Octopus Outgoing Tariff and persist to InfluxDB")
    main()
