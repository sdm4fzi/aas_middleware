import json
import pathlib
import typing
import uvicorn
import aas_middleware
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter


class FileAndBlobContainer(aas_middleware.Submodel):
    html_file: aas_middleware.File
    pdf_file: aas_middleware.File
    html_blob: aas_middleware.Blob
    pdf_blob: aas_middleware.Blob


class ExampleAAS(aas_middleware.AAS):
    example_submodel: typing.Optional[FileAndBlobContainer] = None


pdf_file_path = pathlib.Path(__file__).parent / "resources" / "example_pdf.pdf"

with open(pdf_file_path, "rb") as f:
    pdf_file_content = f.read()

example_product = ExampleAAS(
    id="example_aas_id",
    id_short="example_aas_id",
    description="Example AAS",
    example_submodel=FileAndBlobContainer(
        id="example_blob_and_file_container",
        id_short="example_blob_and_file_container",
        description="Example Container for html and pdf blob and files.",
        html_file=aas_middleware.File(
            id_short="example_html_file",
            media_type="text/html",
            path="https://de.wikipedia.org/wiki/Industrie_4.0",
        ),
        pdf_file=aas_middleware.File(
            id_short="example_pdf_file",
            media_type="application/pdf",
            path="https://publikationen.bibliothek.kit.edu/1000168519/152272154",
        ),
        html_blob=aas_middleware.Blob(
            id_short="example_html_blob",
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
        pdf_blob=aas_middleware.Blob(
            id_short="example_pdf_blob",
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

    # visit the examples at (see http://127.0.0.1:8000/docs#/):
    # - All Product data with the instance: http://127.0.0.1:8000/ExampleAAS/
    # - Example html file: http://127.0.0.1:8000/ExampleAAS/example_aas_id/example_submodel/html_file
    # - Example pdf file: http://127.0.0.1:8000//ExampleAAS/example_aas_id/example_submodel/pdf_file
    # - Example html blob: http://127.0.0.1:8000/ExampleAAS/example_aas_id/example_submodel/html_blob
    # - Example pdf blob: 'http://127.0.0.1:8000/ExampleAAS/example_aas_id/example_submodel/pdf_blob
