import graphene
from crm.schema import CRMQuery, CRMMutation

# The Query class combines all fields from the CRM app (CRMQuery)
# and the base Graphene types (graphene.ObjectType).
class Query(CRMQuery, graphene.ObjectType):
    # This keeps the original 'hello' field defined in Task 0,
    # ensuring backward compatibility for the checkpoint test.
    hello = graphene.String(default_value="Hello, GraphQL!")
    pass

# The Mutation class combines all mutation logic from the CRM app (CRMMutation)
class Mutation(CRMMutation, graphene.ObjectType):
    pass

# Define the final schema used by the GraphQLView in urls.py
schema = graphene.Schema(query=Query, mutation=Mutation)
