from stonks_overwatch.config.degiro import DegiroCredentials


class DegiroHelper:
    """
    Helper class for DeGiro operations, including credential management.
    """

    @staticmethod
    def store_credentials_in_session(request, username: str, password: str, remember_me: bool):
        """Helper function to store credentials in the session"""
        credentials = DegiroCredentials(username=username, password=password, remember_me=remember_me)
        request.session["credentials"] = credentials.to_dict()
        request.session.modified = True
        request.session.save()
