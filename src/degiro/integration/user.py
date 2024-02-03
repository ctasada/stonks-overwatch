from degiro.utils.degiro import DeGiro
import json

class UserData:
    clientDetails = None

    def get_details(self):
        clientDetails = DeGiro.get_client_details()

        return clientDetails['data']

    def get_language(self):
        clientDetails = DeGiro.get_client_details()

        return clientDetails['data']['language']