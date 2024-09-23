from datetime import datetime
from pydantic import BaseModel

class DateTimeModel(BaseModel):
    datetime: datetime
    str_attr: str


import aas_middleware

example_date_model = DateTimeModel(datetime=datetime.now(), str_attr="example")

data_model = aas_middleware.DataModel.from_models(example_date_model)