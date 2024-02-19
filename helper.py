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