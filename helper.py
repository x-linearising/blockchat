from socket import gethostname, gethostbyname

class JSONSerializable:
    """
        Classes inheriting this class can have their instances converted to Json.
        This is useful in endpoints as Flask needs a dictionary like structure
        for its responses and requests.
    """
    def to_dict(self):
        if hasattr(self, '__dict__'):
            return self.__dict__
        else:
            raise TypeError("Object is not JSON serializable")

def myIP():
    # TODO: this may return 127.0.0.1 on some machines instead of the local IP addr.
    # no problem when running locally, but we don't want our online nodes to believe
    # 127.0.0.1 is their IP
    return gethostbyname(gethostname())
