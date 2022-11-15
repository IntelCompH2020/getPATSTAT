"""
Created on Feb 24 2021
Updated on Oct 2022
Authors:    Jeronimo Arenas Garcia <jarenas@ing.uc3m.es>
            José Antonio Espinosa Melchor <joespino@pa.uc3m.es>

Download PATSTAT products using REST API
"""

import argparse
import configparser
import io
import json
import sys
import zipfile
from pathlib import Path

import requests
from dateutil import parser


def print_status(act_msg, err_msg, resp):
    print(f"{act_msg}: {resp}")
    if not resp.status_code == 200:
        print(err_msg)
        try:
            print(json.dumps(json.loads(resp.content.decode()), indent=2))
        except:
            pass
        sys.exit()


if __name__ == "__main__":
    # Args
    arg_parser = argparse.ArgumentParser(description="Download PATSTAT products using REST API")
    arg_parser.add_argument("-c", "--config", help="Configuration file to use", default="config.cf")
    arg_parser.add_argument("-p", "--path", help="Path where the datasets will be downloaded")
    args = arg_parser.parse_args()

    # Make sure a valid a configuration file is available
    config = configparser.ConfigParser()
    if not Path(args.config).is_file():
        print("Please provide a valid configuration file")
        sys.exit()
    config.read(args.config)

    # Load credentials and destination path
    username = config["creds"]["user"]
    password = config["creds"]["pass"]
    if args.path:
        download_path = Path(args.path)
    else:
        download_path = Path(config["data"]["path"])
    if not download_path.is_dir():
        print("Please provide a link to a folder for the download")
        sys.exit()

    # Create session
    with requests.Session() as s:
        # Get token
        # Credentials
        credentials = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "scope": "openid",
        }
        p = s.post(
            "https://login.epo.org/oauth2/aus3up3nz0N133c0V417/v1/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic MG9hM3VwZG43YW41cE1JOE80MTc=",
            },
            data=credentials,
        )
        print_status("Get token", "Invalid credentials", p)
        token_response = json.loads(p.content.decode())
        token_type = token_response["token_type"]
        access_token = token_response["access_token"]

        # Get products
        base_uri = "https://publication-bdds.apps.epo.org/bdds/bdds-bff-service/prod/api/products/"
        r = s.get(base_uri, headers={"Authorization": f"{token_type} {access_token}"})
        print_status("Get products", "Invalid subscription products", r)
        products = json.loads(r.content)

        # Get most recent PATSTAT Global
        product = [p for p in products if "PATSTAT Global" in p["name"]]
        if not product:
            print("These credentials do not allow access to PATSTAT Global")
            sys.exit()
        product = product[0]
        productID = product["id"]
        r = s.get(f"{base_uri}{productID}", headers={"Authorization": f"{token_type} {access_token}"})
        print_status("Get product", "Invalid subscription product", r)
        data_dict = json.loads(r.content)

        # Filter most recent
        most_recent = sorted(
            data_dict["deliveries"], key=lambda x: parser.parse(x["deliveryPublicationDatetime"]), reverse=True,
        )[0]
        deliveryId = most_recent["deliveryId"]

        # Create download directory
        edition = "_".join(most_recent["deliveryName"].split()[-2:])
        version_path = download_path.joinpath(f"{edition}")
        if version_path.exists():
            print("This version has already been downloaded.")
            print("Closing...")
            sys.exit()
        else:
            # Download
            version_path.mkdir(parents=True)
            for file in most_recent["files"]:
                # Save and extract files
                fileId = file["fileId"]
                print(f'Downloading: {file["fileName"]}')
                print(file)
                r = s.get(
                    f"{base_uri}{productID}/delivery/{deliveryId}/file/{fileId}/download",
                    headers={"Authorization": f"{token_type} {access_token}"},
                )
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(version_path)
