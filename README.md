# TODO: fill with content

## Conventions and Requirements for AAS to Object Mapping

### AAS to Object Mapping

To be able to create an object, which can be used in the middleware, from an AAS, some meta information is required. In AAS terms, concept descriptions by Data Specifications are required to define how attribute or class names should be named in the objects. This can be inferred to some extent, but relying on the identifiers to name the classes won't be handy in every way... These requirements differ for AAS, Submodels and Submodelcollections but follow the same structure, since AAS, Submodel and SubmodelCollection can be regarded as Objects of a class with attributes that have an attribute name.

The following requirements exist for specifying the mapping of AAS to Objects:
- Specifying the class name of the object (AAS, Submodel, SubmodelCollection)
- Specifying the attribute names of all contained objects (Submodels, SubmodelCollections)

### Object Mapping to AAS

The only requirement that exists for an arbitrary object to be mapped to an AAS is that the top level object, which should be an AAS, is only allowed to contain other objects as attributes. AAS cannot have SubmodelElements and therefore primitive attributes are not possible. Otherwise, Submodels will be inferred. 



## DataModel

The DataModel is the most basic building block of the middleware and allows to create complex data structures that can be used in the middleware. The DataModel can be used for:
- creating CRUD APIs of the DataModel and persistence in the AAS server
- allowing to define data mappings to other data models
- connecting fields of the data model to data sources and sinks with connectors. 

A DataModel inherits from pydantic BaseModel and can therefore be used like a pydantic BaseModel. However, some extra functionalities are provided to make handling of complex data models easier. Internally, a DataModel has a graph structure that represents the data structure of the graph. The graph structure works as follows:
- Each node in the graph represents an object contained in the DataModel
- Each edge in the graph represents a relation between two objects in the DataModel

An edge can thereby be a direct relation between two objects (composition) or an indirect relation (by referencing the id of another object). The graph structure allows to easily access objects and their relating objects. 

The DataModel allows to retrieve objects either with original relations (direct and indirect), or with resolved relations (purely direct or puerly indirect). Resolving relations means that the objects that are referenced by an id are retrieved and added to the object (or vice versa). This allows to easily access all related objects of an object.

