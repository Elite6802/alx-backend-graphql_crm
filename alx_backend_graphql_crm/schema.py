import graphene

# 1. Define the primary Query class for the GraphQL endpoint
class Query(graphene.ObjectType):
    # Declare a field named 'hello' which returns a String
    # The 'resolve_hello' method handles the logic for this field
    hello = graphene.String()

    def resolve_hello(root, info):
        # Return the required default string
        return "Hello, GraphQL!"

# 2. Define the top-level Schema, listing the available queries
schema = graphene.Schema(query=Query)