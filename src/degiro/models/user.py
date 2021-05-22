from degiro.utils.degiro import DeGiro

class UserModel:
    def __init__(self):
        self.deGiro = DeGiro()

    def getDetails(self):
        clientDetails = self.deGiro.get_client_details()

        return clientDetails['data']