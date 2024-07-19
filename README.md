![aas-middleware logo](https://raw.githubusercontent.com/sdm4fzi/aas_middleware/main/docs/logos/aas_middleware_logo_light_letters.svg)

*Framework for industrial data integration and automation.*

![Build-sucess](https://img.shields.io/badge/build-success-green)
![PyPI](https://img.shields.io/pypi/v/aas_middleware)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aas_middleware)
![Docu](https://img.shields.io/badge/docu-full-green)
<!-- TODO: add DOI -->
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10995273.svg)](https://doi.org/10.5281/zenodo.10995273) -->

aas-middleware has the goal to make information flow and orchestration in industrial environments easier and more automated. To do so, it is build upon three concepts: well defined data models and interfaces, connectors and workflows. The data models are used to define the structure of the data that is exchanged between different systems. The connectors are used to connect the data models to technologically different data sources and sinks. Workflows are used to define the orchestration of the data flow between different systems. 

aas-middleware uses modern api technologies (Rest or GraphQL) to make it easy to access the integrated data models or exchange data with low-level sensors and actuators. The middleware can be used to integrate different systems in the industrial environment, such as MES, ERP, SCADA, PLC, sensors, actuators and asset administration shells. By the modular and extensible design of aas-middleware, it can be used from small use cases, such as streaming sensor values, to large integrations and workflows for automated production planning and control. 

For more information how to use the aas-middleware, read the getting started below or refer to the [documentation](https://sdm4fzi.github.io/aas_middleware/) of the package.

# Installation

To install the package, run the following command in the terminal: 

```bash
pip install aas-middleware
```

To install the package with extras for industrial data integration (OPC UA and MQTT), run the following command in the terminal:

```bash
pip install aas-middleware[industrial]
```

Alternatively, you can install the package with [poetry](https://python-poetry.org/) for development:

```bash
poetry shell
poetry install
```

Please note that the package is only compatible with Python 3.10 or higher.


# Getting Started

In the following, we will consider a minimal example to demonstrate the usage of the package. The example is also available in the [examples](https://github.com/sdm4fzi/aas_middleware/blob/main/examples/minimal_example.py) of the repository and consists of defining a simple asset administration shell based data model to describe a product, serializing this data model to asset administration shells, making the data model available with rest API and defining examplary connectors and workflows.

For further examples, like connecting the data model to a data source, or creating workflows, refer to the tutorials in the [documentation](https://sdm4fzi.github.io/aas_middleware/).

### Defining a simple data model and formatting

At first, we create a simple data model with the basic building blocks of the aas meta model:

```python
import typing
import aas_middleware

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
    process_model: typing.Optional[ProcessModel]
```

The data model consists of a product that has a process model and a bill of material. The process model and the bill of material are contain a list of processes and components, respectively. Note, that the aas-middleware can also use data models that are not compliant with the aas meta model. However, some features, such as storing the data model in a basyx aas server, requires that the data model can be translated to the aas meta model.

To be able to instantiate an data model, we create an instance of the Product:

```python
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
```


With this instance of the product, we can create a DataModel.


```python
data_model = aas_middleware.DataModel.from_model(example_product)
```


The data model is a container for instances and types of data models. It makes access to individual objects easy and allows for formatting. E.g. we can easily transform the data model to either aas components of the [basyx python sdk](https://github.com/eclipse-basyx/basyx-python-sdk):

```python
basyx_object_store = aas_middleware.formatting.BasyxFormatter().serialize(data_model)
```

Or serialize it to a JSON-serialized asset administration shell according to the official [specification of the asset administration shell ](https://industrialdigitaltwin.org/content-hub/aasspecifications):

```python
json_aas = aas_middleware.formatting.AasJsonFormatter().serialize(data_model)
print(json_aas)
```


This formatting transformation can also be reversed, so JSON-serialized or Basyx aas can be used to create data models.

### Starting the aas-middleware with internal storage and aas persistence


To start the aas-middleware and make our data model available through a rest API, we need to create an instance of the middleware and load the data model:

```python
middleware = aas_middleware.Middleware()
middleware.load_data_model("example", data_model, persist_instances=True)
middleware.generate_rest_api_for_data_model("example")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(middleware.app)
```

With the option `persist_instances=True`, the middleware stores the instances of the data model in its internal memory. Moreover, a CRUD (create, read, update, delete) rest API is generated for the data model with the `generate_rest_api_for_data_model` function. 

Under the hood, the aas-middleware uses the [fastapi](https://fastapi.tiangolo.com/) framework to generate the rest API. Therefore, we get an openAPI specification of this API under `http://localhost:8000/docs`. The data model can be accessed via the API with the following curl command:

``` bash
curl -X 'GET' \
  'http://127.0.0.1:8000/Product/' \
  -H 'accept: application/json'
```

We can also instantiate new product data models with post requests:

``` bash 
curl -X 'POST' \
  'http://127.0.0.1:8000/Product/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id_short": "product2",
  "description": "",
  "id": "product2",
  "bill_of_material": {
    "id_short": "product2_bom",
    "description": "",
    "id": "product2_bom",
    "semantic_id": "",
    "components": [
      "bearing", "screw"
    ],
    "bill_of_material_info": {
      "id_short": "product2_bom_info",
      "description": "",
      "semantic_id": "",
      "manufacterer": "other manufacturer",
      "product_type": "wheel"
    }
  },
  "process_model": {
    "id_short": "product2_process_model",
    "description": "",
    "id": "product2_process_model",
    "semantic_id": "",
    "processes": [
      "assembly"
    ]
  }
}'
```
 Besides a rest API, aas-middleware also provides a GraphQL API. To make a data model available via the GraphQL API, use the `generate_graphql_api_for_data_model` function. 
 
```python
middleware.generate_graphql_api_for_data_model("example")
``` 
 
 The GraphQL API can be accessed under `http://localhost:8000/graphql`, where also find the GraphiQL Playground for testing. Some fields of the instances of the product data model can be accessed via the API with the following curl command:

``` bash
curl 'http://127.0.0.1:8000/graphql/?' \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  --data-raw '{"query":"{\n  Product {\n    idShort\n    billOfMaterial {\n      components\n    }\n  }\n}"}'
```

You probably saw during the startup of the middleware a warning log message like:

```
WARNING:aas_middleware.middleware.registries:No persistence factory found for data_model_name='example' model_id=None contained_model_id=None field_id=None. Using default persistence factory.
```

This message indicates that the aas-middleware has no specified persistence factory and stores the data model in internal storage. Besides internal storage, the aas-middleware can utilize different persistence mechanisms. For now, aas-middleware supports the storage of the data model in a basyx aas server (mongo db will come later).

Running the middleware with persistent storage of the data model in a basyx aas server can be done by interchanging the default `Middleware` with the `AasMiddleware`: 

```python
middleware = aas_middleware.AasMiddleware()
middleware.load_aas_persistent_data_model(
    "example", data_model, "localhost", 8081, "localhost", 8081, persist_instances=True
)
middleware.generate_rest_api_for_data_model("example")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(middleware.app)
```

Note, that on port 8081 a aas repository and submodel repository need to be running, e.g. a [basyx java server](https://github.com/eclipse-basyx/basyx-java-server-sdk). The repository already comes with a [docker-compose file](https://github.com/sdm4fzi/aas_middleware/blob/main/docker/docker-compose-dev.yaml) that can be used to start the AAS and Submodel-server. To start the servers with the linked compose file, run the following command in the terminal:

```bash
docker-compose -f docker-compose-dev.yaml up
```

The created rest API can be accessed in the same way as before.

### Creating an examplary connector and workflow

A connector in the aas-middleware is a component that makes a connector to a data source (provider) or a data sink (consumer). The aas-middleware comes with a lot of default connectors (OPC UA, MQTT, http client and server, websocket client and server, webhook), but you can add custom ones. A connector only needs to specify a certain [interface](https://github.com/sdm4fzi/aas_middleware/blob/main/aas_middleware/connect/connectors/connector.py), that consists of a connect, disconnect, consume and provide function. We define an examplary connector like this and add it to the middleware:

``` python
class TrivialConnector:
    def __init__(self):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: str) -> None:
        print(body)
        pass

    async def provide(self) -> typing.Any:
        return "trivial connector example value"
    
example_connector = TrivialConnector()
middleware.add_connector("test_connector", example_connector, model_type=str)
```

We can execute this connector either for reading values with the folling get request:

``` bash
curl -X 'GET' \
  'http://127.0.0.1:8000/connectors/test_connector/value' \
  -H 'accept: application/json'
```

Or send data with the connector to the data sink:

``` bash
curl -X 'POST' \
  'http://127.0.0.1:8000/connectors/test_connector/value?value=connector_example_input_value' \
  -H 'accept: application/json' \
  -d ''
```

Lastly, we can define workflows for more complex automation tasks. A workflow is a function that can be executed via the API the middleware:

``` python
@middleware.workflow()
def example_workflow(a: str) -> str:
    print(a)
    return a
```

To run the workflow, execute the following request:

``` bash
curl -X 'POST' \
  'http://127.0.0.1:8000/workflows/example_workflow/execute?arg=work_flow_input_value' \
  -H 'accept: application/json' \
  -d ''
```

We can also interrupt the workflow, when it is running:

``` bash
curl -X 'GET' \
  'http://127.0.0.1:8000/workflows/example_workflow/interrupt' \
  -H 'accept: application/json'
```

The contents above only demostrate the most fundamental features of the aas-middleware. For more advanced features, like connecting this fundametals for automated information flow in a production environment, refer to the [documentation](https://sdm4fzi.github.io/aas_middleware/).

## Contributing

`aas-middleware` is a new project and has therefore much room for improvement. Therefore, it would be a pleasure to get feedback or support! If you want to contribute to the package, either create issues on [aas-middlweware github page](https://github.com/sdm4fzi/aas_middleware) for discussing new features or contact me directly via [github](https://github.com/SebBehrendt) or [email](mailto:sebastian.behrendt@kit.edu).

## License

The package is licensed under the [MIT license](LICENSE).

## Acknowledgements

We extend our sincere thanks to the German Federal Ministry for Economic Affairs and Climate Action
(BMWK) for supporting this research project 13IK001ZF “Software-Defined Manufacturing for the
automotive and supplying industry [https://www.sdm4fzi.de/](https://www.sdm4fzi.de/).
