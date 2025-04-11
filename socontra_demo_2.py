# Socontra demo 2
# Create a new protocols using general purpose messages, endpoints for specific agents, and configure recipient types.
# Refer to protocol protocol_templates/message/socontra_message_protocol2.py

from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.message import  socontra_message_protocol2
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_message_protocol2)


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
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': random_agent1,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': random_agent2,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
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
    message={'message': "Can you generate a random number from 1 to 10 to guess the number I'm thinking of?",
             'next_agent_to_guess': 'socontra_demo:helper_agent1'}
    
    # Start a dialogue with the two helper agents to play the distributed game according to the protocol in
    # protocol_templates/message/socontra_message_protocol2.py.
    # Note that we are creating our own message_type, protocol and recipient_type with socontra.new_message()
    # and socontra.reply_message(), with their own endpoints to receive agent messages, in order to create
    # our new agent protocols.
    socontra.new_message(agent_name=message_initiator, distribution_list=distribution_list, message=message, 
                         message_type='guess_my_number', protocol='my_new_protocol', recipient_type='helper')

    
