import json
import typing
import uvicorn
import aas_middleware
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter


class BillOfMaterialInfo(aas_middleware.SubmodelElementCollection):
    manufacterer: str
    product_type: str
    example_file: aas_middleware.File
    example_blob: aas_middleware.Blob


class BillOfMaterial(aas_middleware.Submodel):
    components: typing.List[str]
    bill_of_material_info: BillOfMaterialInfo


class ProcessModel(aas_middleware.Submodel):
    processes: typing.List[str]
    example_file: aas_middleware.File
    example_blob: aas_middleware.Blob


class Product(aas_middleware.AAS):
    bill_of_material: BillOfMaterial
    process_model: typing.Optional[ProcessModel]


pdf_file_path = "C:/Users/Sebas/Code/aas_middleware/examples/SB_354.pdf"

with open(pdf_file_path, "rb") as f:
    pdf_file_content = f.read()

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
            example_file=aas_middleware.File(
                id_short="example_file_123",
                media_type="text/html",
                path="https://www.wbk.kit.edu",
            ),
            example_blob=aas_middleware.Blob(
                id_short="example_blob123",
                media_type="text/html",
                content=b"""
                        <html>
                            <head>
                                <title>Some HTML in here</title>
                            </head>
                            <body>
                                <h1>Look ma! HTML!</h1>
                            </body>
                        </html>
                        """,
            ),
        ),
    ),
    process_model=ProcessModel(
        id="example_process_model_id",
        id_short="example_process_model_id",
        description="Example Process Model",
        processes=["process_1", "process_2"],
        example_file=aas_middleware.File(
            id_short="example_file_123211",
            media_type="application/pdf",
            path="https://www.wbk.kit.edu/wbkintern/CI_Tools/Studentenarbeiten/SB_354.pdf",
        ),
        example_blob=aas_middleware.Blob(
            id_short="example_blob12344",
            media_type="application/pdf",
            content=pdf_file_content,
        ),
    ),
)

data_model = aas_middleware.DataModel.from_models(example_product)

middleware = aas_middleware.AasMiddleware()
middleware.load_aas_persistent_data_model(
    "example",
    data_model,
    "localhost",
    8081,
    "localhost",
    8081,
    persist_instances=True,
    caching=True,
)

middleware.generate_rest_api_for_data_model("example")
middleware.generate_graphql_api_for_data_model("example")


if __name__ == "__main__":
    # uvicorn.run("minimal_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)
