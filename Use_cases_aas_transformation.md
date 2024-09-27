
# Loading types to the middleware

These cases describe how data types are loaded to the middleware via the admin API. 

## From unknown AAS format (API or programatically)

This procedure describes how an AAS is loaded to the middleware by transforming it to a pydantic BaseModel with same information content:

1. The AAS is loaded to the middleware via the admin API per POST-request. Parameters are the DataModel to add the type too and whether to create REST or GraphQL API (or both). The type definition (AAS JSON data (1), list of aas url ids on server (2) or url of server (3)) is passed as body. 
2. It is checked whether the AAS contains submodels with submodel templates. If a template exists, this is used to create the type. If not, the middleware tries to infer the type from the submodel data (should be viable to but not as robust as using the template). Submodel template should be saved later in the backend and used for validation of the instance!
3. aas and submodels are transformed to Pydantic models. If there are attribute and class name attribute name concept descriptions available, they are used. Otherwise, the id_short is used for the attribute name. **Convention: 1. attribute names are underscore seperated lower case and class names are camel case. 2. Attributes (but id and id_short) are always optional with None as default.** 
4. A Rest API and GraphQL API is created from the newly provided AAS. 

## From Pydantic models from python (programmatically)

Typical procedure and persist the type via a submodel template that contains all the type information via normal AAS Meta Model and Concept Descriptions for attribute names etc. 

## From Json Schema (API or programatically)

Create a pydantic model from the JSON Schema and save this model then like above. 

# Loading instances to the middleware

These cases describe how instances are loaded to the middleware via the admin API.

## From unknown AAS format

1. The type of the AAS format it determined like above.
2. If the format is provided via a file (1), the instances are extracted and persisted in the backend. If the format is provided via a list of urls to aas ids (2), the instances are loaded from the urls and persisted in the backend. If only a aas server or registry url (3) is provided, all types are scanned and all instances created. 
3. The instances are transformed to Pydantic models. If there are attribute and class name attribute name concept descriptions available, they are used. Otherwise, the id_short is used for the attribute name. 

## From Pydantic model instances from python

Typical procedure and persist the instances via the admin API.

## From Json instances

Requires that the type is already loaded. The instances are transformed to Pydantic models and persisted in the backend. 

# AAS utilities

submodel template validation: 
1. A submodel and its template is passed
2. The submodel is transformed to its pydantic model instance
3. The template is transformed to its pydantic model
4. The submodel is validated against the template as a dictionary.