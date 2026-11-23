"""Provider interface. Only gudi.runner calls submit(); see gudi/paid for the live adapters."""


class Provider:
    name = "abstract"
    is_paid = True

    def quote_milli(self, call):  # exact quoted cost of one request
        raise NotImplementedError

    def submit(self, call, request_key, payload=None):  # -> provider job id (may raise / crash)
        raise NotImplementedError

    def status(self, job_id):  # -> {"state": pending|completed|failed, "url": str|None, "charged_milli": int|None}
        raise NotImplementedError

    def find(self, call, request_key, since_iso):  # reconcile: -> job id or None
        raise NotImplementedError

    def download(self, job_id, url, dest):  # -> path
        raise NotImplementedError
