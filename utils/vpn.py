import os
import requests
import sys
import random
import logging
import orjson
from configs.config import Config


class connect(object):
    def __init__(self, code):
        self.logger = logging.getLogger(__name__)
        self.code = code.lower()

        self.headers = {
            "user-agent": Config().get_user_agent()
        }

    def get_nordvpn_server(self):
        """
        Get the recommended NordVPN server hostname for a specified Country.
        :param country: Country (in alpha 2 format, e.g. 'US' for United States)
        :returns: Recommended NordVPN server hostname, e.g. `us123.nordvpn.com`
        """
        # Get the Country's NordVPN ID
        countries = requests.get(
            url="https://nordvpn.com/wp-admin/admin-ajax.php",
            params={"action": "servers_countries"}
        ).json()
        country_id = [x["id"]
                      for x in countries if x["code"].lower() == self.code.lower()]
        if not country_id:
            return None
        country_id = country_id[0]
        # Get the most recommended server for the country and return it
        recommendations = requests.get(
            url="https://nordvpn.com/wp-admin/admin-ajax.php",
            params={
                "action": "servers_recommendations",
                "filters": orjson.dumps({"country_id": country_id})
            }
        ).json()
        return recommendations[0]["hostname"]

    def load_privatevpn(self):
        html_file = "html.html"
        hosts = []
        resp = requests.get(
            "https://privatevpn.com/serverlist/", stream=True, headers=self.headers
        )
        resp = str(resp.text)
        resp = resp.replace("<br>", "")

        with open(html_file, "w", encoding="utf8") as file:
            file.write(resp)

        with open(html_file, "r") as file:
            text = file.readlines()

        if os.path.exists(html_file):
            os.remove(html_file)

        for p in text:
            if ".pvdata.host" in p:
                hosts.append(p.strip())

        return hosts

    def privateVPN(self):
        private_proxy = {}
        private_hosts = self.load_privatevpn()
        self.logger.debug("private_hosts: {}".format(private_hosts))
        search_host = [host for host in private_hosts if host[:2] == self.code]
        if not search_host == []:
            self.logger.info(f"Founded %s Proxies", str(len(search_host)))
            for n, p in enumerate(search_host):
                self.logger.info(f"[{str(n+1)}] {p}")
            inp = input(
                "\nEnter Proxy Number, or Hit Enter for random one: ").strip()
            if inp == "":
                return random.choice(search_host)
            private_proxy = search_host[int(inp) - 1]
        else:
            self.logger.info(
                "No Proxies Found, you may entered wrong code, or search failed!")

        return private_proxy
