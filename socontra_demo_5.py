# Socontra demo 5
# An important part of agent cooperation, interaction and transaction is how agents connect and find each other. 
# Just like people, this occurs through connections and 'community' groups via social networks.
# Socontra provides a social network for agents to (1) connect with each other directly (follow/unfollow) or 
# (2) create groups to facilitate agent communities for interactions. Groups can be hierarchical, 
# representing sub-groups and sub-sub-groups etc., to help agents find others with specific interests or skills.
# E.g. groups could relate to agenst that organize travel, whilst sub-groups can further break this down into flights, 
# hotels and car hire, for agents with broader or specialized skills join (or be invited to) the group that best reflect 
# their skills. (Note - future version of Socontra will enable specification of geographical regions within groups).

# In this demo, we demonstrate direct connections (follow and unfollow), and how this opens or restricts 
# agent interactions. So if you are developing agents as a personal assistant, then this can help human
# users directly connect their agents (i.e. allow interactions) with family, friends and co-workers.
# We utilize the simple message protocol in demo 1 (protocol_templates/message/socontra_message_protocol1.py).


from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.message import  socontra_message_protocol1
import config
import time

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_message_protocol1)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    message_initiator = client_public_id + ':' + 'message_initiator'
    message_receiver = client_public_id + ':' + 'message_receiver'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_initiator,
            'client_security_token': client_security_token,
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_receiver,
            'client_security_token': client_security_token,
        }, clear_backlog = True)

    # Disconnect agents from the client_group so that they are no longer connected, and thus can't interact.
    socontra.unjoin_client_group(agent_name=message_initiator)
    socontra.unjoin_client_group(agent_name=message_receiver)

    # Agent message_receiver will now follow agent message_initiator. What this means is message_initiator can interact
    # (initiate) messages with message_receiver, but not vice versa, unless they have commenced a dialogue and can interact
    # for the duration of the dialogue.
    socontra.follow(agent_name=message_receiver, agent_to_follow=message_initiator)
    time.sleep(1)
    
    # message_initiator can message/interact with message_receiver.
    print('\nmessage_initiator is initiating a dialogue with message_receiver')
    message="Hi there!"
    socontra.new_message(agent_name=message_initiator, distribution_list=message_receiver, message=message, protocol='socontra')
    time.sleep(1)

    # However, message_receiver cannot interact with message_initiator because message_initiator does not follow message_receiver.
    # Trying to interact below will result in a protocol error being received by message_receiver from the Socontra Network.
    print('\nmessage_receiver is trying to initiate a dialogue with message_initiator - EXPECT A PROTOCOL ERROR')
    message="Why wont you talk to me?"
    socontra.new_message(agent_name=message_receiver, distribution_list=message_initiator, message=message, protocol='socontra')
    time.sleep(1)

    # We now have message_initiator follow message_receiver.
    socontra.follow(agent_name=message_initiator, agent_to_follow=message_receiver)
    time.sleep(1)

    # Now message_receiver can start an interaction with message_initiator.
    print('\nmessage_receiver initiates a dialogue with message_initiator')
    message="Glad we are now mutually connected and can both interact freely!"
    socontra.new_message(agent_name=message_receiver, distribution_list=message_initiator, message=message, protocol='socontra')
    time.sleep(1)
    
    # Agents can unfollow each other as well.
    socontra.unfollow(agent_name=message_receiver, agent_to_unfollow=message_initiator)
    socontra.unfollow(agent_name=message_initiator, agent_to_unfollow=message_receiver)
    