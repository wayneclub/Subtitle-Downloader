#!/usr/bin/python3
# coding: utf-8

"""
This module is for proxy service.
"""
from __future__ import annotations
import logging
import sys
from typing import Optional
import orjson
import requests
from configs.config import config


def get_ip_info(session: Optional[requests.Session] = None) -> dict:
    """Use ipinfo.io to get IP location information."""

    return (session or requests.Session()).get('https://ipinfo.io/json', timeout=5).json()


def get_proxy(region: str, ip_info: dict, geofence: list, platform: str) -> Optional[str]:
    """Get proxy"""

    if not region:
        logger.error('Region cannot be empty!')
        sys.exit(1)
    region = region.lower()

    logger.info('Obtaining a proxy to "%s"', region)

    if ip_info['country'].lower() == ''.join(i for i in region if not i.isdigit()):
        return None  # no proxy necessary

    if config.proxies.get(region):
        proxy = config.proxies[region]
        logger.info(' + %s (via config.proxies)', proxy)
    elif config.nordvpn.get('username') and config.nordvpn.get('password'):
        proxy = get_nordvpn_proxy(region)
        logger.info(' + %s (via nordvpn)', proxy)
    else:
        logger.error(' - Unable to obtain a proxy')
        if geofence:
            logger.error(
                '%s is restricted in %s, please use the proxy to bypass restrictions.', platform, ', '.join(geofence).upper())
        sys.exit(1)

    if '://' not in proxy:
        # assume a https proxy port
        proxy = f'https://{proxy}'

    return proxy


def get_nordvpn_proxy(region: str) -> str:
    """Via NordVPN to use proxy"""

    proxy = f"https://{config.nordvpn['username']}:{config.nordvpn['password']}@"
    if any(char.isdigit() for char in region):
        proxy += f"{region}.nordvpn.com"  # direct server id
    elif config.nordvpn.get("servers", {}).get(region):
        # configured server id
        proxy += f"{region}{config.nordvpn['servers'][region]}.nordvpn.com"
    else:
        # get current recommended server id
        hostname = get_nordvpn_server(region)
        if not hostname:
            logger.error(
                " - NordVPN doesn't contain any servers for the country \"{%s}\"", region)
            sys.exit(1)
        proxy += hostname
    return proxy + ":89"  # https: 89, http: 80


def get_nordvpn_server(country: str) -> Optional[str]:
    """
    Get the recommended NordVPN server hostname for a specified Country.
    :param country: Country (in alpha 2 format, e.g. 'US' for United States)
    :returns: Recommended NordVPN server hostname, e.g. `us123.nordvpn.com`
    """
    # Get the Country's NordVPN ID
    countries = requests.get(
        url="https://nordvpn.com/wp-admin/admin-ajax.php",
        params={"action": "servers_countries"},
        timeout=5
    ).json()
    country_id = [x["id"]
                  for x in countries if x["code"].lower() == country.lower()]
    if not country_id:
        return None
    country_id = country_id[0]
    # Get the most recommended server for the country and return it
    recommendations = requests.get(
        url="https://nordvpn.com/wp-admin/admin-ajax.php",
        params={
            "action": "servers_recommendations",
            "filters": orjson.dumps({"country_id": country_id}).decode('utf-8')
        },
        timeout=5
    ).json()
    return recommendations[0]["hostname"]


if __name__:
    logger = logging.getLogger(__name__)
