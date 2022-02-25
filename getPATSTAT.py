"""
Created on Feb 24 2021
Author: Jeronimo Arenas Garcia
        jarenas@ing.uc3m.es

Download PATSTAT products using REST API
"""

import sys
import argparse
import configparser
import xml.etree.ElementTree as ET
import requests
import xmltodict
import zipfile
import io
from pathlib import Path

import ipdb


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download PATSTAT products using REST API')
    parser.add_argument('-c','--config', help='Configuration file to use', default='config.cf')
    parser.add_argument('-p','--path', help='Path where the datasets will be downloaded')
    argus = parser.parse_args()

    # Make sure a valid a configuration file is available
    config = configparser.ConfigParser()
    if not Path(argus.config).is_file():
        print('Please provide a valid configuration file')
        sys.exit()
    config.read( argus.config )

    # Load credentials and destination path
    user = config['creds']['user']
    password = config['creds']['pass']

    if argus.path:
        rawpath = Path(argus.path)
    else:
        rawpath = Path(config['data']['path'])

    if not rawpath.is_dir():
        print('Please provide a link to a folder for the download')
        sys.exit()

    # Authenticate into the system
    s = requests.Session()
    url = 'https://publication.epo.org/raw-data/authentication?login=' + \
           user + '&pwd=' + password + '&action=1&format=1'
    print('Connect:', url)
    r = s.get(url)
    dict_data = xmltodict.parse(r.content)
    
    if dict_data['download-area']['authentication']['@authenticated'] == 'true':
        #authenticated
        #Retrieve products available for download
        print('Download products:', url)
        url = 'https://publication.epo.org/raw-data/products'
        r = s.get(url)
        dict_data = xmltodict.parse(r.content)
        nextUrl = None
        for product in dict_data['download-area']['products']['product']:
            if 'PATSTAT Global' in product['name']:
                nextUrl = product['url']
        
        #If PATSTAT Global is available for download, retrieve links
        if nextUrl:
            r = s.get(nextUrl+'/editions')
            dict_data = xmltodict.parse(r.content)
            version = dict_data['download-area']['editions']['edition']['version'].replace(' ','_')
            url = dict_data['download-area']['editions']['edition']['url']
            print('Available edition:', version)
            version_path = rawpath.joinpath(version)
            
            #If the directory name is taken, it is likely that the version has already
            #been downloaded
            if version_path.is_dir():
                print('The destination folder already exists. Delete and try again')
            else:
                version_path.mkdir()
                r = s.get(url)
                dict_data = xmltodict.parse(r.content)
                url = dict_data['download-area']['edition']['files-url']
                r = s.get(url)
                dict_data = xmltodict.parse(r.content)
                #SHAS = [el['checksum'] for el in dict_data['download-area']['files']['file']]
                files = [el['url'] for el in dict_data['download-area']['files']['file']]
                
                #Download and extract all files to destination folder
                for file in files:
                    print('Donwloading file:', file.split('/')[-1])
                    r = s.get(file)
                    z = zipfile.ZipFile(io.BytesIO(r.content))
                    z.extractall(version_path)
        else:
            print('These credentials do not allow access to PATSTAT Global')

        # Lastly we need to disconnect
        url = 'https://publication.epo.org/raw-data/authentication?login=' + \
              user + '&pwd=' + password + '&action=0&format=1'
        print('Disconnect:', url)
        r = s.get(url)
    else:
        print('Credentials are not valid')

    ipdb.set_trace()