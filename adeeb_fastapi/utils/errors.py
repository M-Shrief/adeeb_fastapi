from typing import Literal


class APIError(Exception):
    def __init__(self,  status_code: int, caused_in: Literal["repository", "service", "route"], message: str | None =None):
        self.message: str | None = message
        self.status_code: int = status_code
        self.caused_in: Literal['repository', 'service', 'route'] = caused_in
        super().__init__(self.message)

    # def __str__(self):
    #     if :
    #         return f""
    #     return self.message