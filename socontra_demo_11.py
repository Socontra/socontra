# Socontra demo 11
# We demonstrate Socontra task 'transact' protocol service transaction.
# The transact protocol is comprehensive and consistent with contract law. It is suitable for any type of 
# agent-to-agent transations or applications, particularly the automation of commercial transactions, including
# creation of Web Agents as online stores for other agents/bots, and personal assistants that interact with Web Agents
# to automate commercial transactions for good and services on behalf of their human users (or agents themselves).

# Refer to the pdf file "Socontra service protocols.pdf" in the main folder, and protocol modules:
# - Consumer: protocol_templates/service/socontra_transact_protocol_consumer.py
# - Suppliers: protocol_templates/service/socontra_transact_protocol_supplier.py


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
# - Proposal - Non-committal exchange of options for how the supplier can achieve the task. This is analogous to 
#               product search results in online stores.
# - Offer - A proposal which the supplier (legally) commits to, i.e. a formal binding offer for the consumer.
#           This is analogous to 'add to cart' in online stores, ready for final purchase (acceptance) from the consumer.
# - Order - The consumer accepts the offer to create a mutually accepted/signed agreement. Both parties are bound and must 
#           execute their agreed obligations, e.g. the consumer makes payment (if applicable) and the supplier executes and delivers
#           the agreed order. This is analogous to 'purchase items in cart' in online stores.

# Socontra provides a set of commands that facilitate the transactions via messages between agents. Socontra provides 
# the framework and logic behind the transation, and the social network and communication layer. However the content of 
# the messages is up to the developer, which is dependent on the application. Provide three 'standard' templates/protocols,
# however developers can modify or create their own service protocols for any type of transaction.

# Note that we dont always use all 4 stages of a transaction. The demo 9: 'delegation' protocol, simplifies
# the transaction for applications such as agents delegating tasks one-on-one to other agents in an internal system. 
# In this case, we only use Offer -> Order.
# The next demo, we describe a protocol for 'allocation', which uses Proposal -> Offer -> Order. This is also suited to agent
# interaction in an internal system, but provides exploratory search for options to achieve the task to asist with orchestration.
# The final demo we provide a template for the 'transact' protocol, which goes through the full 4 stages of the transaction. This is
# suited to commercial transactions and online stores which involve payments and formal legal underpinnings.

# There is one more protocol which has not yet been implemented, designed during my PhD and time at Department of Defence. 
# It extendes the transact protocol but enables distributed planning and orchestration, backtracking of options, and breaking 
# up of the the task in order to piece together services to solve the problem in unanticipated (and potentially optimal) ways 
# based on the agents and their capabilities/services available at the time. This will be released at a later date.



from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.service import  socontra_transact_protocol_consumer, socontra_transact_protocol_supplier
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_transact_protocol_consumer)
socontra.add_protocol(socontra_transact_protocol_supplier)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    consumer_agent = client_public_id + ':' + 'consumer_agent'
    supplier_agent1 = client_public_id + ':' + 'supplier_agent1'
    supplier_agent2 = client_public_id + ':' + 'supplier_agent2'
    supplier_agent3 = client_public_id + ':' + 'supplier_agent3'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': consumer_agent,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': supplier_agent1,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': supplier_agent2,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': supplier_agent3,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)

    # Both agents join the client_group so that they are connected and can interact with each other.
    socontra.join_client_group(agent_name=consumer_agent)
    socontra.join_client_group(agent_name=supplier_agent1)
    socontra.join_client_group(agent_name=supplier_agent2)
    socontra.join_client_group(agent_name=supplier_agent3)

    # Send the task request to the three supplier agents.
    distribution_list = {
            # Specify groups that the agent is a member of to communicate with the groups' members.
            # Values for 'group_scope' are: 'direct' (specified group only), 'local' (includes sub-groups), 
            #            'global' (includes sub-groups and parent groups), and 'exclusive' (includes parent groups).
            #  'groups' :[{}, {}]

            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            'direct' : [supplier_agent1, supplier_agent2, supplier_agent3],
        }

    # Define the task. 
    task='Add two numbers for me'

    # Timeout in seconds for receiving non-binding proposals (search results) to achieve the task. Service protocols rely on timeouts 
    # because in an open decentralized world where agents are autonomous and self-interested, responses to requests and messages are 
    # not guaranteed.
    proposal_timeout = 5

    # Timeout in seconds for receiving binding offers from suppliers. 
    invite_offer_timeout = 5

    # For the Socontra transact protocol, we use a central orchestrator, which we call below.
    # Refer to the two templates protocol_templates/service/socontra_transact_protocol_consumer.py and
    # protocol_templates/service/socontra_transact_protocol_supplier.py to see the types of commands/messages and the 
    # logic/stages of the protocol.
    socontra.transact_orchestrator_consumer(consumer_agent, task, distribution_list, proposal_timeout, invite_offer_timeout)

    
