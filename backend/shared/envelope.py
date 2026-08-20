from rest_framework.response import Response


class APIResponse(Response):
    """
    Sukses -> {"status": "success", "message": "...", "data": {...}}
    """

    def __init__(self, data=None, status_code=200, message="Berhasil"):
        # 204 No Content tidak boleh punya body
        if status_code == 204:
            super().__init__(status=status_code)
            return

        payload = {
            "status": "success",
            "message": message,
            "data": data,
        }
        super().__init__(payload, status=status_code)
