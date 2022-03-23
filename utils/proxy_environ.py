import os
import requests
import sys
import re
from configs.config import Config
from utils.vpn import connect
import logging


class hold_proxy(object):
    def __init__(self):
        self.proxy = os.environ.get("http_proxy")
        self.logger = logging.getLogger(__name__)

    def disable(self):
        os.environ["http_proxy"] = ""
        os.environ["HTTP_PROXY"] = ""
        os.environ["https_proxy"] = ""
        os.environ["HTTPS_PROXY"] = ""

    def enable(self):
        if self.proxy:
            os.environ["http_proxy"] = self.proxy
            os.environ["HTTP_PROXY"] = self.proxy
            os.environ["https_proxy"] = self.proxy
            os.environ["HTTPS_PROXY"] = self.proxy


class proxy_env(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.args = args
        self.vpn = Config().vpn()
        self.session = requests.session()

    def Load(self):
        proxies = None
        proxy = {}
        aria2c_proxy = []

        if self.args.proxy and self.vpn["proxies"]:
            proxies = self.vpn["proxies"]
            self.logger.info(
                "\nProxy Status: Activated Local Proxy (%s)", proxies)

        elif self.args.privtvpn:
            self.logger.info("\nProxy Status: Activated Private VPN")
            proxy.update({"port": self.vpn["private"]["port"]})
            proxy.update({"user": self.vpn["private"]["email"]})
            proxy.update({"pass": self.vpn["private"]["passwd"]})

            if "pvdata.host" in self.args.privtvpn:
                proxy.update({"host": self.args.privtvpn})
            else:
                proxy.update(
                    {"host": connect(code=self.args.privtvpn).privateVPN()}
                )

            proxies = self.vpn["private"]["http"].format(
                email=proxy["user"],
                passwd=proxy["pass"],
                ip=proxy["host"],
                port=proxy["port"],
            )

        elif self.args.nordvpn:
            proxy.update({"port": self.vpn["nordvpn"]["port"]})
            proxy.update({"user": self.vpn["nordvpn"]["username"]})
            proxy.update({"pass": self.vpn["nordvpn"]["password"]})

            host = ''
            if "nordvpn.com" in self.args.nordvpn:
                host = self.args.nordvpn
            elif re.search(r'[a-z]{2}\d+', self.args.nordvpn):
                # configured server id
                host = f"{self.args.nordvpn}.nordvpn.com"
            else:
                host = connect(code=self.args.nordvpn).get_nordvpn_server()
            proxy.update({"host": host})

            self.logger.info(
                "\nProxy Status: Activated NordVPN (%s)", host.split('.')[0][:2].upper())

            proxies = self.vpn["nordvpn"]["http"].format(
                email=proxy["user"],
                passwd=proxy["pass"],
                ip=proxy["host"],
                port=proxy["port"],
            )

        if proxy.get("host"):
            aria2c_proxy.append(
                "--https-proxy={}:{}".format(proxy.get("host"),
                                             proxy.get("port"))
            )
        if proxy.get("user"):
            aria2c_proxy.append(
                "--https-proxy-user={}".format(proxy.get("user")))
        if proxy.get("pass"):
            aria2c_proxy.append(
                "--https-proxy-passwd={}".format(proxy.get("pass")))

        ip_info = self.verify_proxy(proxies)

        return ip_info

    def verify_proxy(self, proxy):

        if proxy:
            scheme = ('http', 'https')['https' in proxy]
            proxies = {scheme: proxy}
            self.session.proxies = proxies

        res = self.session.get('https://ipinfo.io/json', timeout=5)

        if res.ok:
            ip_info = res.json()
            if proxy:
                ip_info.update({"proxy": proxies})
            else:
                ip_info.update({"proxy": ''})

            self.logger.info('ip: %s (%s)',
                             ip_info['ip'], ip_info['country'])
            return ip_info
        else:
            self.logger.error(res.text)
