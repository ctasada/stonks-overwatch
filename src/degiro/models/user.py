from degiro.utils.degiro import DeGiro

class UserModel:

    def getDetails(self):
        clientDetails = DeGiro.get_client_details()

        return clientDetails['data']