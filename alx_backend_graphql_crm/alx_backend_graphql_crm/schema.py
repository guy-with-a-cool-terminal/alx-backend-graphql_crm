''' 

entry point for all grapghql operations 

'''
import graphene

class Query(graphene.ObjectType):
    '''
    
    root query class --- defines what queries clients can make 
    
    '''
    # define a fielda named helli that returns a string
    hello = graphene.String(
        description="Simple greeting query to test our setup"
    )
    
    def resolve_hello(self,info):
        ''' 
        
        resolver function for the hello field 
        
        '''
        return "Hello, GraphQL!"

# main schema object
schema = graphene.Schema(
    query=Query,
)