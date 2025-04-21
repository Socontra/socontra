# Socontra demo 9
# We demonstrate the simplist agent-to-agent service transaction, which is delegation of tasks.

# Refer to the pdf file "Socontra service protocols.pdf" in the main folder, and protocol modules:
# - Consumer: protocol_templates/service/socontra_delegate_protocol_consumer.py
# - Suppliers: protocol_templates/service/socontra_delegate_protocol_supplier.py

# Also see the overview and tutorial on the socontra.com web site.

#### BACKGROUND TO SOCONTRA SERVICE PROTOCOLS

# There are two types of agents:
# Consumer agents - require a task to be acheived/fulfilled via the acquisition of some service (or goods, products, info, etc).
# Supplier agents - can provide services to agents or their human users to achieve their tasks.

# There are four types of messages or objects that are communicated, which relate to four stages of a transaction:
#                       ####    Task -> Proposal -> Offer -> Order   #####
# - Task - A goal, piece of work or outcome that a consumer wants achieved or fulfilled. This is analogous to 
#           a search request in online stores.
# - Proposal - Non-committal exchange of options for how the supplier can achieve the task. This is analogous to 
#               product search results in online stores.
# - Offer - A proposal which the supplier (legally) commits to, i.e. a formal binding offer for the consumer.
#           This is analogous to 'item added to cart' in online stores, ready for final purchase (acceptance) from the consumer.
# - Order - The consumer accepts the offer to create a mutually accepted/signed agreement. Both parties are bound and must 
#           execute their agreed obligations, e.g. the consumer makes payment (if applicable) and the supplier executes and delivers
#           the agreed order. This is analogous to 'items in cart purchased' in online stores.

# Socontra provides a set of commands that facilitate the transactions via messages between agents. Socontra provides 
# the framework and logic behind the transation, and the social network and communication layer. The content of 
# the messages that represent the tasks, proposals, offers is dependent on the developer and/or application. 
# Socontra provides three 'standard' templates/protocols, however developers can modify or create their own protocols 
# for other types of service transaction.

# Note that we dont always use all 4 stages of a transaction. This demo 9: 'delegate' protocol is the simplist
# transaction where agents delegate tasks directly other agents of known capability in an internal system. 
# In this case, we only use Offer -> Order.
# The next demo, we describe a protocol for 'allocate', which uses Proposal -> Offer -> Order. This is also suited to agent
# interaction in an internal system, but provides exploratory search for options to achieve the task to assist with orchestration.
# The final demo we provide a template for the 'transact' protocol, which goes through the full 4 stages of the transaction. This is
# suited to commercial transactions and online stores which involve payments and formal legal underpinnings.

# Feature in development: A more comprehensive protocol that enables proposals that partially achieve the task, and allows deliberative 
# distributed planning and orchestration (i.e. search with backtracking), in order to piece together multiple services to solve the task.


from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.service import  socontra_delegate_protocol_consumer, socontra_delegate_protocol_supplier
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_delegate_protocol_consumer)
socontra.add_protocol(socontra_delegate_protocol_supplier)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    consumer_agent = client_public_id + ':' + 'consumer_agent'
    supplier_agent = client_public_id + ':' + 'supplier_agent'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': consumer_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': supplier_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)

    # Both agents join the client_group so that they are connected and can interact with each other.
    socontra.join_client_group(agent_name=consumer_agent)
    socontra.join_client_group(agent_name=supplier_agent)

    # Define the task. 
    task='Add two numbers for me'

    # Specify the timeout for receiving acceptances to perform the task (offer in this case) from suppliers. Service protocols rely on 
    # timeouts because in an open decentralized world where agents are autonomous and self-interested, responses to requests and messages 
    # are not guaranteed.
    offer_timeout = 5

    # Start the protocol by sending a new task request.
    # For delegation we make the task an offer (using offer=task), so that so that the consumer is bound to the agreement for services 
    # when the supplier accepts.
    socontra.new_request(agent_name=consumer_agent, distribution_list=supplier_agent, task=task, offer=task, offer_timeout=offer_timeout, protocol='delegate')



    
 
    