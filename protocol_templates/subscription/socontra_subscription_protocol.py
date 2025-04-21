# Socontra template for the agent general subscription (broadcast) protocol, a general purpose 1-way 2-to-many broadcasting tool for agents.

import time

from socontra.socontra import Socontra, Message, Protocol

# Create a Socontra Client for the agent.
protocol = Protocol()
socontra: Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ---- SOCONTRA GENERAL SUBSCRIPTION (BROADCAST) PROTOCOL ENDPOINT ----- #

@route('broadcast', 'subscription', 'socontra', 'recipient')  
# -> response: NoComms - N/A
def receive_new_broadcast(agent_name: str, received_message: Message):    
    # The Socontra Standard subscription/broadcast protocol.
    # Cannot respond to a broadcast.

    # New broadcasts can change the message_type ('socontra_broadcast'), protocol ('socontra') and recipient_type ('recipient')
    # to configure a unique broadcast endpoint for specific purposes, rather than rely on this general broadcast endpoint.
    print(f'\nNew broadcast from {received_message.sender_name} which is {received_message.message} for agent {agent_name}\n')


