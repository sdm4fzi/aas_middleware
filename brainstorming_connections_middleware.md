## Brainstorming: Connecting Data Models to Workflows, Consumers, Providers and Persistence

To connect a data model (or individual fields), the middleware should have methods to make the mappings of indiividual objects in the data model or complete data models to the assocaited connecting actor.



``` python
from aas_middleware import Middleware, DataModel

middleware = Middleware()
data_model = DataModel()

middleware.load_data_model("example_model", data_model)
```

At first, one can specify the persistence of a data model. This is needed for accessing values of the data model. A Persistence is thereby a special type of Consumer / Provider that is executed every time, when an object of the data model is needed or updated.

``` python
aas_connector = AasConnector(url="localhost:8081") # Also allow to specify the aas and sm-repository individually and allow to specify a registry url
middleware.add_persistence(data_model="example_model", aas_connector)
# Loading persistence is also possible for individual objects or types
middleware.add_persistence(model="example_instance", aas_connector)
middleware.add_persistence(model_type="example_type_name", aas_connector)
```

Inside the middleware, when adding persistence, automatically providers and consumers are created that connect the models and the connectors. 
Persistence for data models is done on a model level. 

``` python
add_persistence(data_model: DataModel, aas_connector: AasConnector):
    for model in data_model.get_all_contained_models():
        consumer = Consumer(model, aas_connector)
        provider = Provider(model, aas_connector)
        self.persistence_consumers[model.id] = consumer
        self.persisteince_providers[model.id] = provider
```

All other consumers, providers and workflows are saved independantly in the middleware. If a consumer or a provider should be connected to the persistence, the need to be added as PersistentConsumer / PersistentProvider. They can then be executed and save / send the data automatically to the persistence data_model / model / field. Inside of the data model a Workflow is created that represents this logic.

``` python
add_persistent_consumer(consumer: Consumer, data_model_name: str):
    # check if data model of the consumer is available in the middleware, if not add it
    # make a case distinction if consumers are related to a field, model or datamodel
    
    def persistent_consumer_workflow(consumer):
        payload = self.persistence_providers[data_model_name]
        consumer.execute(payload)
    self.add_workflow(persistent_consumer_workflow)
```

Same adding logic exists for workflows and providers. If one of them needs to be executed, a simple logic can be used.

``` python
execute_consumer(consumer_id: str, payload: Optional[DataModel]):
    # check if data model of the consumer is available in the middleware, if not add it
    # make a case distinction if consumers are related to a model of a data model or a data model itself
    consumer = self.consumers[consumer_id]
    if not payload:
        payload = self.persistence_providers[consumer_id].execute()
    consumer.execute(payload)
```


Providers and consumers need to be defined for three use cases:
- FieldProviders, FieldConsumers -> need to provide/consume data of one field of a model
    - It needs to be known to which data model they belong
    - It needs to be known to which model they belong
    - It needs to known to which attribute of the model they belong
- ModelProviders, ModelConsumers -> need to provide/consume data of one model
    - It needs to be known to which data model they belong
    - It needs to be known to which model they belong in the data model
- DataModelProviders, DataModelConsumers -> need to provide / consume data of one data model
    - Only the data model needs to be known

Ideally, these three providers specify the same API -> provider: execute() -> payload or consumer: execute(payload) -> None
To do this, they need to have a function that in their protocol that allows to retrieve information where the data should come from or where the data should go. This should be in the ProviderInfo / ConsumerInfo:

``` python
class ConsumerInfo(BaseModel):
    consumer_type: Literal["field", "model", "data_model"]
    data_model_id: str
    model_id: Optional[str]
    field_id: Optional[str]
```

With this info, the middleware can detect where the data needs to come from or goes to, if this consumer is executed.

``` python
execute_consumer(consumer_id: str, payload: Optional[DataModel]):
    # check if data model of the consumer is available in the middleware, if not add it
    # make a case distinction if consumers are related to a model of a data model or a data model itself
    consumer = self.consumers[consumer_id]
    if not payload:
        payload = self.persistence_providers[consumer_id].execute()
    consumer.execute(payload)
```

Use cases of consumers:
- C1: A data model / one model should be send to a service upon request
- C2: An OPC UA field should be updated from the middleware when the value changes in the middleware

Use Cases for providers:
- P1: A data model / one model should be retrieved from a service upon request
- P2: An sql table should be retrieved in periodic cycles
- P3: A mqtt message should be saved in the middleware upon arrival

C1:
Required information for integrating the consumer in the middleware:
- where to get the payload from (either from RestAPI or a provider / persistence)
- where to send the data (url + Rest method)

C2:
Required information for integration in the middleware:
- which field in the middleware is connected to consumer
- when does the field changes in value?
- where to send the data


## Key Concepts Providers / Consumers:
- A Consumer requires data to be executed, a Provider gives data when executed
- When consumers / providers are added to the middleware, one can specify how the should be executed and how they are integrated
    - should they be connected to the persistence? Thus, automatically the persistence of the middleware provides / consumes the data or not?
    - on_start_up? on_shut_down?
    - periodic_trigger
    - event_trigger -> Callbacks for a value change to the persistence

on_start_up, on_shutdown, periodic_trigger and event_trigger are only possible if integration to persistence is available. 

This options should be the same as for the workflows. 

Thus there need to be two methods to add the consumer:
- add_consumer(consumer: Consumer)
- connect_consumer(consumer: Consumer, data_model_id: str, model_id: str, field_name: str, on_start_up: bool, on_shutdown: bool, interval: float, event_trigger: Event)


# Functionalities of connectors in the middleware

Connectors can be added to the middleware with the following information:
- name: the name of the connector
- connector: the connector that should be added


Connectors can be connected to the middleware with the following information:
- connector_id: the name of the connector
- connector: the connector that should be connected
- data_model_id: the data model id to which the connector should be connected
- model_id: the model id to which the connector should be connected
- contained_model_id: the contained model id in the model with model_id to which the connector should be connected
- field_name: the field name to which the connector should be connected
- on_start_up: if the connector should be executed on start up
- on_shutdown: if the connector should be executed on shut down
- interval: the interval in which the connector should be executed (if 0, no waiting time)

## 1. Connectors without persistence

The connectors can be executed by an API call to the middleware in the connection API. 

endpoints:
- post connector/value: The API has a post method that allows to execute a consumer with a payload, this payload is then send to the consumer
- get connector/value: The API has a get method that allows to retrieve the value of a provider

This works fine for request/response based connectors. However, publish / subscribe connectors need to be executed in a different way -> maybe use a async queue to save the values.

## 2. Connectors with persistence

The connectors can be executed by an API call to the middleware in the connection API.

endpoints:
- post connector/value: The API has a post method that allows to execute a consumer with a payload, this payload is then send to the consumer and also send to the persistence to update the data model. If no payload is given, the persistence is executed to get the data.
- get connector/value: The API has a get method that allows to retrieve the value of a provider. The provider is executed and the value is returned. If the provider is connected to the persistence, the persistence is updated with the new value.


## 3. Connectors that are executed in the background to automatically update the persistence

Use workflows for this and maybe add convenience functions to do this. (Workflow executed on start up, on shut down, periodic trigger, event trigger...) -> e.g. an example function / class called persistence_connector_workflow that automatically updates the persistence with the new value of the connector.