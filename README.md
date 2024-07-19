![aas middleware logo](https://raw.githubusercontent.com/sdm4fzi/aas_middleware/main/resources/logos/aas_middleware_logo_light_letters.svg)

*Framework for industrial data integration and automation*

![Build-sucess](https://img.shields.io/badge/build-success-green)
![PyPI](https://img.shields.io/pypi/v/aas_middleware)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aas_middleware)
![Docu](https://img.shields.io/badge/docu-full-green)
<!-- TODO: add DOI -->
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10995273.svg)](https://doi.org/10.5281/zenodo.10995273) -->

aas-middleware has the goal to make information flow and orchestration in industrial environments easier and more automated. To do so, it is build upon three concepts: well defined data models and interfaces, connectors and workflows. The data models are used to define the structure of the data that is exchanged between different systems. The connectors are used to connect the data models to technologically different data sources and sinks. Workflows are used to define the orchestration of the data flow between different systems. 

Standard api technologies (Rest or GraphQL) of the middleware make it easy to access the integrated data models or exchange data with low-level sensors and actuators. The middleware can be used to integrate different systems in the industrial environment, such as MES, ERP, SCADA, PLC, sensors and actuators. By the modular and extensible design of aas-middleware, it can be used from small use cases, such as streaming sensor values, to large integrations and workflows for automated production planning and control. 

For more information to use the middleware, read the getting started below or refer to the ![documentation](https://sdm4fzi.github.io/aas_middleware/) of the package.

# Installation

To install the package, run the following command in the terminal: 

```bash
pip install aas-middleware
```

To install the package with extras for industrial data integration (opc ua and mqtt), run the following command in the terminal:

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

In the following, we will consider a minimal example to demonstrate the usage of the package. The example is also available in the [examples](examples/) and consists of defining a simple aas-based data model to describe a product, serializing this data model to asset administration shells, making the data model available with rest API and defining examplary connectors and workflows.

For further examples, like connecting the data model to a data source, or creating workflows, refer to the tutorials in the [documentation](https://sdm4fzi.github.io/aas_middleware/).

### Defining a simple data model and formatting

At first, we create a simple data model with the basic building blocks (AAS and Submodel) of aas2openapi:

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

The data model consists of a product that has a process model and a bill of material. The process model and the bill of material are contain a list of processes and components, respectively. To be able to instantiate an data model, we create an instance of this data model:

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


With this instance of the product data model, we can create a DataModel.


```python
data_model = aas_middleware.DataModel.from_model(example_product)
```


The data model is a container for instances and types of data models. It makes access to individual objects easy and allows for formatting. E.g. we can easily transform the data model to either basyx aas components:

```python
basyx_object_store = aas_middleware.formatting.BasyxFormatter().serialize(data_model)
```



Or serialize it to a JSON-serialized asset administration shell according to DOT AAS 3.0:

```python
json_aas = aas_middleware.formatting.AasJsonFormatter().serialize(data_model)
print(json_aas)
```


This formatting transformation can also be reversed, so JSON-serialized or Basyx aas can be used to create data models.

### Starting the middleware with aas persistence

Running the middleware with storage of the data model in a basyx aas server can be done by running the following command: 

```python
middleware = aas_middleware.AasMiddleware()
middleware.load_aas_persistent_data_model(
    "example", data_model, "localhost", 8081, "localhost", 8081, initial_loading=True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(middleware.app)
```

Note, that on port 8081 a aas repository and submodel repository need to be running. The repository already comes with a docker-compose file that can be used to start the AAS and Submodel-server. To start the docker-compose file, run the following command in the terminal:

```bash
docker-compose -f docker-compose-dev.yaml up
```

However, you can also start middlewares with internal memory, just by using `aas_middleware.Middleware()`.

The middleware starts now and registers the example product instance in the aas server. You can access now the documentation of the REST API with swagger at `http://localhost:8000/docs` and the graphql endpoint at  `http://localhost:8000/graphql`. We can get the data again in the format of the middleware by sending the following query:

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


### Creating an examplary connector and workflow

A connector in the aas middleware is a component that makes a connector to a data source (provider) or a data sink (consumer). The aas middleware comes with a lot of default connectors (opc ua, mqtt, http, websocket, webhook), but you can add custom ones. A connector only needs to specify a certain interface, that consists of a connect, disconnect, consume and provide function. We define an examplary connector like this and add it to the middleware:

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

Lastly, we can define workflows for more complex automation tasks. A workflow is a functino that can be executed in the middleware:

``` python
@middleware.workflow()
def example_workflow(a: str) -> str:
    print(a)
    return a
```

To run the workflow, execute the followingrequest:

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

## Contributing

`aas-middleware` is a new project and has therefore much room for improvement. Therefore, it would be a pleasure to get feedback or support! If you want to contribute to the package, either create issues on [aas_middlweware github page](https://github.com/sdm4fzi/aas-middleware) for discussing new features or contact me directly via [github](https://github.com/SebBehrendt) or [email](mailto:sebastian.behrendt@kit.edu).

## License

The package is licensed under the [MIT license](LICENSE).

## Acknowledgements

We extend our sincere thanks to the German Federal Ministry for Economic Affairs and Climate Action
(BMWK) for supporting this research project 13IK001ZF “Software-Defined Manufacturing for the
automotive and supplying industry [https://www.sdm4fzi.de/](https://www.sdm4fzi.de/).
