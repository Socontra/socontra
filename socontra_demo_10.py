# Socontra demo 10
# We demonstrate Socontra task 'allocation' protocol service transaction.
# Allocate protocol can help with orchestration where there are multiple agents (internally developed agents or 
# externally developed specialized agents anywhere in the world) that can achieve the task, and the 
# orchestrator wants to assess the different options to optimize the outcome.

# Refer to the pdf file "Socontra service protocols.pdf" in the main folder, and protocol modules:
# - Consumer: protocol_templates/service/socontra_allocate_protocol_consumer.py
# - Suppliers: protocol_templates/service/socontra_allocate_protocol_supplier.py

# Also see the overview and tutorial on the socontra.com web site, and comments in socontra_demo_9.py file.


from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.service import  socontra_allocate_protocol_consumer, socontra_allocate_protocol_supplier
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_allocate_protocol_consumer)
socontra.add_protocol(socontra_allocate_protocol_supplier)


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

    # Specify the timeout for receiving offers from suppliers to achieve the task. Service protocols rely on timeouts because in an
    # open decentralized world where agents are autonomous and self-interested, responses to requests and messages are not guaranteed.
    invite_offer_timeout = 5

    # For the Socontra allocate protocol, we use a central orchestrator, contained in the protocol template file
    # protocol_templates/service/socontra_allocate_protocol_consumer.py.
    socontra.allocate_orchestrator_consumer(consumer_agent, task, distribution_list, invite_offer_timeout)

    
