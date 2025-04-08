# Socontra demo 9
# We demonstrate the simplist agent-to-agent service transaction, which is delegation of tasks.

#### INTRODUCTION

# Key characteristics of AI agents are autonomy (or agency) and decentralization (i.e. self-control and self-interest).
# Agents can represent or act on behalf of their human or business users which comprise the same characteristics.
# AI facilitates agents because it enables agents to act autonomously, with purpose, goal driven, and ability to
# work out ways to solve problems on their own, and act on behalf of their users (like human agents in the real world).
# An agent can be a few lines of code which switch a light on and off, to a LLM which analyzes documents or
# sends emails, to an online store Web Agent which transacts with other agents for the purchase of goods and services
# for their human users (or for the agent's themselves, e.g. computational tasks to solve problems they are working on).

# However, what is important about agents, which are decentralized (specialized) autonomous programs, is that like people and
# businesses, they become useful when they work together and perform tasks (services) for each other in the open world.
# Traditional APIs are unsuitable for agent interoperability. APIs are designed for 1-way database operations or tight 
# integration of specific software systems (without autonomy), and lack a common framework for scalability. API are useful
# for integrating agents with software systems, but not for scalable agent-to-agent interactions and interoperability
# in the open world, which is 2-way transactions rather than 1-way integration.

# The best way for agents interact and transact is in the same way that people and business have done so for hundreds
# of years. Whether informal agreements between family, friends or co-workers, to commercial transactions 
# (B2C and B2B) for goods and services, transactions take place using Social Contracts (which is where the name Socontra 
# comes from: SOCial CONTRActs). Its so common place we have law (i.e. contract law) to enforce it. 
# Not only has history evolved an ideal mechanism for interoperability between 'decentralized (specialized) autonomous'
# entities, but if we want agents to act on our behalf, it makes sense and easier if they follow the same rules of 
# interoperability, e.g. easier translation of online stores to Web Agents underpinned by the same contractual protocols.

# Socontra provides a common framework consistent with Social Contracts (or contract law) that help developers create 
# protocols to enable agents to transact for services, and importantly, automate commercial transactions,
# in the open world/market.

#### BACKGROUND TO SOCONTRA SERVICE PROTOCOLS

# There are two types of agents:
# Consumer agents - require a task to be acheived/fulfilled via the acquisition of some service (or goods, products, info, etc).
# Supplier agents - can provide services to agents or their human users to achieve their tasks.

# There are four types of messages or objects that are communicated, which relate to four stages of a transaction:
#                       ####    Task -> Proposal -> Offer -> Order   #####
# - Task - A goal, piece of work or outcome that a consumer wants achieved or fulfilled. This is analogous to 
#           a search request in online stores.
# - Proposal - Non-commital exchange of options for how the supplier can achieve the task. This is analogous to 
#               product search results in online stores.
# - Offer - A proposal which the supplier (legally) commits to, i.e. a formal binding offer for the consumer.
#           This is analogous to 'add to cart' in online stores, ready for final purchase (acceptance) from the consumer.
# - Order - The consumer accepts the offer to create a mutually accepted/signed agreement. Both parties must execute their 
#           agreed obligations, e.g. the consumer makes payment (if applicable) and the supplier executed and delivers
#           the agreed order. This is analogous to 'purchase items in cart' in online stores.

# Socontra provides a set of commands that facilitate the transactions via messages between agents. Socontra provides 
# the framework and logic behind the transation, and the social network and communication layer. However the content of 
# the messages is up to the developer, which is dependent on the application.

# Note that we dont always go through all 4 stages of a transaction. In the first demo, delegation, to simplify 
# the transaction for applications such as agents delegating tasks one-on-one to other agents in an internal system 
# we only use Offer -> Order.
# The next demo, we describe a protocol for allocation, which uses Proposal -> Offer -> Order. This is also suited to agent
# interaction in an internal system, but provides exploratory search for options to achieve the task to asist with orchestration.
# The final demo we provide a template for the transact protocol, which goes through the full 4 stages of the transaction. This is
# suited to commercial transactions and online stores which involve payments and formal legal underpinnings.

# There is one more protocol which has not yet been implemented, designed during my PhD and time at Department of Defence. 
# It extendes the transact protocol but enables distributed planning and orchestration, backtracking of options, and breaking 
# up of the the task in order to piece together services to solve the problem in unanticipated (and potentially optimal) ways 
# based on the agents and their capabilities/services available at the time. This will be released at a later date.

# In this demo we utilize the delegate service protocols:
# - Consumer: protocol_templates/service/socontra_delegate_protocol_consumer.py
# - Suppliers: protocol_templates/service/socontra_delegate_protocol_supplier.py


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
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': supplier_agent,
            'client_security_token': client_security_token,
        }, clear_backlog = True)

    # Both agents join the client_group so that they are connected and can interact with each other.
    socontra.join_client_group(agent_name=consumer_agent)
    socontra.join_client_group(agent_name=supplier_agent)

    # Define the task. 
    task='Add two numbers for me'

    # Specify the timeout for receiving offer acceptances from suppliers. Service protocols rely on timeouts because in an
    # open decentralized world where agents are autonomous and self-interested, responses to requests and messages are not guaranteed.
    offer_timeout = 5

    # Start the protocol by sending a new task request.
    # The key for delegation is in the task request. We force the task to be an offer (with offer=task), which unusually allows  
    # the supplier to accept the offer/task for execution and delivery. Simple, quick and efficient protocol for delegation.
    # Refer to the delegate templates to see the types of commands/messages and the logic/stages of the protocol.
    socontra.new_request(agent_name=consumer_agent, distribution_list=supplier_agent, task=task, offer=task, offer_timeout=offer_timeout, protocol='delegate')



    
 
    