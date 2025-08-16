''' 

entry point for all grapghql operations 

'''
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    '''
    
    root query class --- defines what queries clients can make 
    inherits from crm
    
    '''
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    """
    Main Mutation class that inherits all CRM mutations.
    
    This gives us access to:
    - createCustomer
    - bulkCreateCustomers  
    - createProduct
    - createOrder
    """
    pass

# main schema object
schema = graphene.Schema(
    query=Query,
    mutation=Mutation
)