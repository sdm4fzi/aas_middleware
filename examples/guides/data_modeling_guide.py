import typing
import aas_middleware
from aas_middleware.model.data_model import DataModel


class BillOfMaterialInfo(aas_middleware.SubmodelElementCollection):
    manufacterer: str
    product_type: str

class BillOfMaterial(aas_middleware.Submodel):
    components: typing.List[str]
    bill_of_material_info: BillOfMaterialInfo


class ProcessModel(aas_middleware.Submodel):
    processes: typing.List[str]


class Product(aas_middleware.AAS):
    bill_of_material: BillOfMaterial
    process_model: ProcessModel


example_product = Product(
    id="example_product_id",
    id_short="example_product_id",
    description="Example Product",
    bill_of_material=BillOfMaterial(
        id="example_bom_id",
        id_short="example_bom_id",
        description="Example Bill of Material",
        components=["component_1", "component_2"],
        bill_of_material_info=BillOfMaterialInfo(
            id="example_bom_info_id",
            id_short="example_bom_info_id",
            description="Example Bill of Material Info",
            manufacterer="Example Manufacterer",
            product_type="Example Product Type",
        ),
    ),
    process_model=ProcessModel(
        id="example_process_model_id",
        id_short="example_process_model_id",
        description="Example Process Model",
        processes=["process_1", "process_2"],
    ),
)


# you can instantiate a data model from a list of models. Models need to be unique. The Data Model parses through the model and makes it and contained models easily available. 

data_model = aas_middleware.DataModel.from_models(example_product)

# The passed models with this method are so called top level models. 

print(data_model.get_top_level_models())

# you can also get all contained models

print(data_model.get_contained_models())

# 1. retrieve data models of by id

print(data_model.get_model("example_product_id"))
print(data_model.get_model("example_bom_id"))

# 2. retrieve data models by type
print(data_model.get_models_of_type(BillOfMaterial))
print(data_model.get_models_of_type_name("ProcessModel"))

# besides retrieving all the contained models, the data model class also analyzes the references in the data model. It detects associations and references (with key attributes) between models and can be used to generate a graph of the data model.

referenced_models = data_model.get_referenced_models(example_product)
print(referenced_models)
referencing_models = data_model.get_referencing_models(example_product.bill_of_material)
print(referencing_models)


# Types are very important. The data model class analyzes the types and makes them and their connection easily available

top_level_types = data_model.get_top_level_types()

# With this you can also create a type graph.



# Formatting and Mapping of data 

# Formatting is: chaning the notation / language of the data 
# Mapping is: changing the concept of the data

# The data model is the basic building block for formatting. The data model can be formatted in different ways. For example, the data model can be formatted in the Basyx format.


basyx_object_store = aas_middleware.formatting.BasyxFormatter().serialize(data_model)

json_aas = aas_middleware.formatting.AasJsonFormatter().serialize(data_model)
print(json_aas)

reformatted_data_model = aas_middleware.formatting.AasJsonFormatter().deserialize(json_aas)
print(reformatted_data_model.get_model("example_product_id"))


# DataModels as BaseModels

# a DataModel is a BaseModel and you can use it like that to create pydantic classes with attributes that bring the features of data models with it.

class ProductModel(DataModel):
    bill_of_material: BillOfMaterial
    process_model: ProcessModel




product_model = ProductModel(bill_of_material=example_product.bill_of_material, process_model=example_product.process_model)
print(product_model.get_model("example_bom_id"))