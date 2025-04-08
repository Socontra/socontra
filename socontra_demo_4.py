# Socontra demo 4
# Demo of subscription type broadcast messages. Useful to provide many agents updates or feeds of information. 
# One-way messages (one-to-many), so agents cannot reply to broadcast messages.
# Refer to protocol protocol_templates/subscription/socontra_subscription_protocol1.py

from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.subscription import  socontra_subscription_protocol
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_subscription_protocol)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    message_initiator = client_public_id + ':' + 'message_initiator'
    random_agent1 = client_public_id + ':' + 'helper_agent1'
    random_agent2 = client_public_id + ':' + 'helper_agent2'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents. 
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_initiator,
            'client_security_token': client_security_token,
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': random_agent1,
            'client_security_token': client_security_token,
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': random_agent2,
            'client_security_token': client_security_token,
        }, clear_backlog = True)

    # Join the client_group so that agents are 'connected' and can interact.
    socontra.join_client_group(agent_name=message_initiator)
    socontra.join_client_group(agent_name=random_agent1)
    socontra.join_client_group(agent_name=random_agent2)

    # Can communicate with multiple agents by creating distribution list. Will use 'direct' communication list. 
    # Will explore agent 'groups' later.
    distribution_list = {
            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            'direct' : [random_agent1, random_agent2],
        }

    # Message can be a string or json/dict.
    message='Hello, my first broadcast message'
    socontra.broadcast(agent_name=message_initiator, distribution_list=distribution_list, message=message)

    

    