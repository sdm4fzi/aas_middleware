# TODO: fill with content

## Conventions and Requirements for AAS to Object Mapping

### AAS to Object Mapping

To be able to create an object, which can be used in the middleware, from an AAS, some meta information is required. In AAS terms, concept descriptions by Data Specifications are required to define how attribute or class names should be named in the objects. This can be inferred to some extent, but relying on the identifiers to name the classes won't be handy in every way... These requirements differ for AAS, Submodels and Submodelcollections but follow the same structure, since AAS, Submodel and SubmodelCollection can be regarded as Objects of a class with attributes that have an attribute name.

The following requirements exist for specifying the mapping of AAS to Objects:
- Specifying the class name of the object (AAS, Submodel, SubmodelCollection)
- Specifying the attribute names of all contained objects (Submodels, SubmodelCollections)

### Object Mapping to AAS

The only requirement that exists for an arbitrary object to be mapped to an AAS is that the top level object, which should be an AAS, is only allowed to contain other objects as attributes. AAS cannot have SubmodelElements and therefore primitive attributes are not possible. Otherwise, Submodels will be inferred. 
