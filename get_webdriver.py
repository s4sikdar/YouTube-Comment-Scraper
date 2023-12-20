#!/usr/bin/env python
'''
Python script to make GET requests to JSON endpoints containing urls for the latest stable builds of chrome webdriver.
If the script can get a url, it then tries to download the zip file with the chrome webdriver inside of it and saves it locally.
The name it saves the file as locally is given by the url endpoint (everything after the last slash becomes the zipfile name).
The script first tries to make a request to to a spcific endpoint to
https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json to an endpoint to download the
script. If the zip file is successfully downloaded this way, then the script exits. Otherwise, the script tries to construct the
URL endpoint based on a hard-coded URL in the script. If neither one works, the script exits with a non-zero error code.
'''
import requests
import json
import argparse
import sys


def hardcode_url_download(platform):
    '''
        hardcode_url_download(platform) downloads the latest chromedriver by going to the url below to get the latest stable version.
        https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE
        From there, the URL is constructed and a request is made. One parameter is passed in - platform. platform specifies the platform
        for which you want to use. platform can be one of the following values below:
        * linux64
        * mac-arm64
        * mac-x64
        * win32
        * win64
        Passing anything else as the parameter for this function will cause the script to print to standard error and exit with an
        error code of 2.
    '''
    latest_version_url='https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE'
    latest_stable_version=requests.get(latest_version_url)
    download_endpoint_base='https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing'
    platform_specific_endpoints = {
        'linux64': 'linux64/chromedriver-linux64.zip',
        'mac-arm64': 'mac-arm64/chromedriver-mac-arm64.zip',
        'mac-x64': 'mac-x64/chromedriver-mac-x64.zip',
        'win32': 'win32/chromedriver-win32.zip', 
        'win64': 'win64/chromedriver-win64.zip'
    }
    if not latest_stable_version:
        print(
            (
                f'A request was made to {latest_version_url} and a status code of {latest_stable_version.status_code} '
                'was returned, implying an unsuccessful request. Exiting with an error code of 1.'
            ),
            file=sys.stderr, flush=True
        )
        exit(1)
    elif latest_stable_version.status_code == 204:
        print(
            (
                f'A request was made to {latest_version_url} and a status code of 204 was returned, implying the payload is empty.'
                'Exiting with an error code of 1.'
            ),
            file=sys.stderr, flush=True
        )
        exit(1)
    else:
        version=latest_stable_version.text
        if not (platform in platform_specific_endpoints):
            print(
                (
                    f'Platform {platform} is not supported by chromedriver. With this platform the program cannot run.'
                    'Exiting with an error code of 2.'
                ),
                file=sys.stderr, flush=True
            )
            exit(2)
        else:
            url = f'{download_endpoint_base}/{version}/' + platform_specific_endpoints[platform]
            zip_response = requests.get(url, stream=True)
            zip_fname=url.split('/')[-1]
            if not zip_response:
                print(
                    (
                        f'A request to the url {zip_response} returned an http status code of {zip_response.status_code}.'
                        'Exiting with an error code of 1.'
                    ),
                    file=sys.stderr, flush=True
                )
                exit(1)
            elif zip_response.status_code == 204:
                print(
                    (
                        f'A request to the url {zip_response} returned an http status code of 204. This means nothing is at the endpoint. '
                        'Exiting with an error code of 1.'
                    ),
                    file=sys.stderr, flush=True
                )
                exit(1)
            else:
                with open(zip_fname, 'wb') as webdriver_zip:
                    for payload_bytes in zip_response.iter_content(chunk_size=256):
                        zip_fname.write(payload_bytes)
                print(zip_fname)
                exit(0)


def main():
    '''
        main() is the script entry point
    '''
    JSON_URL = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'
    # ArgumentParser configured to parse only a platform argument. The platform argument takes in one of: linux64, mac-arm64, mac-x64, win32, and win64
    parser = argparse.ArgumentParser(
        description=(
            'A python script to download the most recent stable chromedriver binary for a specific platform which is passed in.'
            'The script makes a request to https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json for the info.'
            'If the script successfully finds the url in the returned json, then the script tries to download the name based on everything in the endpoint after '
            'the last slash.'
        )
    )
    parser.add_argument(
        '-p', '--platform',
        type=str, required=True,
        help='The platform for which you want to download the chromedriver binary.',
        choices=['linux64', 'mac-arm64', 'mac-x64', 'win32', 'win64']
    )
    arguments = parser.parse_args()
    # Make a request to JSON_URL to get a JSON with info on the endpoint to get the latest chrome binary.
    result= requests.get(JSON_URL)
    if (not result) or (result.status_code == 204):
        # The URL endpoint returns with a non-successful status code or with a status code of 204, meaning nothing is at that endpoint.
        hardcode_url_download(arguments.platform)
    chrome_versions = json.loads(result.content)
    try:
        stable_downloads = chrome_versions['channels']['Stable']['downloads']['chromedriver']
    except KeyError as err:
        hardcode_url_download(arguments.platform)
    else:
        for item in stable_downloads:
            if item['platform'] == arguments.platform:
                endpoint = item['url']
                zipfile_name = endpoint.split(sep='/')[-1]
                zipfile_payload = requests.get(endpoint, stream=True)
                if not zipfile_payload:
                    print(
                        f'The endpoint {endpoint} returned with a return code of {zipfile_payload.status_code}. Exiting with an error code of 1.',
                        file=sys.stderr, flush=True
                    )
                    exit(1)
                elif zipfile_payload.status_code == 204:
                    print(
                        f'The endpoint {endpoint} returned with a return code of {zipfile_payload.status_code}. Exiting with an error code of 1.',
                        file=sys.stderr, flush=True
                    )
                    exit(1)
                else:
                    # Write the response payload to the zipfile (same name as the name indicated by everything after the last slash in the url)
                    with open(zipfile_name, 'wb') as zipfile:
                        for zipfile_block in zipfile_payload.iter_content(chunk_size=256):
                            zipfile.write(zipfile_block)
                        print(zipfile_name)
                        exit(0)



if __name__ == '__main__':
    main()
