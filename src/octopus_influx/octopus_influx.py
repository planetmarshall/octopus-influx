from argparse import ArgumentParser
from configparser import ConfigParser
import logging
import os
import urllib.parse

from influxdb_client import InfluxDBClient
import pandas as pd
import requests


base_url = "https://api.octopus.energy"


def load_config(config_file=None):
    if config_file is None:
        config_file_name = "octopus-influx.conf"
        candidates = [os.path.realpath(os.path.join(prefix, config_file_name))
                      for prefix in [".", "/etc", "/usr/local/etc"]]
        for candidate in candidates:
            if os.path.exists(candidate):
                config_file = candidate
        if config_file is None:
            raise ValueError("No config file found")

    config_file_path = os.path.realpath(config_file)
    config = ConfigParser()
    config.read(config_file_path)
    return config


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


def write_tariff_dataframe(tariff_name, tariff_dataframe: pd.DataFrame, bucket=None, org=None, url=None, token=None):
    with InfluxDBClient(url, token, org=org) as client:
        with client.write_api() as write_client:
            write_client.write(
                bucket,
                org,
                record=tariff_dataframe,
                data_frame_measurement_name=tariff_name
            )


def octopus_configs(config: ConfigParser):
    for section, _ in config.items():
        if section.startswith("octopus"):
            yield section, config[section]


def main():
    parser = ArgumentParser(description="Get Octopus Outgoing Tariff and persist to InfluxDB")
    parser.add_argument("--config", help="Full path to config file", default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    config = load_config(args.config)
    auth_config = config["auth"]
    influx_config = config["influx2"]

    for tariff_name, octopus_config in octopus_configs(config):
        tariff_dataframe = get_tariff(auth_config.get("octopus_api_key"), **octopus_config)
        logging.info(f"Retrieved {len(tariff_dataframe)} records for tariff {tariff_name}")
        write_tariff_dataframe(tariff_name, tariff_dataframe, **influx_config)


if __name__ == "__main__":
    main()
