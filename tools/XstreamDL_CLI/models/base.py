class BaseUri:
    def __init__(self, name: str = '', home_url: str = '', base_url: str = ''):
        self.name = name
        self.home_url = home_url
        self.base_url = base_url

    def new_name(self, name: str):
        return BaseUri(name, self.home_url, self.base_url)

    def new_home_url(self, home_url: str):
        return BaseUri(self.name, home_url, self.base_url)

    def new_base_url(self, base_url: str):
        return BaseUri(self.name, self.home_url, base_url)